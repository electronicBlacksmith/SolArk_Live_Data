//! ESP-IDF v6.0.3 feasibility spike. Throwaway code; the plan borrows from it.
//! Stages: [T0] info, [T3] PBKDF2, [T4] UART RX/TOUT, [T1]/[T2] Wi-Fi + MQTT TLS + HTTPS.
mod certgen;
mod net;
mod pbkdf2;
mod uart_test;
mod wifi_check;

use esp_idf_svc::sys;
use std::ffi::CStr;

pub fn heap_report(tag: &str) {
    unsafe {
        log::info!(
            "[heap:{tag}] internal free={} min_ever={} largest={} | psram free={} min_ever={}",
            sys::heap_caps_get_free_size(sys::MALLOC_CAP_INTERNAL),
            sys::heap_caps_get_minimum_free_size(sys::MALLOC_CAP_INTERNAL),
            sys::heap_caps_get_largest_free_block(sys::MALLOC_CAP_INTERNAL),
            sys::heap_caps_get_free_size(sys::MALLOC_CAP_SPIRAM),
            sys::heap_caps_get_minimum_free_size(sys::MALLOC_CAP_SPIRAM),
        );
    }
}

fn main() {
    sys::link_patches();
    esp_idf_svc::log::EspLogger::initialize_default();
    let ver = unsafe { CStr::from_ptr(sys::esp_get_idf_version()) };
    log::info!("[T0] IDF version: {}", ver.to_string_lossy());
    log::info!("[T0] mbedtls version: {}", unsafe {
        CStr::from_ptr(sys::MBEDTLS_VERSION_STRING.as_ptr() as *const _).to_string_lossy()
    });
    let psram = unsafe { sys::heap_caps_get_total_size(sys::MALLOC_CAP_SPIRAM) };
    log::info!("[T0] PSRAM heap total={psram} bytes (ECC status is in the boot log: octal_psram)");
    heap_report("boot");

    if option_env!("SPIKE_WIFI_ONLY").is_some() {
        wifi_check::run(); // Wi-Fi-only join check; skips PBKDF2/UART/MQTT/HTTPS
        return;
    }
    pbkdf2::run();
    uart_test::run();
    net::run(); // never returns when creds are present
    log::info!("[done] no network stage (no creds in build)");
}
