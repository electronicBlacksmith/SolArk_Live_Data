//! [T2] On-device self-signed ECDSA P-256 certificate via mbedTLS 4 + PSA.
use esp_idf_svc::sys::*;
use std::time::Instant;

const PSA_KEY_TYPE_ECC_KEY_PAIR_SECP_R1: u16 = 0x7100 | 0x12;
const PSA_KEY_USAGE_EXPORT: u32 = 0x0001;
const PSA_KEY_USAGE_SIGN_MESSAGE: u32 = 0x0400;
const PSA_KEY_USAGE_SIGN_HASH: u32 = 0x1000;
const PSA_ALG_ECDSA_SHA256: u32 = 0x0600_0600 | 0x09;

pub struct CertKey {
    pub cert_pem: Vec<u8>, // NUL-terminated
    pub key_pem: Vec<u8>,  // NUL-terminated
}

fn check(what: &str, rc: i32) -> anyhow::Result<()> {
    if rc != 0 {
        anyhow::bail!("{what} failed: {rc} (-0x{:x})", -rc);
    }
    Ok(())
}

pub fn generate() -> anyhow::Result<CertKey> {
    let t = Instant::now();
    unsafe {
        check("psa_crypto_init", psa_crypto_init())?;
        // PSA key attributes: fields are public in the bindgen struct, so we do not
        // need the static-inline psa_set_key_* helpers.
        let mut attrs: psa_key_attributes_t = core::mem::zeroed();
        attrs.type_ = PSA_KEY_TYPE_ECC_KEY_PAIR_SECP_R1;
        attrs.bits = 256;
        attrs.policy.usage = PSA_KEY_USAGE_SIGN_HASH | PSA_KEY_USAGE_SIGN_MESSAGE | PSA_KEY_USAGE_EXPORT;
        attrs.policy.alg = PSA_ALG_ECDSA_SHA256;
        let mut key_id: mbedtls_svc_key_id_t = 0;
        check("psa_generate_key", psa_generate_key(&attrs, &mut key_id))?;
        let t_key = t.elapsed();

        let mut pk: mbedtls_pk_context = core::mem::zeroed();
        mbedtls_pk_init(&mut pk);
        check("pk_copy_from_psa", mbedtls_pk_copy_from_psa(key_id, &mut pk))?;

        let mut crt: mbedtls_x509write_cert = core::mem::zeroed();
        mbedtls_x509write_crt_init(&mut crt);
        mbedtls_x509write_crt_set_version(&mut crt, 2); // v3 (the arg is MBEDTLS_X509_CRT_VERSION_3 = 2)
        mbedtls_x509write_crt_set_md_alg(&mut crt, mbedtls_md_type_t_MBEDTLS_MD_SHA256);
        mbedtls_x509write_crt_set_subject_key(&mut crt, &mut pk);
        mbedtls_x509write_crt_set_issuer_key(&mut crt, &mut pk);
        let name = c"CN=solark-spike,O=solark";
        check("subject", mbedtls_x509write_crt_set_subject_name(&mut crt, name.as_ptr()))?;
        check("issuer", mbedtls_x509write_crt_set_issuer_name(&mut crt, name.as_ptr()))?;
        let mut serial = [0u8; 8];
        esp_fill_random(serial.as_mut_ptr() as *mut _, serial.len());
        serial[0] &= 0x7f;
        serial[0] |= 0x01; // positive, non-zero
        check("serial", mbedtls_x509write_crt_set_serial_raw(&mut crt, serial.as_ptr(), serial.len()))?;
        // Spike only: fixed validity. Real firmware derives this from SNTP time and config.
        check(
            "validity",
            mbedtls_x509write_crt_set_validity(&mut crt, c"20260101000000".as_ptr(), c"20360101000000".as_ptr()),
        )?;
        check("basic_constraints", mbedtls_x509write_crt_set_basic_constraints(&mut crt, 0, -1))?;
        let mut cert_pem = vec![0u8; 2048];
        check("crt_pem", mbedtls_x509write_crt_pem(&mut crt, cert_pem.as_mut_ptr(), cert_pem.len()))?;
        let mut key_pem = vec![0u8; 1024];
        check("pk_write_key_pem", mbedtls_pk_write_key_pem(&pk, key_pem.as_mut_ptr(), key_pem.len()))?;
        for v in [&mut cert_pem, &mut key_pem] {
            let n = v.iter().position(|b| *b == 0).unwrap_or(v.len() - 1);
            v.truncate(n + 1);
        }
        mbedtls_x509write_crt_free(&mut crt);
        mbedtls_pk_free(&mut pk);
        psa_destroy_key(key_id);
        log::info!(
            "[T2] cert generated: keygen={} ms total={} ms cert_pem={}B key_pem={}B",
            t_key.as_millis(),
            t.elapsed().as_millis(),
            cert_pem.len(),
            key_pem.len()
        );
        Ok(CertKey { cert_pem, key_pem })
    }
}
