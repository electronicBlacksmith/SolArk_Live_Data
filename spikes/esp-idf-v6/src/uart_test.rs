//! [T4] Two RX-only UARTs (UART1 on GPIO1/D0, UART2 on GPIO2/D1) with the RX idle timeout.
//! Loopback with no wires: UART0 TX is on spare pad GPIO4; that pad's input is fed to the
//! UART1/UART2 RXD inputs through the GPIO matrix (esp_rom_gpio_connect_in_signal).
use esp_idf_hal::delay::BLOCK;
use esp_idf_hal::gpio::AnyIOPin;
use esp_idf_hal::peripherals::Peripherals;
use esp_idf_hal::uart::{config::Config, UartDriver, UartEventPayload, UartRxDriver};
use esp_idf_hal::units::Hertz;
use esp_idf_svc::sys;
use std::sync::{Arc, Mutex};
use std::time::Duration;

const BAUD: u32 = 9600;
const U1RXD_IN_IDX: u32 = 15; // gpio_sig_map.h (esp32s3)
const U2RXD_IN_IDX: u32 = 18;
const TXPAD: i32 = 4; // spare, unconnected (D3)

fn char_us() -> f64 {
    10.0 * 1_000_000.0 / BAUD as f64
}

#[derive(Clone, Debug)]
struct Rec {
    t_us: i64,
    len: usize,
    first: u8,
}
type Log = Arc<Mutex<Vec<Rec>>>;

struct SendRx(UartRxDriver<'static>);
// SAFETY: IDF UART driver calls are thread-safe; the wrapper only holds a port number + queue handle.
unsafe impl Send for SendRx {}

fn spawn_rx(drv: UartRxDriver<'static>, log: Log, name: &'static str) {
    let d = SendRx(drv);
    std::thread::Builder::new()
        .name(name.into())
        .stack_size(6144)
        .spawn(move || {
            let d = d;
            let drv = &d.0;
            let q = drv.event_queue().expect("queue");
            let mut acc: Vec<u8> = Vec::new();
            let mut buf = [0u8; 512];
            loop {
                let Some((ev, _)) = q.recv_front(BLOCK) else { continue };
                let t = unsafe { sys::esp_timer_get_time() };
                match ev.payload() {
                    UartEventPayload::Data { timeout, .. } => {
                        loop {
                            let n = drv.read(&mut buf, 0).unwrap_or(0);
                            if n == 0 {
                                break;
                            }
                            acc.extend_from_slice(&buf[..n]);
                        }
                        if timeout && !acc.is_empty() {
                            log.lock().unwrap().push(Rec { t_us: t, len: acc.len(), first: acc[0] });
                            acc.clear();
                        }
                    }
                    other => log::warn!("[T4] {name} event {:?}", other),
                }
            }
        })
        .unwrap();
}

fn reg_base(port: u32) -> usize {
    match port {
        0 => 0x6000_0000,
        1 => 0x6001_0000,
        _ => 0x6002_E000,
    }
}
unsafe fn rd(a: usize) -> u32 {
    core::ptr::read_volatile(a as *const u32)
}
unsafe fn wr(a: usize, v: u32) {
    core::ptr::write_volatile(a as *mut u32, v)
}
const MEM_CONF: usize = 0x60; // UART_MEM_CONF_REG, RX_TOUT_THRHD = bits[26:17]
const RX_FILT: usize = 0x18; // UART_RX_FILT_REG, GLITCH_FILT [7:0], GLITCH_FILT_EN bit 8
fn tout_reg(port: u32) -> u32 {
    unsafe { (rd(reg_base(port) + MEM_CONF) >> 17) & 0x3ff }
}
fn set_tout_raw(port: u32, v: u32) {
    unsafe {
        let a = reg_base(port) + MEM_CONF;
        wr(a, (rd(a) & !(0x3ff << 17)) | ((v & 0x3ff) << 17));
    }
}

fn busy_us(us: u32) {
    unsafe { sys::esp_rom_delay_us(us) }
}

/// Send frames; each item = (bytes, gap_after_us). Returns the esp_timer time TX finished.
fn send_script(tx: &mut UartDriver<'static>, script: &[(Vec<u8>, u32)]) -> i64 {
    for (bytes, gap) in script {
        tx.write(bytes).unwrap();
        tx.wait_tx_done(BLOCK).unwrap();
        busy_us(*gap);
    }
    unsafe { sys::esp_timer_get_time() }
}

fn frame(id: u8, len: usize) -> Vec<u8> {
    let mut v = vec![0x01, 0x03, id];
    v.extend((0..len.saturating_sub(3)).map(|i| (i as u8).wrapping_add(id)));
    v
}


fn route(to1: bool, to2: bool) {
    unsafe {
        // inv=false; a signal index of 0x38 means constant-high ("no pin") -> idle line
        sys::esp_rom_gpio_connect_in_signal(if to1 { TXPAD as u32 } else { 0x38 }, U1RXD_IN_IDX, false);
        sys::esp_rom_gpio_connect_in_signal(if to2 { TXPAD as u32 } else { 0x38 }, U2RXD_IN_IDX, false);
    }
}

fn splits(log: &Log) -> usize {
    log.lock().unwrap().len()
}

pub fn run() {
    let p = Peripherals::take().unwrap();
    *crate::net::PERIPH.lock().unwrap() = Some((p.modem,));
    let cfg = |tout: u8| {
        let mut c = Config::new().baudrate(Hertz(BAUD)).queue_size(64).rx_fifo_size(1024);
        c.event_config.receive_timeout = Some(tout);
        c
    };
    let (log1, log2): (Log, Log) = (Arc::default(), Arc::default());
    // RX-only: no TX pin passed.
    let rx1 = UartRxDriver::new(p.uart1, p.pins.gpio1, None::<AnyIOPin>, None::<AnyIOPin>, &cfg(4)).unwrap();
    let rx2 = UartRxDriver::new(p.uart2, p.pins.gpio2, None::<AnyIOPin>, None::<AnyIOPin>, &cfg(4)).unwrap();
    log::info!("[T4] rx drivers up (UART1 RX=GPIO1, UART2 RX=GPIO2, no TX pins)");
    unsafe {
        for pin in [1, 2] {
            sys::gpio_set_pull_mode(pin, sys::gpio_pull_mode_t_GPIO_FLOATING);
        }
    }
    // Transmitter: UART0, TX on spare GPIO4 only.
    let mut tx = match UartDriver::new(
        p.uart0,
        p.pins.gpio4,
        p.pins.gpio5,
        None::<AnyIOPin>,
        None::<AnyIOPin>,
        &Config::new().baudrate(Hertz(BAUD)).rx_fifo_size(1024).tx_fifo_size(1024),
    ) {
        Ok(t) => t,
        Err(e) => {
            log::error!("[T4] UART0 TX driver failed: {e:?}");
            return;
        }
    };
    unsafe {
        sys::gpio_input_enable(TXPAD);
        sys::gpio_set_pull_mode(TXPAD, sys::gpio_pull_mode_t_GPIO_FLOATING);
    }
    route(true, true);
    spawn_rx(rx1, log1.clone(), "rx1");
    spawn_rx(rx2, log2.clone(), "rx2");
    std::thread::sleep(Duration::from_millis(100));

    let mut min_d = i64::MAX;
    for _ in 0..1000 {
        let a = unsafe { sys::esp_timer_get_time() };
        let b = unsafe { sys::esp_timer_get_time() };
        if b > a {
            min_d = min_d.min(b - a);
        }
    }
    log::info!("[T4] esp_timer: smallest observed step = {min_d} us");
    log::info!("[T4] char time at {BAUD} 8N1 = {:.1} us; 3.5 char = {:.0} us", char_us(), 3.5 * char_us());
    log::info!("[T4] rx_timeout reg after driver create with API value 4: UART1={} UART2={}", tout_reg(1), tout_reg(2));

    // sanity: a single byte arrives on both
    log1.lock().unwrap().clear();
    log2.lock().unwrap().clear();
    send_script(&mut tx, &[(vec![0x55], 0)]);
    std::thread::sleep(Duration::from_millis(200));
    log::info!("[T4] loopback sanity: UART1 frames={} UART2 frames={}", splits(&log1), splits(&log2));

    // ---- TOUT unit: API value -> register readback, idle-detect delay after TX done
    for api in [1i32, 2, 4, 8, 12] {
        unsafe {
            sys::uart_set_rx_timeout(1, api as u8);
        }
        let mut delays = vec![];
        for _ in 0..5 {
            log1.lock().unwrap().clear();
            let t_end = send_script(&mut tx, &[(vec![0x55], 0)]);
            std::thread::sleep(Duration::from_millis(150));
            if let Some(r) = log1.lock().unwrap().first() {
                delays.push(r.t_us - t_end);
            }
        }
        log::info!(
            "[T4] uart_set_rx_timeout(1,{api}) -> reg={} ; idle-detect delay after TX-done us={:?} (1 bit={:.0} us, 1 char={:.0} us)",
            tout_reg(1),
            delays,
            char_us() / 10.0,
            char_us()
        );
    }
    for raw in [10u32, 35, 100] {
        set_tout_raw(1, raw);
        let mut delays = vec![];
        for _ in 0..3 {
            log1.lock().unwrap().clear();
            let t_end = send_script(&mut tx, &[(vec![0x55], 0)]);
            std::thread::sleep(Duration::from_millis(200));
            if let Some(r) = log1.lock().unwrap().first() {
                delays.push(r.t_us - t_end);
            }
        }
        log::info!(
            "[T4] raw reg {raw} -> readback={} ; delay us={:?} (if bit units: {:.0} us; if char units: {:.0} us)",
            tout_reg(1),
            delays,
            raw as f64 * char_us() / 10.0,
            raw as f64 * char_us()
        );
    }

    // ---- Threshold sweep: split/merge matrix. rows = API threshold (symbols), cols = gap (us) between two 10-byte frames
    let gaps = [500u32, 1000, 1500, 2000, 3000, 3600, 4500, 6000, 10000];
    log::info!("[T4] SWEEP gaps(us)={gaps:?}; char={:.0}us. cell = UART1 frames/UART2 frames (2=split,1=merged)", char_us());
    for api in [1u8, 2, 3, 4, 6, 10] {
        unsafe {
            sys::uart_set_rx_timeout(1, api);
            sys::uart_set_rx_timeout(2, api);
        }
        let mut row = vec![];
        for gap in gaps {
            log1.lock().unwrap().clear();
            log2.lock().unwrap().clear();
            // two writes queued; the gap is created by wait_done + busy wait
            send_script(&mut tx, &[(frame(1, 10), gap), (frame(2, 10), 0)]);
            std::thread::sleep(Duration::from_millis(120));
            row.push(format!("{}/{}", splits(&log1), splits(&log2)));
        }
        log::info!("[T4] SWEEP api_thresh={api} (regs {}/{}): {row:?}", tout_reg(1), tout_reg(2));
    }

    // ---- Framing test, threshold = 3.5 char on both
    unsafe {
        sys::uart_set_rx_timeout(1, 4);
        sys::uart_set_rx_timeout(2, 4);
    }
    log::info!("[T4] FRAMING with API thresh 4 symbols (regs {}/{}), both UARTs simultaneously", tout_reg(1), tout_reg(2));
    let f = |i: u8, n: usize| frame(i, n);
    // F1(8) gap F2(205) gap [F3(20)+F4(37)+F5(9) single write = zero gap] gap F6(64) ; F7(12) wait_done+<1.5ch gap
    let script: Vec<(Vec<u8>, u32)> = vec![
        (f(1, 8), 8000),
        (f(2, 205), 8000),
        ([f(3, 20), f(4, 37), f(5, 9)].concat(), 8000),
        (f(6, 64), 400),
        (f(7, 12), 0),
    ];
    log::info!("[T4] expect 4 frames/UART: lens 8,205,66,76");
    log1.lock().unwrap().clear();
    log2.lock().unwrap().clear();
    let t0 = unsafe { sys::esp_timer_get_time() };
    send_script(&mut tx, &script);
    std::thread::sleep(Duration::from_millis(300));
    for (n, l) in [(1, &log1), (2, &log2)] {
        let v = l.lock().unwrap().clone();
        log::info!("[T4]    UART{n}: {} frames (len,t_us_rel) {:?}", v.len(), v.iter().map(|r| (r.len, r.t_us - t0)).collect::<Vec<_>>());
    }
    let (v1, v2) = (log1.lock().unwrap().clone(), log2.lock().unwrap().clone());
    let d: Vec<i64> = v1.iter().zip(v2.iter()).map(|(a, b)| a.t_us - b.t_us).collect();
    log::info!("[T4]    per-frame timestamp diff UART1-UART2 (us) = {d:?}");

    // jitter: 30 x 10-byte frames separated by 10 ms; timestamp minus TX-done
    unsafe {
        sys::uart_set_rx_timeout(1, 4);
        sys::uart_set_rx_timeout(2, 4);
    }
    let mut lat1 = vec![];
    for _ in 0..30 {
        log1.lock().unwrap().clear();
        let t_end = send_script(&mut tx, &[(frame(9, 10), 0)]);
        std::thread::sleep(Duration::from_millis(30));
        if let Some(r) = log1.lock().unwrap().first() {
            lat1.push(r.t_us - t_end);
        }
    }
    if !lat1.is_empty() {
        let mn = *lat1.iter().min().unwrap();
        let mx = *lat1.iter().max().unwrap();
        let mean = lat1.iter().sum::<i64>() as f64 / lat1.len() as f64;
        log::info!("[T4] JITTER idle-detect latency after TX-done: n={} min={mn} max={mx} mean={mean:.0} us (spread {} us)", lat1.len(), mx - mn);
    }

    // ---- 3.5ch gap + glitch filter / autobaud reachability
    unsafe {
        let a = reg_base(2) + RX_FILT;
        let before = rd(a);
        wr(a, (1 << 8) | 4);
        log::info!("[T4] RX_FILT UART2 before=0x{before:x} after write=0x{:x} (raw register reachable)", rd(a));
        wr(a, before);
        let cfg = sys::uart_bitrate_detect_config_t { rx_io_num: 2, source_clk: sys::soc_module_clk_t_SOC_MOD_CLK_APB as _ };
        let rc = sys::uart_detect_bitrate_start(2, &cfg);
        log::info!("[T4] uart_detect_bitrate_start(2) with all 3 UARTs in use -> {rc}");
        if rc == 0 {
            let mut res: sys::uart_bitrate_res_t = core::mem::zeroed();
            let r2 = sys::uart_detect_bitrate_stop(2, false, &mut res);
            log::info!("[T4] detect_bitrate_stop -> {r2}");
        }
    }
    std::mem::forget(tx);
    crate::heap_report("after-uart");
}
