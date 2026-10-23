export const chapters=[
 {
  "id": "cell",
  "label": "The waiting work",
  "act": "THE CALL",
  "title": "The change is ready.\nThe part is waiting.",
  "line": "Engineering has the next task. The cell needs an approved way to run it.",
  "question": "Why is the part still waiting?",
  "answer": "The gap is the handoff from engineering intent to an accepted task at the receiving cell.",
  "prompt": "Open with the manufacturing handoff. The airframe and waiting work are illustrative; no delay or savings have been measured.",
  "focus": "cell"
 },
 {
  "id": "recipe",
  "label": "Package the change",
  "act": "THE THRESHOLD",
  "title": "Make the change\nready for the cell.",
  "line": "A bounded task. A named receiving profile. A result we can trace.",
  "question": "What must travel with the task?",
  "answer": "The approved recipe, exact release identity and target profile. Local approval stays with the cell.",
  "prompt": "Use the exploded work package to explain responsibilities. Save signature and sequence details for inspection.",
  "focus": "cell"
 },
 {
  "id": "architecture",
  "label": "Deliver with intent",
  "act": "THE CROSSING",
  "title": "Deliver the task.\nEarn acceptance.",
  "line": "Engineering prepares. The channel delivers. The receiving cell decides.",
  "question": "Who can activate the task, and when?",
  "answer": "Rust verifies the package and local approval, then activates only while idle.",
  "prompt": "Follow preparation, delivery and local admission. Keep the engineering mechanism available through question-first reveals.",
  "focus": "cell"
 },
 {
  "id": "disconnect",
  "label": "Local work",
  "act": "THE FIRST TRIAL",
  "title": "The link is cut.\nThe cell owns the work.",
  "line": "The central data plane goes away. Local execution keeps its task.",
  "question": "What survives the connection cut?",
  "answer": "The finite simulator task can finish without the central data plane. A separate observer stays available.",
  "prompt": "Now reveal the detailed 3D cell. Retained poses are playback; actual controls live in the workbench.",
  "focus": "cell"
 },
 {
  "id": "recovery",
  "label": "Account for the work",
  "act": "THE ORDEAL",
  "title": "Keep the history.\nChoose the next task.",
  "line": "Interrupted work stays interrupted. Recovery is a deliberate decision.",
  "question": "Does recovery restart uncertain work?",
  "answer": "No. The old task is recorded as interrupted. Another execution requires a deliberately new action.",
  "prompt": "Read the forked history from left to right. Never paint interrupted work as completed.",
  "focus": "cell"
 },
 {
  "id": "ecosystem",
  "label": "Repeat the process",
  "act": "THE RETURN",
  "title": "New work.\nA familiar handoff.",
  "line": "Reuse delivery and recovery. Qualify each task profile and cell.",
  "question": "Can the process support more than inspection?",
  "answer": "Inspection and rework positioning already share it in simulation. Different device interfaces require reviewed adapters.",
  "prompt": "Separate existing simulator tasks from future concepts. No fleet, machine-tending implementation or production support claim.",
  "focus": "cell"
 },
 {
  "id": "qualify",
  "label": "Choose the pilot",
  "act": "THE NEXT JOURNEY",
  "title": "One task. One cell.\nA testable decision.",
  "line": "Measure rollout effort, recovery effort and the task outcome.",
  "question": "What should the first pilot establish?",
  "answer": "Named compute hosts, one bounded task, an acceptance owner and inspectable evidence.",
  "prompt": "Hand off deliberately into the dashboard. Local simulation, Intel/Red Hat compute, physical acceptance and business value are separate gates.",
  "focus": "cell"
 }
] as const
export const architectureLayers=[
 {question:'Who asks for the change?',answer:'An operator selects an approved capability.',component:'OPERATOR → DISPATCH',detail:'Same-origin request; immutable action ID and configured destination.',ids:['operator','evy']},
 {question:'Who checks what arrived?',answer:'Rust admits only an exact locally approved release.',component:'HTTPS → LOCAL VERIFICATION',detail:'Signature, approval, profile, time, sequence and bounded content.',ids:['signature','edge']},
 {question:'Who owns the next move?',answer:'The local executor pins the task and owns execution.',component:'RUST → CONTROLLER → MUJOCO',detail:'Idle activation and local IPC; central traffic is outside the control loop.',ids:['rust','plant']},
 {question:'What survives a failure?',answer:'Durable task identity, committed samples and an explicit receipt.',component:'LOCAL STATE → OBSERVATION',detail:'A separate observer is not a safety channel. An export still requires independent audit.',ids:['receipt','observer']},
] as const
export const mechanisms=[
 {id:'signature',name:'Admission gate',detail:'Exact signed bytes meet the configured local approval, target, expiry and sequence rules. This is not physical safety certification.'},
 {id:'ownership',name:'Execution ownership',detail:'Idle activation, pinned releases and an OS-owned lock keep a task tied to the version it started with.'},
 {id:'state',name:'Durable state',detail:'SQLite WAL retains action identity, committed samples and terminal receipts. This is trusted local state, not an externally anchored immutable ledger.'},
 {id:'compute',name:'Qualified compute',detail:'Intel × Red Hat is the target. A new compute host still needs measured identity, resource and workload acceptance. No accelerator benefit is assumed.'},
] as const
