//! Reusable, locally invoked transfer action. No remote trust/config overrides.
use crate::*;
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActionRequest {
    pub schema: String,
    pub action_id: String,
    pub skill_id: String,
    pub release_digest: String,
}
impl Store {
    pub fn run_action(
        &mut self,
        request: &ActionRequest,
        mut progress: impl FnMut(Value),
    ) -> Result<Value> {
        require(
            request.schema == "evy-aeris.transfer-action.v1"
                && identifier(&request.action_id)
                && request.action_id.len() <= 80
                && identifier(&request.skill_id)
                && digest(&request.release_digest),
            "ACTION_CONTRACT",
        )?;
        // A distinct action lock serializes orchestration; the existing executor
        // lock still owns every activation/execution/recovery boundary.
        let _action_lock = action_lock(&self.path)?;
        let encoded = serde_json::to_string(request)?;
        let tx = self
            .conn
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute(
            "INSERT OR IGNORE INTO actions VALUES(?1,?2)",
            params![request.action_id, encoded],
        )?;
        let saved: String = tx.query_row(
            "SELECT request FROM actions WHERE id=?1",
            [&request.action_id],
            |r| r.get(0),
        )?;
        require(saved == encoded, "ACTION_ID_REUSED_WITH_DIFFERENT_REQUEST")?;
        tx.commit()?;
        let task = format!("action-{}", request.action_id);
        let existing: Option<String> = self
            .conn
            .query_row(
                "SELECT release_digest FROM tasks WHERE id=?1",
                [&task],
                |r| r.get(0),
            )
            .optional()?;
        if let Some(id) = existing {
            require(id == request.release_digest, "TASK_RELEASE_MISMATCH")?;
            let encoded: String =
                self.conn
                    .query_row("SELECT bundle FROM releases WHERE digest=?1", [&id], |r| {
                        r.get(0)
                    })?;
            let bundle: Bundle = serde_json::from_str(&encoded)?;
            let manifest: Manifest = serde_json::from_str(&bundle.manifest_json)?;
            require(
                sha(bundle.manifest_json.as_bytes()) == id && manifest.skill_id == request.skill_id,
                "ACTION_CAPABILITY_MISMATCH",
            )?;
        } else {
            let cached: Option<String> = self
                .conn
                .query_row(
                    "SELECT bundle FROM releases WHERE digest=?1",
                    [&request.release_digest],
                    |r| r.get(0),
                )
                .optional()?;
            if let Some(bytes) = cached {
                let bundle: Bundle = serde_json::from_str(&bytes)?;
                let (id, manifest, _) = verify(&bundle, &self.cfg, now_ms()?)?;
                require(
                    id == request.release_digest && manifest.skill_id == request.skill_id,
                    "ACTION_CAPABILITY_MISMATCH",
                )?;
            } else {
                self.fetch_for_release(&request.release_digest, &request.skill_id)?;
            }
            self.activate(&request.release_digest, now_ms()?)?;
        }
        let result = self.execute_for_release(&task, &request.release_digest, &mut progress)?;
        Ok(
            json!({"schema":"evy-aeris.transfer-action-result.v1","action_id":request.action_id,"skill_id":request.skill_id,"release_digest":request.release_digest,"task":task,"status":result["status"],"idempotent":result.get("idempotent").and_then(Value::as_bool).unwrap_or(false),"receipt":result,"simulation_only":true,"physical_motion_authorized":false}),
        )
    }
}
