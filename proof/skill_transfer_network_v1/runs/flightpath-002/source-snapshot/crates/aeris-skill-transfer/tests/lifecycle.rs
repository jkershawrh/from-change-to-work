mod test_support;
use aeris_skill_transfer::Store;

#[test]
fn staged_bytes_and_active_pointer_survive_reopen() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    {
        let mut store = Store::open(d.path().join("edge.sqlite"), &cfg).unwrap();
        let id = store.stage(&first, 1000).unwrap();
        store.activate(&id, 1000).unwrap();
        store.stage(&second, 1000).unwrap();
    }
    let store = Store::open(d.path().join("edge.sqlite"), &cfg).unwrap();
    let state = store.status().unwrap();
    assert_eq!(state["active_sequence"], 1);
    assert_eq!(state["sequence_floor"], 2);
    assert_eq!(state["staged_count"], 2);
}

#[test]
fn tampering_and_replay_do_not_change_active_or_floor() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    let mut store = Store::open(d.path().join("edge.sqlite"), &cfg).unwrap();
    let id = store.stage(&second, 1000).unwrap();
    store.activate(&id, 1000).unwrap();
    let before = store.status().unwrap();
    assert!(store.stage(&first, 1000).is_err());
    let mut corrupted = second.clone();
    corrupted.behavior_json.push(' ');
    assert!(store.stage(&corrupted, 1000).is_err());
    assert_eq!(before, store.status().unwrap());
}

#[test]
fn duplicate_delivery_is_idempotent_and_wrong_local_config_refused() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, _) = test_support::fixtures();
    let path = d.path().join("edge.sqlite");
    let mut store = Store::open(&path, &cfg).unwrap();
    let a = store.stage(&first, 1000).unwrap();
    assert_eq!(store.stage(&first, 1000).unwrap(), a);
    assert_eq!(store.status().unwrap()["staged_count"], 1);
    drop(store);
    let mut changed = cfg.clone();
    changed.target.calibration_sha256 = "0".repeat(64);
    assert!(Store::open(path, &changed).is_err());
}

#[test]
fn activation_refuses_a_stored_bundle_under_the_wrong_digest() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    let path = d.path().join("edge.sqlite");
    let mut store = Store::open(&path, &cfg).unwrap();
    let id = store.stage(&first, 1000).unwrap();
    store.stage(&second, 1000).unwrap();
    let conn = rusqlite::Connection::open(path).unwrap();
    conn.execute(
        "UPDATE releases SET bundle=?1 WHERE digest=?2",
        rusqlite::params![serde_json::to_string(&second).unwrap(), id],
    )
    .unwrap();
    assert!(
        store.activate(&id, 1000).is_err(),
        "Stored bytes must still bind the requested digest"
    );
    assert!(store.status().unwrap()["active_digest"].is_null());
}

#[test]
fn orphaned_running_task_blocks_activation_until_explicit_recovery() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    let path = d.path().join("edge.sqlite");
    let mut store = Store::open(&path, &cfg).unwrap();
    let first_id = store.stage(&first, 1000).unwrap();
    store.activate(&first_id, 1000).unwrap();
    let second_id = store.stage(&second, 1000).unwrap();
    let conn = rusqlite::Connection::open(path).unwrap();
    conn.execute(
        "INSERT INTO tasks VALUES('orphan',?1,'RUNNING',NULL)",
        [&first_id],
    )
    .unwrap();
    assert!(store.activate(&second_id, 1000).is_err());
    assert_eq!(store.recover().unwrap()["interrupted_tasks"], 1);
    store.activate(&second_id, 1000).unwrap();
    assert_eq!(store.receipt("orphan").unwrap()["status"], "INTERRUPTED");
    assert_eq!(store.status().unwrap()["sequence_floor"], 2);
}

#[test]
fn signed_contract_rejections_leave_an_empty_store() {
    let (cfg, first, _) = test_support::fixtures();
    let original: aeris_skill_transfer::Manifest =
        serde_json::from_str(&first.manifest_json).unwrap();
    for case in 0..12 {
        let mut m = original.clone();
        let mut behavior = first.behavior_json.clone();
        match case {
            0 => m.target.units = "deg".into(),
            1 => m.target.plant_sha256 = "0".repeat(64),
            2 => m.target.calibration_sha256 = "0".repeat(64),
            3 => m.target.runtime_version = "wrong".into(),
            4 => m.target.joint_names.swap(0, 1),
            5 => m.expires_at_ms = 999,
            6 => m.not_before_ms = 1001,
            7 => m.origin = "unqualified_new_training".into(),
            8 => m.sequence = 0,
            9 => {
                behavior =
                    "{\"schema\":\"aeris.bounded-joint-goals.v1\",\"goals\":[],\"goals\":[]}"
                        .into();
                m.behavior_sha256 = aeris_skill_transfer::sha(behavior.as_bytes());
                m.behavior_size = behavior.len();
            }
            10 => m.recovery_of = Some("9".repeat(64)),
            11 => m.behavior_size += 1,
            _ => unreachable!(),
        }
        let bundle = test_support::sign(&m, behavior);
        let mut local = cfg.clone();
        local
            .approved_manifests
            .push(aeris_skill_transfer::sha(bundle.manifest_json.as_bytes()));
        let d = tempfile::tempdir().unwrap();
        let mut store = Store::open(d.path().join("edge.sqlite"), &local).unwrap();
        assert!(store.stage(&bundle, 1000).is_err(), "case {case}");
        assert_eq!(store.status().unwrap()["sequence_floor"], 0);
        assert_eq!(store.status().unwrap()["staged_count"], 0);
    }
}

#[test]
fn pinned_execution_refuses_another_release_even_for_a_completed_task() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    let path = d.path().join("edge.sqlite");
    let mut store = Store::open(&path, &cfg).unwrap();
    let a = store.stage(&first, 1000).unwrap();
    let b = store.stage(&second, 1000).unwrap();
    let conn = rusqlite::Connection::open(path).unwrap();
    conn.execute(
        "INSERT INTO tasks VALUES('done',?1,'COMPLETE','{\"status\":\"COMPLETE\"}')",
        [&a],
    )
    .unwrap();
    assert!(store.execute_for_release("done", &b, |_| {}).is_err());
    assert_eq!(
        store.execute_for_release("done", &a, |_| {}).unwrap()["idempotent"],
        true
    );
}

#[test]
fn action_identity_is_immutable_across_retries() {
    let d = tempfile::tempdir().unwrap();
    let (cfg, first, second) = test_support::fixtures();
    let mut store = Store::open(d.path().join("edge.sqlite"), &cfg).unwrap();
    let mut request = aeris_skill_transfer::ActionRequest {
        schema: "evy-aeris.transfer-action.v1".into(),
        action_id: "repeatable".into(),
        skill_id: "inspection".into(),
        release_digest: aeris_skill_transfer::sha(first.manifest_json.as_bytes()),
    };
    // Missing local CA makes delivery fail, but cannot erase the request binding.
    assert!(store.run_action(&request, |_| {}).is_err());
    request.release_digest = aeris_skill_transfer::sha(second.manifest_json.as_bytes());
    assert_eq!(
        store.run_action(&request, |_| {}).unwrap_err().0,
        "ACTION_ID_REUSED_WITH_DIFFERENT_REQUEST"
    );
}
