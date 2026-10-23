use aeris_skill_transfer::*;
use ed25519_dalek::{Signer, SigningKey};
use std::path::PathBuf;
pub fn key() -> SigningKey {
    SigningKey::from_bytes(&[42; 32])
}
pub fn sign(manifest: &Manifest, behavior_json: String) -> Bundle {
    let manifest_json = serde_json::to_string(manifest).unwrap();
    let signature = key().sign(&[DOMAIN, manifest_json.as_bytes()].concat());
    Bundle {
        schema: "evy-aeris.transfer-bundle.v2".into(),
        signature_hex: signature
            .to_bytes()
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect(),
        manifest_json,
        behavior_json,
    }
}
pub fn fixtures() -> (Config, Bundle, Bundle) {
    let target = Target {
        profile: "mujoco-six-axis-goals-v1".into(),
        plant_sha256: "1".repeat(64),
        calibration_sha256: "2".repeat(64),
        joint_names: std::array::from_fn(|i| format!("j{i}")),
        units: "rad".into(),
        frame: "world-base".into(),
        runtime: "mujoco-rust-mpc-v1".into(),
        runtime_version: "3.3.7".into(),
        host_arch: std::env::consts::ARCH.into(),
        host_os: std::env::consts::OS.into(),
        adapter_sha256: "3".repeat(64),
    };
    let behavior = serde_json::to_string(&Behavior {
        schema: "aeris.bounded-joint-goals.v1".into(),
        goals: vec![aeris_control_v2::HOME],
    })
    .unwrap();
    let mut m = Manifest {
        schema: "evy-aeris.transfer-release.v2".into(),
        release_id: "first".into(),
        skill_id: "inspection".into(),
        sequence: 1,
        issued_at_ms: 0,
        not_before_ms: 0,
        expires_at_ms: 10000,
        origin: "existing_deterministic_behavior".into(),
        target: target.clone(),
        behavior_sha256: sha(behavior.as_bytes()),
        behavior_size: behavior.len(),
        recovery_of: None,
    };
    let first = sign(&m, behavior.clone());
    m.sequence = 2;
    m.release_id = "second".into();
    let second = sign(&m, behavior);
    let public = key()
        .verifying_key()
        .to_bytes()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    let cfg = Config {
        schema: "evy-aeris.edge-config.v2".into(),
        publisher_url: "https://localhost:1/release".into(),
        ca_der_path: PathBuf::from("/tmp/test-ca"),
        bearer_file: PathBuf::from("/tmp/test-token"),
        publisher_public_hex: public,
        approved_manifests: vec![
            sha(first.manifest_json.as_bytes()),
            sha(second.manifest_json.as_bytes()),
        ],
        target,
        python: PathBuf::from("/tmp/test-python"),
        python_sha256: "4".repeat(64),
        adapter: PathBuf::from("/tmp/test-adapter"),
    };
    (cfg, first, second)
}
