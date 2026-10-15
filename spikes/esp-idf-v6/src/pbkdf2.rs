//! [T3] PBKDF2-HMAC-SHA256 via PSA key derivation (mbedTLS 4 / TF-PSA-Crypto).
use esp_idf_svc::sys::*;
use std::time::Instant;

// PSA constants that bindgen cannot see (casts inside macros). Values from
// tf-psa-crypto/include/psa/crypto_values.h in ESP-IDF v6.0.3.
const PSA_ALG_SHA_256: u32 = 0x0200_0009;
const PSA_ALG_PBKDF2_HMAC_BASE: u32 = 0x0880_0100;
const PSA_KEY_DERIVATION_INPUT_PASSWORD: u16 = 0x0102;
const PSA_KEY_DERIVATION_INPUT_SALT: u16 = 0x0202;
const PSA_KEY_DERIVATION_INPUT_COST: u16 = 0x0205;

pub fn pbkdf2_sha256(pw: &[u8], salt: &[u8], iters: u64, out: &mut [u8]) -> Result<(), i32> {
    unsafe {
        let mut op: psa_key_derivation_operation_t = core::mem::zeroed();
        let alg = PSA_ALG_PBKDF2_HMAC_BASE | (PSA_ALG_SHA_256 & 0x0000_00ff);
        let chk = |s: psa_status_t, op: &mut psa_key_derivation_operation_t| {
            if s != 0 {
                psa_key_derivation_abort(op);
                Err(s)
            } else {
                Ok(())
            }
        };
        chk(psa_key_derivation_setup(&mut op, alg), &mut op)?;
        chk(psa_key_derivation_input_integer(&mut op, PSA_KEY_DERIVATION_INPUT_COST, iters), &mut op)?;
        chk(psa_key_derivation_input_bytes(&mut op, PSA_KEY_DERIVATION_INPUT_SALT, salt.as_ptr(), salt.len()), &mut op)?;
        chk(psa_key_derivation_input_bytes(&mut op, PSA_KEY_DERIVATION_INPUT_PASSWORD, pw.as_ptr(), pw.len()), &mut op)?;
        chk(psa_key_derivation_output_bytes(&mut op, out.as_mut_ptr(), out.len()), &mut op)?;
        psa_key_derivation_abort(&mut op);
    }
    Ok(())
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

pub fn run() {
    let st = unsafe { psa_crypto_init() };
    log::info!("[T3] psa_crypto_init -> {st}");
    // Expected values computed on the Mac: Python hashlib.pbkdf2_hmac('sha256', ...)
    let cases: [(u64, &str); 2] = [
        (10_000, "99140ec140b4db63a2499abe849064771328ac65efdbc94a76215f4a27cebf0f"),
        (50_000, "025bdcdbbb22b8fd8514fc52eb5a1c271b2f5056b63dbe36d535eb211c94b605"),
    ];
    for (iters, expect) in cases {
        let mut out = [0u8; 32];
        let t = Instant::now();
        let r = pbkdf2_sha256(b"correct horse battery", b"solark-salt-0001", iters, &mut out);
        let dt = t.elapsed();
        match r {
            Ok(()) => log::info!(
                "[T3] pbkdf2 iters={iters} time={} ms match={}",
                dt.as_millis(),
                hex(&out) == expect
            ),
            Err(s) => log::error!("[T3] pbkdf2 iters={iters} FAILED psa_status={s}"),
        }
    }
}
