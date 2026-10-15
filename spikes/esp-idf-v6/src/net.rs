//! [T1] Wi-Fi + SNTP + MQTT over TLS and [T2] HTTPS server with an on-device cert.
//! Credentials come from compile-time env vars (never logged, never in the repo):
//!   SPIKE_WIFI_SSID, SPIKE_WIFI_PASS, SPIKE_BROKER_URL (mqtts://IP:8883),
//!   SPIKE_MQTT_USER, SPIKE_MQTT_PASS (throwaway), SPIKE_CA_PEM (path to the throwaway CA).
use crate::certgen;
use esp_idf_hal::modem::Modem;
use esp_idf_svc::eventloop::EspSystemEventLoop;
use esp_idf_svc::http::server::{Configuration as HttpCfg, EspHttpServer};
use esp_idf_svc::http::Method;
use esp_idf_svc::mqtt::client::{EspMqttClient, EventPayload, MqttClientConfiguration, QoS};
use esp_idf_svc::nvs::EspDefaultNvsPartition;
use esp_idf_svc::sntp::{EspSntp, SyncStatus};
use esp_idf_svc::tls::X509;
use esp_idf_svc::wifi::{BlockingWifi, ClientConfiguration, Configuration, EspWifi};
use esp_idf_svc::io::Write;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub static PERIPH: Mutex<Option<(Modem,)>> = Mutex::new(None);

static CA_PEM: &str = include_str!(env!("SPIKE_CA_PEM"));

pub fn run() {
    let (Some(ssid), Some(pass), Some(url)) = (
        option_env!("SPIKE_WIFI_SSID"),
        option_env!("SPIKE_WIFI_PASS"),
        option_env!("SPIKE_BROKER_URL"),
    ) else {
        log::warn!("[T1] blocked: no creds in this build");
        return;
    };
    if let Err(e) = run_inner(ssid, pass, url) {
        log::error!("[T1/T2] failed: {e:?}");
    }
}

fn run_inner(ssid: &str, pass: &str, url: &str) -> anyhow::Result<()> {
    let (modem,) = PERIPH.lock().unwrap().take().expect("modem");
    let sysloop = EspSystemEventLoop::take()?;
    let sysloop2 = sysloop.clone();
    let nvs = EspDefaultNvsPartition::take()?;
    let mut wifi = BlockingWifi::wrap(EspWifi::new(modem, sysloop.clone(), Some(nvs))?, sysloop)?;
    wifi.set_configuration(&Configuration::Client(ClientConfiguration {
        ssid: ssid.try_into().map_err(|_| anyhow::anyhow!("ssid too long"))?,
        password: pass.try_into().map_err(|_| anyhow::anyhow!("pass too long"))?,
        auth_method: esp_idf_svc::wifi::AuthMethod::WPA2Personal, // a threshold: WPA2 minimum, WPA3 accepted (WPA2WPA3 rejects WPA2-only APs, reason 211)
        ..Default::default()
    }))?;
    unsafe {
        // esp-idf-svc leaves sae_pwe_h2e at 0 (hunt-and-peck only); allow H2E as well.
        let mut c: esp_idf_svc::sys::wifi_config_t = core::mem::zeroed();
        esp_idf_svc::sys::esp_wifi_get_config(esp_idf_svc::sys::wifi_interface_t_WIFI_IF_STA, &mut c);
        c.sta.sae_pwe_h2e = esp_idf_svc::sys::wifi_sae_pwe_method_t_WPA3_SAE_PWE_BOTH as _;
        c.sta.sae_pk_mode = 0;
        c.sta.pmf_cfg.capable = true;
        c.sta.pmf_cfg.required = false;
        c.sta.scan_method = esp_idf_svc::sys::wifi_scan_method_t_WIFI_ALL_CHANNEL_SCAN;
        let rc = esp_idf_svc::sys::esp_wifi_set_config(esp_idf_svc::sys::wifi_interface_t_WIFI_IF_STA, &mut c);
        log::info!("[T1] set sae_pwe_h2e=BOTH rc={rc} (reg={})", c.sta.sae_pwe_h2e);
    }
    wifi.start()?;
    // Max TX power (~20 dBm) makes this XIAO miss the AP's auth response (AUTH_EXPIRE); 19 dBm and below join.
    // Units are 0.25 dBm. Default 68 = 17 dBm; override with SPIKE_WIFI_TXPOWER_QDBM.
    let qdbm: i8 = option_env!("SPIKE_WIFI_TXPOWER_QDBM").and_then(|v| v.parse().ok()).unwrap_or(68);
    let rc = unsafe { esp_idf_svc::sys::esp_wifi_set_max_tx_power(qdbm) };
    let mut got: i8 = 0;
    unsafe { esp_idf_svc::sys::esp_wifi_get_max_tx_power(&mut got) };
    log::info!("[T1] tx power set rc={rc} requested={qdbm} actual={got} (x0.25 dBm)");
    let _sub = sysloop2.subscribe::<esp_idf_svc::wifi::WifiEvent, _>(|e| {
        if let esp_idf_svc::wifi::WifiEvent::StaDisconnected(d) = e {
            log::warn!("[T1] sta disconnected reason={}", d.reason());
        }
    })?;
    match wifi.scan() {
        Ok(aps) => {
            for a in aps.iter().filter(|a| a.ssid.as_str() == ssid) {
                log::info!("[T1] scan: matching AP ch={} rssi={} auth={:?}", a.channel, a.signal_strength, a.auth_method);
            }
            log::info!("[T1] scan: {} APs total", aps.len());
        }
        Err(e) => log::warn!("[T1] scan failed {e:?}"),
    }
    let t = std::time::Instant::now();
    wifi.connect()?;
    wifi.wait_netif_up()?;
    let ip = wifi.wifi().sta_netif().get_ip_info()?;
    log::info!("[T1] wifi up in {} ms, ip={}", t.elapsed().as_millis(), ip.ip);
    crate::heap_report("wifi-up");

    // --- SNTP before TLS
    let sntp = EspSntp::new_default()?;
    let t = std::time::Instant::now();
    while sntp.get_sync_status() != SyncStatus::Completed {
        if t.elapsed() > Duration::from_secs(30) {
            anyhow::bail!("SNTP timeout");
        }
        std::thread::sleep(Duration::from_millis(200));
    }
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    log::info!("[T1] SNTP synced in {} ms, unix={now}", t.elapsed().as_millis());

    // --- MQTT over TLS
    let mut ca = CA_PEM.as_bytes().to_vec();
    ca.push(0);
    let ca: &'static [u8] = Box::leak(ca.into_boxed_slice());
    let connected = Arc::new(AtomicBool::new(false));
    let rx_count = Arc::new(AtomicU32::new(0));
    let (c2, r2) = (connected.clone(), rx_count.clone());
    let mqtt_conf = MqttClientConfiguration {
        client_id: Some("solark-spike"),
        username: option_env!("SPIKE_MQTT_USER"),
        password: option_env!("SPIKE_MQTT_PASS"),
        server_certificate: Some(X509::pem_until_nul(ca)),
        buffer_size: 2048,
        out_buffer_size: 2048,
        ..Default::default()
    };
    let t = std::time::Instant::now();
    let mut client = EspMqttClient::new_cb(url, &mqtt_conf, move |ev| match ev.payload() {
        EventPayload::Connected(_) => {
            log::info!("[T1] mqtt connected");
            c2.store(true, Ordering::SeqCst)
        }
        EventPayload::Disconnected => {
            log::warn!("[T1] mqtt disconnected");
            c2.store(false, Ordering::SeqCst)
        }
        EventPayload::Received { topic, data, .. } => {
            log::info!("[T1] mqtt rx topic={:?} len={}", topic, data.len());
            r2.fetch_add(1, Ordering::SeqCst);
        }
        EventPayload::Error(e) => log::error!("[T1] mqtt error {e:?}"),
        _ => {}
    })?;
    while !connected.load(Ordering::SeqCst) {
        if t.elapsed() > Duration::from_secs(600) {
            anyhow::bail!("MQTT connect timeout");
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    log::info!("[T1] mqtt TLS connect took {} ms", t.elapsed().as_millis());
    client.subscribe("solark/spike/cmd", QoS::AtLeastOnce)?;
    client.publish("solark/spike/hello", QoS::AtLeastOnce, false, b"hello from xiao")?;
    crate::heap_report("mqtt-up");

    // --- HTTPS server with on-device cert
    let ck = certgen::generate()?;
    let cert: &'static [u8] = Box::leak(ck.cert_pem.into_boxed_slice());
    let key: &'static [u8] = Box::leak(ck.key_pem.into_boxed_slice());
    let mut server = EspHttpServer::new(&HttpCfg {
        https_port: 443,
        stack_size: 10240,
        max_open_sockets: 3,
        lru_purge_enable: true,
        server_certificate: Some(X509::pem_until_nul(cert)),
        private_key: Some(X509::pem_until_nul(key)),
        ..Default::default()
    })?;
    server.fn_handler::<anyhow::Error, _>("/", Method::Get, |req| {
        log::info!("[T2] served GET /");
        crate::heap_report("during-https");
        req.into_ok_response()?.write_all(b"<h1>solark spike over HTTPS</h1>")?;
        Ok(())
    })?;
    crate::heap_report("https-up");
    log::info!("[T2] https listening on {}:443", ip.ip);

    // --- idle loop: heartbeat over MQTT so the Mac side can verify; stays up ~10 min
    for i in 0..120u32 {
        std::thread::sleep(Duration::from_secs(5));
        let payload = format!("hb {i} rx={}", rx_count.load(Ordering::SeqCst));
        let _ = client.publish("solark/spike/hb", QoS::AtLeastOnce, false, payload.as_bytes());
        if i % 6 == 0 {
            crate::heap_report("steady");
        }
    }
    drop(server);
    Ok(())
}
