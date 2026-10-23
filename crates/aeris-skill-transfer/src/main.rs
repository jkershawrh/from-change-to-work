use aeris_skill_transfer::{
    ActionRequest, Bundle, Config, Error, MAX_BUNDLE, Result, Store, now_ms, read_bounded, require,
};
use serde_json::{Value, json};
use std::{io::Write, path::Path};
fn emit(value: Value) {
    println!("{value}");
    let _ = std::io::stdout().flush();
}
fn run() -> Result<Value> {
    let args: Vec<_> = std::env::args().collect();
    require(
        args.len() >= 4,
        "USAGE: aeris-skill-transfer CONFIG DB COMMAND [ARG]",
    )?;
    let cfg = Config::load(Path::new(&args[1]))?;
    let mut store = Store::open(&args[2], &cfg)?;
    let argument = || args.get(4).ok_or_else(|| Error("ARGUMENT_REQUIRED".into()));
    match args[3].as_str() {
        "action" => {
            let request: ActionRequest =
                serde_json::from_slice(&read_bounded(Path::new(argument()?), 4096)?)?;
            store.run_action(&request, emit)
        }
        "fetch" => Ok(json!({"status":"STAGED","digest":store.fetch()?})),
        "stage" => {
            let b: Bundle =
                serde_json::from_slice(&read_bounded(Path::new(argument()?), MAX_BUNDLE)?)?;
            Ok(json!({"status":"STAGED","digest":store.stage(&b,now_ms()?)?}))
        }
        "activate" => store.activate(argument()?, now_ms()?),
        "execute" => store.execute(argument()?, emit),
        "recover" => store.recover(),
        "status" => store.status(),
        "receipt" => store.receipt(argument()?),
        _ => Err(Error("UNKNOWN_COMMAND".into())),
    }
}
fn main() {
    match run() {
        Ok(value) => emit(value),
        Err(error) => {
            emit(json!({"status":"REJECTED","reason":error.0,"physical_motion_authorized":false}));
            std::process::exit(2)
        }
    }
}
