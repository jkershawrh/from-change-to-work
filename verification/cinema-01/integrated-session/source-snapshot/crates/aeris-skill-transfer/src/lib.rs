//! Signed simulator capability transfer and crash-consistent activation.
//! Local configuration is trusted. No physical driver or training authority exists.
use ed25519_dalek::{Signature, VerifyingKey};
use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    fs::{File, OpenOptions},
    io::Read,
    os::{fd::AsRawFd, unix::fs::OpenOptionsExt},
    path::{Path, PathBuf},
    time::{Duration, SystemTime, UNIX_EPOCH},
};

pub mod action;
pub mod executor;
pub use action::ActionRequest;
pub const DOMAIN: &[u8] = b"evy-aeris.transfer-release.v2\0";
pub const MAX_BUNDLE: usize = 65536;
pub type Result<T> = std::result::Result<T, Error>;
#[derive(Debug)]
pub struct Error(pub String);
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}
impl std::error::Error for Error {}
macro_rules! from_error {
    ($t:ty) => {
        impl From<$t> for Error {
            fn from(e: $t) -> Self {
                Self(e.to_string())
            }
        }
    };
}
from_error!(std::io::Error);
from_error!(serde_json::Error);
from_error!(rusqlite::Error);
pub fn require(ok: bool, reason: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(Error(reason.into()))
    }
}
pub fn sha(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
pub fn now_ms() -> Result<u64> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| Error("CLOCK".into()))?
        .as_millis()
        .try_into()
        .map_err(|_| Error("CLOCK".into()))
}
fn identifier(s: &str) -> bool {
    !s.is_empty()
        && s.len() <= 96
        && s.bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_.".contains(&b))
}
fn digest(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn decode<const N: usize>(s: &str) -> Result<[u8; N]> {
    require(
        s.len() == N * 2
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
        "HEX",
    )?;
    let mut out = [0; N];
    for (i, b) in out.iter_mut().enumerate() {
        *b = u8::from_str_radix(&s[2 * i..2 * i + 2], 16).map_err(|_| Error("HEX".into()))?;
    }
    Ok(out)
}
pub fn read_bounded(path: &Path, max: usize) -> Result<Vec<u8>> {
    let f = File::open(path)?;
    require(f.metadata()?.is_file(), "NOT_REGULAR")?;
    let mut bytes = Vec::new();
    f.take((max + 1) as u64).read_to_end(&mut bytes)?;
    require(bytes.len() <= max, "SIZE")?;
    Ok(bytes)
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Target {
    pub profile: String,
    pub plant_sha256: String,
    pub calibration_sha256: String,
    pub joint_names: [String; 6],
    pub units: String,
    pub frame: String,
    pub runtime: String,
    pub runtime_version: String,
    pub host_arch: String,
    pub host_os: String,
    pub adapter_sha256: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub schema: String,
    pub publisher_url: String,
    pub ca_der_path: PathBuf,
    pub bearer_file: PathBuf,
    pub publisher_public_hex: String,
    pub approved_manifests: Vec<String>,
    pub target: Target,
    pub python: PathBuf,
    pub python_sha256: String,
    pub adapter: PathBuf,
}
impl Config {
    pub fn load(path: &Path) -> Result<Self> {
        let c: Self = serde_json::from_slice(&read_bounded(path, 32768)?)?;
        c.validate()?;
        Ok(c)
    }
    fn validate(&self) -> Result<()> {
        require(self.schema == "evy-aeris.edge-config.v2", "CONFIG_SCHEMA")?;
        let url = reqwest::Url::parse(&self.publisher_url).map_err(|_| Error("URL".into()))?;
        require(
            url.scheme() == "https"
                && url.username().is_empty()
                && url.password().is_none()
                && url.query().is_none()
                && url.fragment().is_none(),
            "HTTPS_REQUIRED",
        )?;
        decode::<32>(&self.publisher_public_hex)?;
        require(
            !self.approved_manifests.is_empty()
                && self.approved_manifests.len() <= 128
                && self.approved_manifests.iter().all(|s| digest(s)),
            "APPROVAL_CONFIG",
        )?;
        require(
            self.target.profile == "mujoco-six-axis-goals-v1"
                && self.target.units == "rad"
                && self.target.frame == "world-base"
                && self.target.runtime == "mujoco-rust-mpc-v1",
            "PROFILE",
        )?;
        require(
            self.target.joint_names.iter().all(|s| identifier(s))
                && self
                    .target
                    .joint_names
                    .iter()
                    .collect::<std::collections::BTreeSet<_>>()
                    .len()
                    == 6,
            "JOINTS",
        )?;
        require(
            [
                &self.target.plant_sha256,
                &self.target.calibration_sha256,
                &self.target.adapter_sha256,
                &self.python_sha256,
            ]
            .iter()
            .all(|s| digest(s)),
            "CONFIG_DIGEST",
        )?;
        require(
            self.target.host_arch == std::env::consts::ARCH
                && self.target.host_os == std::env::consts::OS,
            "HOST_COMPATIBILITY",
        )?;
        require(
            [
                &self.ca_der_path,
                &self.bearer_file,
                &self.python,
                &self.adapter,
            ]
            .iter()
            .all(|p| p.is_absolute()),
            "LOCAL_ABSOLUTE_PATHS",
        )
    }
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Bundle {
    pub schema: String,
    pub manifest_json: String,
    pub signature_hex: String,
    pub behavior_json: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Manifest {
    pub schema: String,
    pub release_id: String,
    pub skill_id: String,
    pub sequence: i64,
    pub issued_at_ms: u64,
    pub not_before_ms: u64,
    pub expires_at_ms: u64,
    pub origin: String,
    pub target: Target,
    pub behavior_sha256: String,
    pub behavior_size: usize,
    pub recovery_of: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Behavior {
    pub schema: String,
    pub goals: Vec<[f64; 6]>,
}
fn verify(bundle: &Bundle, cfg: &Config, now: u64) -> Result<(String, Manifest, Behavior)> {
    require(
        serde_json::to_vec(bundle)?.len() <= MAX_BUNDLE && bundle.manifest_json.len() <= 16384,
        "SIZE",
    )?;
    require(
        bundle.schema == "evy-aeris.transfer-bundle.v2",
        "BUNDLE_SCHEMA",
    )?;
    let public = VerifyingKey::from_bytes(&decode(&cfg.publisher_public_hex)?)
        .map_err(|_| Error("KEY".into()))?;
    let signature = Signature::from_bytes(&decode(&bundle.signature_hex)?);
    public
        .verify_strict(
            &[DOMAIN, bundle.manifest_json.as_bytes()].concat(),
            &signature,
        )
        .map_err(|_| Error("SIGNATURE".into()))?;
    let id = sha(bundle.manifest_json.as_bytes());
    require(cfg.approved_manifests.contains(&id), "NOT_LOCALLY_APPROVED")?;
    let m: Manifest = serde_json::from_str(&bundle.manifest_json)?;
    require(
        m.schema == "evy-aeris.transfer-release.v2"
            && m.origin == "existing_deterministic_behavior",
        "MANIFEST_PROFILE",
    )?;
    require(
        identifier(&m.release_id) && identifier(&m.skill_id) && m.sequence > 0,
        "IDENTITY",
    )?;
    require(
        m.issued_at_ms <= m.not_before_ms
            && m.not_before_ms <= now
            && now < m.expires_at_ms
            && m.expires_at_ms
                .checked_sub(m.issued_at_ms)
                .is_some_and(|x| x <= 7 * 86400000),
        "VALIDITY",
    )?;
    require(m.target == cfg.target, "COMPATIBILITY")?;
    require(
        digest(&m.behavior_sha256)
            && m.behavior_sha256 == sha(bundle.behavior_json.as_bytes())
            && m.behavior_size == bundle.behavior_json.len(),
        "BEHAVIOR_IDENTITY",
    )?;
    require(
        m.recovery_of.as_ref().is_none_or(|s| digest(s)),
        "RECOVERY_IDENTITY",
    )?;
    let b: Behavior = serde_json::from_str(&bundle.behavior_json)?;
    require(
        b.schema == "aeris.bounded-joint-goals.v1" && !b.goals.is_empty() && b.goals.len() <= 4,
        "BEHAVIOR_PROFILE",
    )?;
    require(
        b.goals.iter().all(|q| {
            q.iter()
                .zip(aeris_control_v2::HOME)
                .all(|(x, h)| x.is_finite() && (x - h).abs() <= 0.35)
        }),
        "GOAL_OUTSIDE_RECIPE",
    )?;
    Ok((id, m, b))
}
#[cfg(feature = "fault-injection")]
pub fn fault(point: &str) {
    if std::env::var("AERIS_TRANSFER_CRASH_AT").ok().as_deref() == Some(point) {
        std::process::exit(86);
    }
}
#[cfg(not(feature = "fault-injection"))]
pub fn fault(_: &str) {}

// An OS-owned lock dies with the executor process. Database RUNNING ownership does not.
// All operations that can change motion ownership acquire this same lock.
pub struct ExecutionLock(File);
impl Drop for ExecutionLock {
    fn drop(&mut self) {
        unsafe {
            libc::flock(self.0.as_raw_fd(), libc::LOCK_UN);
        }
    }
}
fn execution_lock(path: &Path) -> Result<ExecutionLock> {
    lock_file(&path.with_extension("executor-lock"))
}
fn action_lock(path: &Path) -> Result<ExecutionLock> {
    lock_file(&path.with_extension("action-lock"))
}
fn lock_file(path: &Path) -> Result<ExecutionLock> {
    let f = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
    require(
        unsafe { libc::flock(f.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } == 0,
        "EXECUTOR_BUSY",
    )?;
    Ok(ExecutionLock(f))
}

pub struct Store {
    pub(crate) conn: Connection,
    pub(crate) cfg: Config,
    pub(crate) path: PathBuf,
}
impl Store {
    pub fn open(path: impl AsRef<Path>, cfg: &Config) -> Result<Self> {
        cfg.validate()?;
        let path = path.as_ref().to_path_buf();
        let mut conn = Connection::open(&path)?;
        conn.busy_timeout(Duration::from_secs(2))?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY CHECK(id=1), config_sha TEXT NOT NULL, floor INTEGER NOT NULL, active TEXT);
          CREATE TABLE IF NOT EXISTS releases(digest TEXT PRIMARY KEY, sequence INTEGER UNIQUE NOT NULL, bundle TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, release_digest TEXT NOT NULL REFERENCES releases(digest), status TEXT NOT NULL, receipt TEXT);
          CREATE TABLE IF NOT EXISTS samples(task TEXT NOT NULL REFERENCES tasks(id), tick INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(task,tick));
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, request TEXT NOT NULL);")?;
        let check: String = conn.query_row("PRAGMA quick_check", [], |r| r.get(0))?;
        require(check == "ok", "DATABASE_INTEGRITY")?;
        let config_sha = sha(&serde_json::to_vec(cfg)?);
        let tx = conn.transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute(
            "INSERT OR IGNORE INTO meta VALUES(1,?1,0,NULL)",
            [&config_sha],
        )?;
        let pinned: String =
            tx.query_row("SELECT config_sha FROM meta WHERE id=1", [], |r| r.get(0))?;
        require(pinned == config_sha, "LOCAL_CONFIG_CHANGED")?;
        tx.commit()?;
        Ok(Self {
            conn,
            cfg: cfg.clone(),
            path,
        })
    }
    pub fn stage(&mut self, bundle: &Bundle, now: u64) -> Result<String> {
        let (id, m, _) = verify(bundle, &self.cfg, now)?;
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let existing: Option<String> = tx
            .query_row("SELECT bundle FROM releases WHERE digest=?1", [&id], |r| {
                r.get(0)
            })
            .optional()?;
        if let Some(bytes) = existing {
            require(
                bytes == serde_json::to_string(bundle)?,
                "IDENTITY_COLLISION",
            )?;
            return Ok(id);
        }
        let floor: i64 = tx.query_row("SELECT floor FROM meta WHERE id=1", [], |r| r.get(0))?;
        require(m.sequence > floor, "REPLAYED_SEQUENCE")?;
        if let Some(old) = &m.recovery_of {
            let bytes: String = tx
                .query_row("SELECT bundle FROM releases WHERE digest=?1", [old], |r| {
                    r.get(0)
                })
                .optional()?
                .ok_or_else(|| Error("UNKNOWN_RECOVERY_SOURCE".into()))?;
            let old: Bundle = serde_json::from_str(&bytes)?;
            require(
                sha(old.behavior_json.as_bytes()) == m.behavior_sha256,
                "RECOVERY_BYTES_DIFFER",
            )?;
        }
        tx.execute(
            "INSERT INTO releases VALUES(?1,?2,?3)",
            params![id, m.sequence, serde_json::to_string(bundle)?],
        )?;
        tx.execute("UPDATE meta SET floor=?1 WHERE id=1", [m.sequence])?;
        tx.execute(
            "INSERT INTO events(kind,payload) VALUES('STAGED',?1)",
            [
                json!({"digest":id,"sequence":m.sequence,"received_verified_bytes":true})
                    .to_string(),
            ],
        )?;
        fault("stage-before-commit");
        tx.commit()?;
        fault("stage-after-commit");
        Ok(id)
    }
    pub fn fetch(&mut self) -> Result<String> {
        self.fetch_bound(None)
    }
    pub fn fetch_for_release(&mut self, id: &str, skill: &str) -> Result<String> {
        require(digest(id) && identifier(skill), "ACTION_IDENTITY")?;
        self.fetch_bound(Some((id, skill)))
    }
    fn fetch_bound(&mut self, expected: Option<(&str, &str)>) -> Result<String> {
        // Endpoint, CA, token, signer and approval policy all come from local config.
        let ca = reqwest::Certificate::from_der(&read_bounded(&self.cfg.ca_der_path, 16384)?)
            .map_err(|_| Error("CA".into()))?;
        let token = String::from_utf8(read_bounded(&self.cfg.bearer_file, 256)?)
            .map_err(|_| Error("TOKEN".into()))?;
        require(
            token.len() >= 32 && token.bytes().all(|b| b.is_ascii_alphanumeric()),
            "TOKEN",
        )?;
        let client = reqwest::blocking::Client::builder()
            .https_only(true)
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(Duration::from_secs(5))
            .connect_timeout(Duration::from_secs(2))
            .tls_certs_only([ca])
            .build()
            .map_err(|_| Error("TLS_CLIENT".into()))?;
        let response = client
            .get(&self.cfg.publisher_url)
            .bearer_auth(token)
            .send()
            .map_err(|error| {
                let mut source = std::error::Error::source(&error);
                while let Some(cause) = source {
                    eprintln!("Transport cause: {cause}");
                    source = cause.source();
                }
                Error("TRANSPORT_FAILED".into())
            })?;
        require(response.status() == reqwest::StatusCode::OK, "HTTP_STATUS")?;
        require(
            response
                .content_length()
                .is_none_or(|n| n <= MAX_BUNDLE as u64),
            "SIZE",
        )?;
        let mut bytes = Vec::new();
        response
            .take((MAX_BUNDLE + 1) as u64)
            .read_to_end(&mut bytes)
            .map_err(|_| Error("DOWNLOAD_INTERRUPTED".into()))?;
        require(bytes.len() <= MAX_BUNDLE, "SIZE")?;
        let bundle: Bundle = serde_json::from_slice(&bytes)?;
        let now = now_ms()?;
        if let Some((expected_id, skill)) = expected {
            let (id, m, _) = verify(&bundle, &self.cfg, now)?;
            require(
                id == expected_id && m.skill_id == skill,
                "UNEXPECTED_REMOTE_CAPABILITY",
            )?;
        }
        self.stage(&bundle, now)
    }
    pub fn activate(&mut self, id: &str, now: u64) -> Result<Value> {
        require(digest(id), "DIGEST")?;
        let _lock = execution_lock(&self.path)?;
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let busy: i64 = tx.query_row(
            "SELECT count(*) FROM tasks WHERE status='RUNNING'",
            [],
            |r| r.get(0),
        )?;
        require(busy == 0, "RECOVERY_REQUIRED")?;
        let bytes: String =
            tx.query_row("SELECT bundle FROM releases WHERE digest=?1", [id], |r| {
                r.get(0)
            })?;
        let (verified_id, m, _) = verify(&serde_json::from_str(&bytes)?, &self.cfg, now)?;
        require(verified_id == id, "STORED_DIGEST_CHANGED")?;
        let (floor, active): (i64, Option<String>) =
            tx.query_row("SELECT floor,active FROM meta WHERE id=1", [], |r| {
                Ok((r.get(0)?, r.get(1)?))
            })?;
        // Duplicate ACK is safe only if it names the currently active release.
        if active.as_deref() == Some(id) {
            return Ok(json!({"status":"ALREADY_ACTIVE","digest":id}));
        }
        require(m.sequence == floor, "SUPERSEDED_RELEASE")?;
        tx.execute("UPDATE meta SET active=?1 WHERE id=1", [id])?;
        tx.execute(
            "INSERT INTO events(kind,payload) VALUES('ACTIVATED',?1)",
            [json!({"digest":id,"sequence":m.sequence}).to_string()],
        )?;
        fault("activate-before-commit");
        tx.commit()?;
        fault("activate-after-commit");
        Ok(json!({"status":"ACTIVE","digest":id,"sequence":m.sequence,"simulation_only":true}))
    }
    pub fn recover(&mut self) -> Result<Value> {
        let _lock = execution_lock(&self.path)?;
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let count=tx.execute("UPDATE tasks SET status='INTERRUPTED',receipt=json_object('status','INTERRUPTED','simulation_reset_required',json('true'),'physical_resume_authorized',json('false')) WHERE status='RUNNING'",[])?;
        tx.execute("INSERT INTO events(kind,payload) VALUES('RECOVERED',?1)",[json!({"interrupted_tasks":count,"action":"Explicit simulated task interruption; next new task starts at home","physical_resume_authorized":false}).to_string()])?;
        tx.commit()?;
        Ok(
            json!({"status":"RECOVERED","interrupted_tasks":count,"physical_resume_authorized":false}),
        )
    }
    pub fn status(&self) -> Result<Value> {
        let tx = self.conn.unchecked_transaction()?;
        let (floor, active): (i64, Option<String>) =
            tx.query_row("SELECT floor,active FROM meta WHERE id=1", [], |r| {
                Ok((r.get(0)?, r.get(1)?))
            })?;
        let seq: Option<i64> = tx
            .query_row(
                "SELECT sequence FROM releases WHERE digest=?1",
                [&active],
                |r| r.get(0),
            )
            .optional()?;
        let count: i64 = tx.query_row("SELECT count(*) FROM releases", [], |r| r.get(0))?;
        let mut st = tx.prepare("SELECT id,release_digest,status FROM tasks ORDER BY id")?;
        let tasks=st.query_map([],|r|Ok(json!({"id":r.get::<_,String>(0)?,"release_digest":r.get::<_,String>(1)?,"status":r.get::<_,String>(2)?})))?.collect::<std::result::Result<Vec<_>,_>>()?;
        let mut st = tx.prepare("SELECT kind,payload FROM events ORDER BY id")?;
        let events = st
            .query_map([], |r| {
                Ok(json!({"kind":r.get::<_,String>(0)?,"payload":r.get::<_,String>(1)?}))
            })?
            .collect::<std::result::Result<Vec<_>, _>>()?;
        Ok(
            json!({"sequence_floor":floor,"active_digest":active,"active_sequence":seq,"staged_count":count,"tasks":tasks,"events":events,"simulation_only":true,"physical_motion_authorized":false}),
        )
    }
    pub fn receipt(&self, task: &str) -> Result<Value> {
        let tx = self.conn.unchecked_transaction()?;
        let (id, status, receipt): (String, String, Option<String>) = tx.query_row(
            "SELECT release_digest,status,receipt FROM tasks WHERE id=?1",
            [task],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )?;
        let mut st = tx.prepare("SELECT payload FROM samples WHERE task=?1 ORDER BY tick")?;
        let samples = st
            .query_map([task], |r| r.get::<_, String>(0))?
            .collect::<std::result::Result<Vec<_>, _>>()?;
        let samples: Vec<Value> = samples
            .iter()
            .map(|s| serde_json::from_str(s))
            .collect::<std::result::Result<_, _>>()?;
        Ok(
            json!({"task":task,"release_digest":id,"status":status,"result":receipt.map(|s|serde_json::from_str::<Value>(&s)).transpose()?,"samples":samples,"simulation_only":true,"physical_motion_authorized":false}),
        )
    }
}
