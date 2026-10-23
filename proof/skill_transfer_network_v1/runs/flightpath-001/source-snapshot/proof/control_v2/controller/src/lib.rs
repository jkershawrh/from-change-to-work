//! Simulation research controller. No physical-robot interface or safety certification.
//! Six separable constrained double-integrator QPs; collisions are a separate gate.
use clarabel::{algebra::CscMatrix, solver::*};
use serde::{Deserialize, Serialize};
use std::time::Instant;

pub const N: usize = 20;
pub const DT: f64 = 0.02;
// Heuristic tightening validated empirically; no invariant-set guarantee.
pub const PHYSICAL_VMAX: f64 = 0.45;
pub const PHYSICAL_AMAX: f64 = 1.2;
pub const VMAX: f64 = 0.40;
pub const AMAX: f64 = 0.85;
pub const DEADLINE_MS: f64 = 20.0;
// Literal home coordinates match the pinned MJCF keyframe, rather than rounded pi/2.
#[allow(clippy::approx_constant)]
pub const HOME: [f64; 6] = [-1.5708, -1.5708, 1.5708, -1.5708, -1.5708, 0.0];
pub const RADIUS: f64 = 0.63;
pub const PHYSICAL_RADIUS: f64 = 0.65;
const _: () = assert!(VMAX < PHYSICAL_VMAX && AMAX < PHYSICAL_AMAX && RADIUS < PHYSICAL_RADIUS);

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub sequence: u64,
    pub observation_age_ms: f64,
    pub q: [f64; 6],
    pub velocity: [f64; 6],
    pub target: [f64; 6],
}

#[derive(Debug, Serialize)]
pub struct Plan {
    pub sequence: u64,
    pub status: &'static str,
    pub reason: Option<String>,
    pub acceleration: Option<[f64; 6]>,
    pub positions: Vec<[f64; 6]>,
    pub velocities: Vec<[f64; 6]>,
    pub accelerations: Vec<[f64; 6]>,
    pub solve_ms: f64,
    pub max_primal_residual: f64,
    pub horizon_seconds: f64,
}

impl Plan {
    pub fn rejected(sequence: u64, reason: impl Into<String>, ms: f64) -> Self {
        Self {
            sequence,
            status: "REJECTED",
            reason: Some(reason.into()),
            acceleration: None,
            positions: vec![],
            velocities: vec![],
            accelerations: vec![],
            solve_ms: ms,
            max_primal_residual: 0.,
            horizon_seconds: N as f64 * DT,
        }
    }
}

pub fn validate(r: &Request, last_sequence: Option<u64>) -> Result<(), &'static str> {
    if !r.observation_age_ms.is_finite()
        || r.q
            .iter()
            .chain(&r.velocity)
            .chain(&r.target)
            .any(|x| !x.is_finite())
    {
        return Err("NONFINITE_INPUT");
    }
    if r.observation_age_ms < 0. || r.observation_age_ms > 40. {
        return Err("STALE_OBSERVATION");
    }
    if last_sequence.is_some_and(|last| r.sequence <= last) {
        return Err("REPLAYED_SEQUENCE");
    }
    for (j, home) in HOME.iter().enumerate() {
        if (r.target[j] - home).abs() > RADIUS {
            return Err("TARGET_OUTSIDE_RECIPE");
        }
        if (r.q[j] - home).abs() > RADIUS + 1e-7 || r.velocity[j].abs() > PHYSICAL_VMAX + 1e-7 {
            return Err("STATE_OUTSIDE_ENVELOPE");
        }
    }
    Ok(())
}

pub fn dispatch_allowed(
    solve_age_ms: f64,
    observation_age_ms: f64,
    collision_clear: bool,
) -> Result<(), &'static str> {
    if !solve_age_ms.is_finite() || !(0. ..DEADLINE_MS).contains(&solve_age_ms) {
        return Err("DEADLINE_EXPIRED");
    }
    if !observation_age_ms.is_finite()
        || observation_age_ms < 0.
        || observation_age_ms + solve_age_ms > 40.
    {
        return Err("STALE_AT_DISPATCH");
    }
    if !collision_clear {
        return Err("COLLISION_GATE");
    }
    Ok(())
}

fn csc(rows: &[Vec<f64>], upper: bool) -> CscMatrix<f64> {
    let m = rows.len();
    let n = rows[0].len();
    let mut colptr = vec![0];
    let mut rowval = vec![];
    let mut nzval = vec![];
    for c in 0..n {
        for (r, row) in rows.iter().enumerate().take(m) {
            if (!upper || r <= c) && row[c].abs() > 1e-14 {
                rowval.push(r);
                nzval.push(row[c]);
            }
        }
        colptr.push(nzval.len());
    }
    CscMatrix::new(m, n, colptr, rowval, nzval)
}

pub fn solve(r: &Request) -> Plan {
    solve_core(r, true)
}

fn solve_core(r: &Request, enforce_deadline: bool) -> Plan {
    let start = Instant::now();
    if let Err(e) = validate(r, None) {
        return Plan::rejected(r.sequence, e, 0.);
    }
    let mut positions = vec![[0.; 6]; N];
    let mut velocities = vec![[0.; 6]; N];
    let mut accelerations = vec![[0.; 6]; N];
    let mut max_residual: f64 = 0.;
    for (joint, home) in HOME.iter().enumerate() {
        let mut p = vec![vec![0.; N]; N];
        let mut linear = vec![0.; N];
        let mut a = vec![];
        let mut b = vec![];
        for k in 0..N {
            let coeff: Vec<_> = (0..N)
                .map(|j| {
                    if j <= k {
                        (k - j) as f64 * DT * DT + 0.5 * DT * DT
                    } else {
                        0.
                    }
                })
                .collect();
            let vel: Vec<_> = (0..N).map(|j| if j <= k { DT } else { 0. }).collect();
            let offset = r.q[joint] + (k + 1) as f64 * DT * r.velocity[joint];
            let weight = if k == N - 1 { 600. } else { 60. };
            let velocity_weight = if k == N - 1 { 8. } else { 0.3 };
            for i in 0..N {
                linear[i] += 2. * weight * (offset - r.target[joint]) * coeff[i]
                    + 2. * velocity_weight * r.velocity[joint] * vel[i];
                for j in 0..N {
                    p[i][j] +=
                        2. * weight * coeff[i] * coeff[j] + 2. * velocity_weight * vel[i] * vel[j];
                }
            }
            p[k][k] += 0.03;
            // A u <= b, with nonnegative cone slack. Acceleration, position and velocity bounds.
            for sign in [1., -1.] {
                let mut row = vec![0.; N];
                row[k] = sign;
                a.push(row);
                b.push(AMAX);
                a.push(vel.iter().map(|v| v * sign).collect());
                b.push(VMAX - sign * r.velocity[joint]);
                a.push(coeff.iter().map(|v| v * sign).collect());
                b.push(RADIUS + sign * (home - offset));
            }
        }
        let settings = DefaultSettings {
            verbose: false,
            max_iter: 75,
            time_limit: if enforce_deadline {
                0.01
            } else {
                f64::INFINITY
            },
            tol_feas: 1e-8,
            tol_gap_abs: 1e-8,
            tol_gap_rel: 1e-8,
            ..DefaultSettings::default()
        };
        let mut solver = match DefaultSolver::new(
            &csc(&p, true),
            &linear,
            &csc(&a, false),
            &b,
            &[NonnegativeConeT(b.len())],
            settings,
        ) {
            Ok(s) => s,
            Err(_) => {
                return Plan::rejected(
                    r.sequence,
                    "SOLVER_SETUP",
                    start.elapsed().as_secs_f64() * 1000.,
                );
            }
        };
        solver.solve();
        if solver.solution.status != SolverStatus::Solved {
            return Plan::rejected(
                r.sequence,
                format!("SOLVER_{:?}", solver.solution.status),
                start.elapsed().as_secs_f64() * 1000.,
            );
        }
        max_residual = max_residual.max(solver.solution.r_prim);
        let mut q = r.q[joint];
        let mut v = r.velocity[joint];
        for k in 0..N {
            let u = solver.solution.x[k];
            q += DT * v + 0.5 * DT * DT * u;
            v += DT * u;
            if !q.is_finite()
                || !v.is_finite()
                || !u.is_finite()
                || u.abs() > AMAX + 1e-6
                || v.abs() > VMAX + 1e-6
                || (q - home).abs() > RADIUS + 1e-6
            {
                return Plan::rejected(
                    r.sequence,
                    "INDEPENDENT_BOUND_CHECK",
                    start.elapsed().as_secs_f64() * 1000.,
                );
            }
            positions[k][joint] = q;
            velocities[k][joint] = v;
            accelerations[k][joint] = u;
        }
    }
    let ms = start.elapsed().as_secs_f64() * 1000.;
    // This is a plan, not dispatch authority. The caller must recheck age and collision clearance.
    if enforce_deadline {
        if let Err(e) = dispatch_allowed(ms, r.observation_age_ms, true) {
            return Plan::rejected(r.sequence, e, ms);
        }
    }
    Plan {
        sequence: r.sequence,
        status: "PLANNED",
        reason: None,
        acceleration: Some(accelerations[0]),
        positions,
        velocities,
        accelerations,
        solve_ms: ms,
        max_primal_residual: max_residual,
        horizon_seconds: N as f64 * DT,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn request() -> Request {
        Request {
            sequence: 1,
            observation_age_ms: 0.,
            q: HOME,
            velocity: [0.; 6],
            target: HOME,
        }
    }
    #[test]
    fn stale_and_replay_are_rejected() {
        let mut r = request();
        r.observation_age_ms = 41.;
        assert_eq!(validate(&r, None), Err("STALE_OBSERVATION"));
        r.observation_age_ms = 0.;
        assert_eq!(validate(&r, Some(1)), Err("REPLAYED_SEQUENCE"));
    }
    #[test]
    fn nonfinite_and_outside_recipe_rejected() {
        let mut r = request();
        r.q[0] = f64::NAN;
        assert_eq!(validate(&r, None), Err("NONFINITE_INPUT"));
        r.q = HOME;
        r.target[2] += 2.;
        assert_eq!(validate(&r, None), Err("TARGET_OUTSIDE_RECIPE"));
    }
    #[test]
    fn dispatch_requires_fresh_timely_collision_checked_plan() {
        assert!(dispatch_allowed(1., 0., true).is_ok());
        assert!(dispatch_allowed(20., 0., true).is_err());
        assert!(dispatch_allowed(15., 30., true).is_err());
        assert!(dispatch_allowed(1., 0., false).is_err());
        assert!(dispatch_allowed(f64::NAN, 0., true).is_err());
    }
    // Numerical tests are independent of debug build speed; deadline logic has its own tests,
    // and release timing is measured against the external plant with the production deadline.
    #[test]
    fn planner_reserves_real_constraint_margin() {
        let mut r = request();
        r.velocity[0] = PHYSICAL_VMAX + 0.00001;
        assert_eq!(validate(&r, None), Err("STATE_OUTSIDE_ENVELOPE"));
    }
    #[test]
    fn mixed_direction_moving_state_respects_tightened_predictions() {
        let mut r = request();
        for j in 0..6 {
            let sign = if j % 2 == 0 { 1. } else { -1. };
            r.target[j] += sign * 0.35;
            r.velocity[j] = sign * 0.18;
        }
        let p = solve_core(&r, false);
        assert_eq!(p.status, "PLANNED");
        let mut q = r.q;
        let mut v = r.velocity;
        for k in 0..N {
            for j in 0..6 {
                let u = p.accelerations[k][j];
                q[j] += DT * v[j] + 0.5 * DT * DT * u;
                v[j] += DT * u;
                assert!((q[j] - p.positions[k][j]).abs() < 1e-10);
                assert!((v[j] - p.velocities[k][j]).abs() < 1e-10);
                assert!(v[j].abs() <= VMAX + 1e-6 && u.abs() <= AMAX + 1e-6);
            }
        }
    }
    #[test]
    fn equilibrium_has_zero_control() {
        let p = solve_core(&request(), false);
        assert_eq!(p.status, "PLANNED");
        assert!(p.acceleration.unwrap().iter().all(|u| u.abs() < 1e-6));
    }
    #[test]
    fn horizon_moves_to_target_without_breaking_bounds() {
        let mut r = request();
        r.target[0] += 0.4;
        let p = solve_core(&r, false);
        assert_eq!(p.status, "PLANNED");
        assert!(p.positions[N - 1][0] > HOME[0]);
        for k in 0..N {
            assert!(p.velocities[k][0].abs() <= VMAX + 1e-6);
            assert!(p.accelerations[k][0].abs() <= AMAX + 1e-6);
        }
    }
    #[test]
    fn infeasible_braking_state_is_not_dispatched() {
        let mut r = request();
        r.q[0] += RADIUS - 0.001;
        r.velocity[0] = VMAX;
        let p = solve_core(&r, false);
        assert_eq!(p.status, "REJECTED");
        assert!(p.acceleration.is_none());
        assert!(p.reason.unwrap().contains("PrimalInfeasible"));
    }
}
