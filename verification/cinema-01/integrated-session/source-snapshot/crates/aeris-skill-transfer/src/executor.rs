//! Local stepped simulator adapter. Network delivery never enters this control loop.
use crate::*;
use aeris_control_v2::{self as mpc, DT, HOME};
use std::{
    io::{BufRead, BufReader, Write},
    process::{Child, ChildStdin, Command, Stdio},
    sync::mpsc::{self, Receiver},
    thread::JoinHandle,
    time::Instant,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct State {
    q: [f64; 6],
    velocity: [f64; 6],
    simulation_seconds: f64,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Substep {
    index: usize,
    simulation_seconds: f64,
    q: [f64; 6],
    velocity_before: [f64; 6],
    velocity: [f64; 6],
    finite_difference_acceleration: [f64; 6],
    native_acceleration: [f64; 6],
    requested_torque_nm: [f64; 6],
    applied_torque_nm: [f64; 6],
    disturbance_nm: [f64; 6],
    contacts: Vec<Value>,
}
#[derive(Deserialize)]
#[serde(tag = "kind", deny_unknown_fields)]
enum Reply {
    Ready {
        plant_sha256: String,
        runtime_version: String,
        joint_names: [String; 6],
    },
    Observed {
        state: State,
    },
    Checked {
        clear: bool,
    },
    Stepped {
        state: State,
        substeps: Vec<Substep>,
    },
}
struct Adapter {
    child: Child,
    input: ChildStdin,
    rx: Option<Receiver<Result<String>>>,
    reader: Option<JoinHandle<()>>,
}
impl Adapter {
    fn start(cfg: &Config) -> Result<Self> {
        require(
            sha(&read_bounded(&cfg.adapter, 65536)?) == cfg.target.adapter_sha256,
            "ADAPTER_CHANGED",
        )?;
        require(
            sha(&read_bounded(&cfg.python, 128 * 1024 * 1024)?) == cfg.python_sha256,
            "PYTHON_CHANGED",
        )?;
        let mut child = Command::new(&cfg.python)
            .arg("-B")
            .arg(&cfg.adapter)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()?;
        let input = child
            .stdin
            .take()
            .ok_or_else(|| Error("ADAPTER_STDIN".into()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| Error("ADAPTER_STDOUT".into()))?;
        let (tx, rx) = mpsc::sync_channel(1);
        let reader = std::thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut bytes = Vec::new();
                let result = std::io::Read::by_ref(&mut reader)
                    .take(262145)
                    .read_until(b'\n', &mut bytes);
                let line: Result<String> = (|| {
                    let n = result?;
                    require(
                        n > 0 && n <= 262144 && bytes.last() == Some(&b'\n'),
                        "ADAPTER_LINE_BOUND",
                    )?;
                    String::from_utf8(bytes).map_err(|_| Error("ADAPTER_UTF8".into()))
                })();
                let end = line.is_err();
                if tx.send(line).is_err() || end {
                    break;
                }
            }
        });
        let a = Self {
            child,
            input,
            rx: Some(rx),
            reader: Some(reader),
        };
        match a.read(Duration::from_secs(5))? {
            Reply::Ready {
                plant_sha256,
                runtime_version,
                joint_names,
            } => require(
                plant_sha256 == cfg.target.plant_sha256
                    && runtime_version == cfg.target.runtime_version
                    && joint_names == cfg.target.joint_names,
                "OBSERVED_SIMULATOR_INCOMPATIBLE",
            )?,
            _ => return Err(Error("ADAPTER_READY".into())),
        }
        Ok(a)
    }
    fn read(&self, timeout: Duration) -> Result<Reply> {
        let line = self
            .rx
            .as_ref()
            .ok_or_else(|| Error("ADAPTER_CLOSED".into()))?
            .recv_timeout(timeout)
            .map_err(|_| Error("ADAPTER_TIMEOUT_OR_EXIT".into()))??;
        Ok(serde_json::from_str(&line)?)
    }
    fn call(&mut self, value: Value) -> Result<Reply> {
        writeln!(self.input, "{value}")?;
        self.input.flush()?;
        self.read(Duration::from_secs(2))
    }
}
impl Drop for Adapter {
    fn drop(&mut self) {
        // Parent death closes stdin too; adapter advances at most one 20 ms interval
        // without a fresh command, then exits on EOF. There is no robot connection.
        let _ = self.child.kill();
        let _ = self.child.wait();
        self.rx.take();
        if let Some(reader) = self.reader.take() {
            let _ = reader.join();
        }
    }
}
fn validate_step(before: &State, after: &State, steps: &[Substep]) -> Result<()> {
    require(steps.len() == 10, "SUBSTEP_COUNT")?;
    let mut prev_time = before.simulation_seconds;
    let mut prev_velocity = before.velocity;
    for (i, s) in steps.iter().enumerate() {
        require(
            s.index == i
                && (s.simulation_seconds - prev_time - 0.002).abs() < 1e-9
                && s.contacts.is_empty(),
            "TIME_OR_CONTACT",
        )?;
        for j in 0..6 {
            let finite = [
                s.q[j],
                s.velocity[j],
                s.velocity_before[j],
                s.finite_difference_acceleration[j],
                s.native_acceleration[j],
                s.applied_torque_nm[j],
                s.requested_torque_nm[j],
                s.disturbance_nm[j],
            ]
            .iter()
            .all(|x| x.is_finite());
            require(
                finite
                    && (s.q[j] - HOME[j]).abs() <= 0.65 + 1e-6
                    && s.velocity[j].abs() <= 0.45 + 1e-6
                    && s.finite_difference_acceleration[j].abs() <= 1.2 + 1e-6
                    && s.native_acceleration[j].abs() <= 1.2 + 1e-6,
                "MEASURED_LIMIT",
            )?;
            require(
                (s.velocity_before[j] - prev_velocity[j]).abs() < 1e-9
                    && ((s.velocity[j] - prev_velocity[j]) / 0.002
                        - s.finite_difference_acceleration[j])
                        .abs()
                        < 1e-8,
                "SUBSTEP_CONTINUITY",
            )?;
        }
        prev_time = s.simulation_seconds;
        prev_velocity = s.velocity;
    }
    let last = &steps[9];
    require(
        after.q == last.q
            && after.velocity == last.velocity
            && after.simulation_seconds == last.simulation_seconds,
        "STATE_CONTINUITY",
    )
}
impl Store {
    pub fn execute(&mut self, task: &str, progress: impl FnMut(Value)) -> Result<Value> {
        self.execute_pinned(task, None, progress)
    }
    pub fn execute_for_release(
        &mut self,
        task: &str,
        expected: &str,
        progress: impl FnMut(Value),
    ) -> Result<Value> {
        require(digest(expected), "DIGEST")?;
        self.execute_pinned(task, Some(expected), progress)
    }
    fn execute_pinned(
        &mut self,
        task: &str,
        expected: Option<&str>,
        mut progress: impl FnMut(Value),
    ) -> Result<Value> {
        require(identifier(task), "TASK_ID")?;
        let _lock = execution_lock(&self.path)?;
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let existing: Option<(String, Option<String>, String)> = tx
            .query_row(
                "SELECT status,receipt,release_digest FROM tasks WHERE id=?1",
                [task],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
            )
            .optional()?;
        if let Some((status, receipt, release)) = existing {
            require(
                expected.is_none_or(|id| id == release),
                "TASK_RELEASE_MISMATCH",
            )?;
            require(status != "RUNNING", "RECOVERY_REQUIRED")?;
            return Ok(
                json!({"status":status,"task":task,"idempotent":true,"result":receipt.map(|s|serde_json::from_str::<Value>(&s)).transpose()?}),
            );
        }
        let running: i64 = tx.query_row(
            "SELECT count(*) FROM tasks WHERE status='RUNNING'",
            [],
            |r| r.get(0),
        )?;
        require(running == 0, "RECOVERY_REQUIRED")?;
        let id: String = tx.query_row("SELECT active FROM meta WHERE id=1", [], |r| r.get(0))?;
        require(
            expected.is_none_or(|expected| expected == id),
            "ACTIVE_RELEASE_CHANGED",
        )?;
        let bytes: String =
            tx.query_row("SELECT bundle FROM releases WHERE digest=?1", [&id], |r| {
                r.get(0)
            })?;
        let (verified_id, manifest, behavior) =
            verify(&serde_json::from_str(&bytes)?, &self.cfg, now_ms()?)?;
        require(id == verified_id, "STORED_DIGEST_CHANGED")?;
        tx.execute(
            "INSERT INTO tasks VALUES(?1,?2,'RUNNING',NULL)",
            params![task, id],
        )?;
        tx.execute(
            "INSERT INTO events(kind,payload) VALUES('TASK_STARTED',?1)",
            [json!({"task":task,"digest":id,"sequence":manifest.sequence}).to_string()],
        )?;
        tx.commit()?;
        fault("task-after-start");
        progress(
            json!({"event":"TASK_STARTED","task":task,"release_digest":id,"sequence":manifest.sequence}),
        );
        let started = Instant::now();
        let started_at_unix_ms = now_ms()?;
        let mut ticks = 0;
        let mut completed_goals = 0;
        let mut deadline_refusals = 0;
        let result: Result<()> = (|| {
            let mut adapter = Adapter::start(&self.cfg)?;
            progress(json!({"event":"ADAPTER_READY","pid":adapter.child.id(),"task":task}));
            for (goal_index, target) in behavior.goals.iter().enumerate() {
                let mut held = 0;
                let mut done = false;
                for _ in 0..400 {
                    let observed_at = Instant::now();
                    let observed_at_unix_ms = now_ms()?;
                    let before = match adapter.call(json!({"kind":"observe"}))? {
                        Reply::Observed { state } => state,
                        _ => return Err(Error("OBSERVE_PROTOCOL".into())),
                    };
                    let request = mpc::Request {
                        sequence: ticks + 1,
                        observation_age_ms: observed_at.elapsed().as_secs_f64() * 1000.,
                        q: before.q,
                        velocity: before.velocity,
                        target: *target,
                    };
                    mpc::validate(&request, None).map_err(|s| Error(s.into()))?;
                    let solved_at = Instant::now();
                    let plan = mpc::solve(&request);
                    let mut acceleration = plan.acceleration.unwrap_or_else(|| {
                        before
                            .velocity
                            .map(|v| (-v / DT).clamp(-mpc::AMAX, mpc::AMAX))
                    });
                    let mut outcome = plan.reason.clone().unwrap_or_else(|| "MPC_DISPATCH".into());
                    let positions = if plan.status == "PLANNED" {
                        plan.positions
                    } else {
                        vec![before.q]
                    };
                    let clear = match adapter.call(json!({"kind":"check","positions":positions}))? {
                        Reply::Checked { clear } => clear,
                        _ => return Err(Error("CHECK_PROTOCOL".into())),
                    };
                    if plan.status == "PLANNED" {
                        if let Err(reason) = mpc::dispatch_allowed(
                            solved_at.elapsed().as_secs_f64() * 1000.,
                            request.observation_age_ms,
                            clear,
                        ) {
                            outcome = reason.into();
                            deadline_refusals += 1;
                            acceleration = before
                                .velocity
                                .map(|v| (-v / DT).clamp(-mpc::AMAX, mpc::AMAX));
                        }
                    }
                    // Gate the fallback's own sampled braking path, too.
                    if outcome != "MPC_DISPATCH" {
                        let end = std::array::from_fn::<_, 6, _>(|j| {
                            before.q[j] + before.velocity[j] * DT + 0.5 * acceleration[j] * DT * DT
                        });
                        let clear = match adapter.call(json!({"kind":"check","positions":[end]}))? {
                            Reply::Checked { clear } => clear,
                            _ => false,
                        };
                        require(clear, "FALLBACK_COLLISION")?;
                    } else {
                        require(clear, "COLLISION_GATE")?;
                    }
                    let (after, substeps) =
                        match adapter.call(json!({"kind":"step","acceleration":acceleration}))? {
                            Reply::Stepped { state, substeps } => (state, substeps),
                            _ => return Err(Error("STEP_PROTOCOL".into())),
                        };
                    let checked = validate_step(&before, &after, &substeps);
                    let sample = json!({"tick":ticks,"observed_at_unix_ms":observed_at_unix_ms,"goal_index":goal_index,"target":target,"before":before,"after":after,"acceleration_command":acceleration,"controller_outcome":outcome,"solve_ms":plan.solve_ms,"physics_substeps":substeps,"release_digest":id,"task":task,"valid":checked.is_ok()});
                    self.conn.execute(
                        "INSERT INTO samples VALUES(?1,?2,?3)",
                        params![task, ticks, sample.to_string()],
                    )?;
                    ticks += 1;
                    fault("task-after-step");
                    checked?;
                    if ticks == 1 || ticks % 10 == 0 {
                        progress(
                            json!({"event":"SIM_PROGRESS","task":task,"tick":ticks,"observed_at_unix_ms":observed_at_unix_ms,"goal_index":goal_index,"release_digest":id}),
                        );
                    }
                    let close = after
                        .q
                        .iter()
                        .zip(target)
                        .all(|(q, t)| (q - t).abs() < 0.015)
                        && after.velocity.iter().all(|v| v.abs() < 0.025);
                    held = if close { held + 1 } else { 0 };
                    if held >= 10 {
                        done = true;
                        completed_goals += 1;
                        break;
                    }
                }
                require(done, "SIM_GOAL_TIMEOUT")?;
            }
            Ok(())
        })();
        let status = if result.is_ok() { "COMPLETE" } else { "FAILED" };
        let receipt = json!({"schema":"evy-aeris.sim-transfer-receipt.v2","status":status,"task":task,"release_digest":id,"sequence":manifest.sequence,"behavior_sha256":manifest.behavior_sha256,"target":self.cfg.target,"ticks":ticks,"completed_goals":completed_goals,"requested_goals":behavior.goals.len(),"deadline_refusals":deadline_refusals,"started_at_unix_ms":started_at_unix_ms,"completed_at_unix_ms":now_ms()?,"host_elapsed_ms":started.elapsed().as_secs_f64()*1000.,"error":result.err().map(|e|e.0),"simulation_only":true,"physical_motion_authorized":false,"training_required":false});
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute(
            "UPDATE tasks SET status=?1,receipt=?2 WHERE id=?3",
            params![status, receipt.to_string(), task],
        )?;
        tx.execute(
            "INSERT INTO events(kind,payload) VALUES('TASK_FINISHED',?1)",
            [receipt.to_string()],
        )?;
        tx.commit()?;
        fault("task-after-complete");
        Ok(receipt)
    }
}
