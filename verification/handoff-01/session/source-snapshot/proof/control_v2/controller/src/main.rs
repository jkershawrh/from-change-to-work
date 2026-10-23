use aeris_control_v2::{Plan, Request, dispatch_allowed, solve, validate};
use serde::Deserialize;
use std::io::{self, BufRead, Write};
use std::time::Instant;

#[derive(Deserialize)]
#[serde(
    tag = "type",
    content = "payload",
    rename_all = "snake_case",
    deny_unknown_fields
)]
enum Message {
    Plan(Request),
    Dispatch {
        sequence: u64,
        collision_clear: bool,
    },
}

fn main() {
    let mut last = None;
    let mut pending: Option<(Plan, Instant, f64)> = None;
    let mut out = io::BufWriter::new(io::stdout().lock());
    for line in io::stdin().lock().lines() {
        let response = match line {
            Ok(line) => match serde_json::from_str::<Message>(&line) {
                Ok(Message::Plan(request)) => {
                    pending = None;
                    match validate(&request, last) {
                        Ok(()) => {
                            last = Some(request.sequence);
                            let issued = Instant::now();
                            let plan = solve(&request);
                            let response = serde_json::to_string(&plan).unwrap();
                            if plan.status == "PLANNED" {
                                pending = Some((plan, issued, request.observation_age_ms));
                            }
                            if writeln!(out, "{response}")
                                .and_then(|_| out.flush())
                                .is_err()
                            {
                                break;
                            }
                            continue;
                        }
                        Err(e) => Plan::rejected(request.sequence, e, 0.),
                    }
                }
                Ok(Message::Dispatch {
                    sequence,
                    collision_clear,
                }) => match pending.take() {
                    Some((mut plan, issued, age)) if plan.sequence == sequence => {
                        match dispatch_allowed(
                            issued.elapsed().as_secs_f64() * 1000.,
                            age,
                            collision_clear,
                        ) {
                            Ok(()) => {
                                plan.status = "DISPATCHED";
                                plan.positions.clear();
                                plan.velocities.clear();
                                plan.accelerations.clear();
                                plan
                            }
                            Err(e) => Plan::rejected(sequence, e, plan.solve_ms),
                        }
                    }
                    _ => Plan::rejected(sequence, "NO_MATCHING_PENDING_PLAN", 0.),
                },
                Err(_) => {
                    pending = None;
                    Plan::rejected(0, "MALFORMED_REQUEST", 0.)
                }
            },
            Err(_) => break,
        };
        if writeln!(out, "{}", serde_json::to_string(&response).unwrap())
            .and_then(|_| out.flush())
            .is_err()
        {
            break;
        }
    }
}
