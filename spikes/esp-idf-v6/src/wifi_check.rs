//! IoT Wi-Fi join check: association + DHCP only (no SNTP/MQTT/HTTPS).
//! Enabled by building with SPIKE_WIFI_ONLY=1. Env: SPIKE_WIFI_SSID, SPIKE_WIFI_PASS,
//! optional SPIKE_WIFI_AUTH=wpa2|wpa2wpa3 (default wpa2), SPIKE_WIFI_PMF=off (PMF capable=false). Secrets are never logged.
use esp_idf_hal::peripherals::Peripherals;
use esp_idf_svc::eventloop::EspSystemEventLoop;
use esp_idf_svc::nvs::EspDefaultNvsPartition;
use esp_idf_svc::sys;
use esp_idf_svc::wifi::{AuthMethod, BlockingWifi, ClientConfiguration, Configuration, EspWifi, WifiEvent};
use std::time::{Duration, Instant};

fn rssi() -> Option<i8> {
    unsafe {
        let mut ap: sys::wifi_ap_record_t = core::mem::zeroed();
        (sys::esp_wifi_sta_get_ap_info(&mut ap) == 0).then_some(ap.rssi)
    }
}

pub fn run() {
    if let Err(e) = run_inner() {
        log::error!("[W] failed: {e:?}");
    }
}

fn run_inner() -> anyhow::Result<()> {
    let t0 = Instant::now();
    let ssid = option_env!("SPIKE_WIFI_SSID").ok_or_else(|| anyhow::anyhow!("no ssid"))?;
    let pass = option_env!("SPIKE_WIFI_PASS").ok_or_else(|| anyhow::anyhow!("no pass"))?;
    let auth = match option_env!("SPIKE_WIFI_AUTH") {
        Some("wpa2wpa3") => AuthMethod::WPA2WPA3Personal,
        _ => AuthMethod::WPA2Personal,
    };
    let pmf = option_env!("SPIKE_WIFI_PMF") != Some("off");
    let pin_bssid: Option<[u8; 6]> = option_env!("SPIKE_WIFI_BSSID").map(|b| {
        let mut m = [0u8; 6];
        for (i, h) in b.split(':').enumerate().take(6) {
            m[i] = u8::from_str_radix(h, 16).unwrap_or(0);
        }
        m
    });
    let pin_channel: Option<u8> = option_env!("SPIKE_WIFI_CHANNEL").and_then(|c| c.parse().ok());
    log::info!("[W] pin bssid={pin_bssid:02x?} channel={pin_channel:?}");
    log::info!("[W] config auth={auth:?} pmf capable={pmf} required=false");
    let p = Peripherals::take()?;
    let sysloop = EspSystemEventLoop::take()?;
    let nvs = EspDefaultNvsPartition::take()?;
    let mut wifi = BlockingWifi::wrap(EspWifi::new(p.modem, sysloop.clone(), Some(nvs))?, sysloop.clone())?;
    wifi.set_configuration(&Configuration::Client(ClientConfiguration {
        ssid: ssid.try_into().map_err(|_| anyhow::anyhow!("ssid too long"))?,
        password: pass.try_into().map_err(|_| anyhow::anyhow!("pass too long"))?,
        auth_method: auth,
        bssid: pin_bssid,
        channel: pin_channel,
        ..Default::default()
    }))?;
    unsafe {
        let mut c: sys::wifi_config_t = core::mem::zeroed();
        sys::esp_wifi_get_config(sys::wifi_interface_t_WIFI_IF_STA, &mut c);
        c.sta.pmf_cfg.capable = pmf;
        c.sta.pmf_cfg.required = false;
        c.sta.scan_method = sys::wifi_scan_method_t_WIFI_ALL_CHANNEL_SCAN;
        let rc = sys::esp_wifi_set_config(sys::wifi_interface_t_WIFI_IF_STA, &mut c);
        log::info!("[W] set pmf capable/not-required, all-channel scan rc={rc}");
    }
    let _sub = sysloop.subscribe::<WifiEvent, _>(move |e| match e {
        WifiEvent::StaStarted => log::info!("[W] event StaStarted"),
        WifiEvent::StaConnected(c) => log::info!("[W] event StaConnected ch={}", c.channel()),
        WifiEvent::StaDisconnected(d) => log::warn!("[W] event StaDisconnected reason={}", d.reason()),
        other => log::info!("[W] event {other:?}"),
    })?;
    wifi.start()?;
    let mut matched = false;
    match wifi.scan() {
        Ok(aps) => {
            for a in aps.iter().filter(|a| a.ssid.as_str() == ssid) {
                matched = true;
                log::info!("[W] scan: SSID match=yes bssid={:02x?} auth={:?} ch={} rssi={}", a.bssid, a.auth_method, a.channel, a.signal_strength);
            }
            if !matched {
                log::warn!("[W] scan: SSID match=no ({} APs seen)", aps.len());
            }
        }
        Err(e) => log::warn!("[W] scan failed {e:?}"),
    }
    let t = Instant::now();
    wifi.connect()?;
    log::info!("[W] associated in {} ms", t.elapsed().as_millis());
    wifi.wait_netif_up()?;
    let ni = wifi.wifi().sta_netif().get_ip_info()?;
    log::info!(
        "[W] GOT IP ip={} gw={} mask={} rssi={:?} dns={:?} elapsed_since_start={} ms",
        ni.ip, ni.subnet.gateway, ni.subnet.mask, rssi(), ni.dns, t0.elapsed().as_millis()
    );
    for i in 0..6 {
        std::thread::sleep(Duration::from_secs(5));
        log::info!("[W] idle t={}s rssi={:?} connected={:?}", (i + 1) * 5, rssi(), wifi.is_connected());
    }
    log::info!("[W] done");
    Ok(())
}
