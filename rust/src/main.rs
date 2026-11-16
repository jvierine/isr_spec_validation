// Native RUISDAP Rust spectrum evaluation and warmed in-process benchmark.
// All parsing and serialized output occur outside the timed interval.
use anyhow::{ensure, Result};
use guisdap_ion::spectrum::{IonSpecies, PlasmaState, SpectrumModel};
pub use num_complex::Complex64 as Complex;
use serde::{Deserialize, Serialize};
use std::{hint::black_box, io::Read, time::Instant};
// Exact pre-optimization Rust module at ruisdap commit 7bf2c45. It is used
// only to measure paired Rust before/after performance and numerical change.
#[allow(dead_code)]
mod baseline;
mod precision_trial;

#[derive(Deserialize)]
struct Request {
    radar_hz: f64,
    ne: f64,
    te: f64,
    ti: f64,
    ions: Vec<(String, f64, f64)>,
    #[serde(default)]
    nu_e: f64,
    #[serde(default)]
    nu_i: f64,
    #[serde(default)]
    velocity_m_s: f64,
    #[serde(default)]
    b: f64,
    frequency_hz: Vec<f64>,
    #[serde(default = "trials")]
    trials: usize,
    #[serde(default = "batch")]
    batch: usize,
}
fn trials() -> usize {
    31
}
fn batch() -> usize {
    100
}
#[derive(Serialize)]
struct Output {
    spectrum: Vec<f64>,
    elapsed_s: Vec<f64>,
    batch_size: usize,
    baseline_elapsed_s: Vec<f64>,
    max_relative_change: f64,
    float32_spectrum: Option<Vec<f64>>,
    float32_elapsed_s: Vec<f64>,
    cpu_elapsed_s: Vec<f64>,
    baseline_cpu_elapsed_s: Vec<f64>,
    backend: &'static str,
}

fn cpu_seconds() -> Result<f64> {
    let mut t = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    // t points to one writable timespec and the call retains no pointer.
    ensure!(
        unsafe { libc::clock_gettime(libc::CLOCK_THREAD_CPUTIME_ID, &mut t) } == 0,
        "thread CPU clock unavailable"
    );
    Ok(t.tv_sec as f64 + t.tv_nsec as f64 * 1e-9)
}

fn main() -> Result<()> {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input)?;
    let q: Request = serde_json::from_str(&input)?;
    ensure!(q.b == 0., "Rust model supports B=0 only");
    ensure!(q.trials > 0 && q.batch > 0, "empty benchmark");
    let model = SpectrumModel {
        radar_frequency_hz: q.radar_hz,
        ions: q
            .ions
            .iter()
            .map(|(_, mass, fraction)| IonSpecies {
                mass_amu: *mass,
                fraction: *fraction,
            })
            .collect(),
        electron_collision_s: q.nu_e,
    };
    let state = PlasmaState {
        electron_density_m3: q.ne,
        ion_temperature_k: q.ti,
        electron_temperature_k: q.te,
        velocity_m_s: q.velocity_m_s,
        ion_collision_s: q.nu_i,
    };
    let spectrum = model.evaluate(state, &q.frequency_hz)?;
    let previous = baseline::SpectrumModel {
        radar_frequency_hz: q.radar_hz,
        ions: q
            .ions
            .iter()
            .map(|(_, mass, fraction)| baseline::IonSpecies {
                mass_amu: *mass,
                fraction: *fraction,
            })
            .collect(),
        electron_collision_s: q.nu_e,
    };
    let prior_state = baseline::PlasmaState {
        electron_density_m3: q.ne,
        ion_temperature_k: q.ti,
        electron_temperature_k: q.te,
        velocity_m_s: q.velocity_m_s,
        ion_collision_s: q.nu_i,
    };
    let prior = previous.evaluate(prior_state, &q.frequency_hz)?;
    let peak = prior.iter().copied().fold(0_f64, f64::max);
    let max_relative_change = spectrum
        .iter()
        .zip(&prior)
        .map(|(a, b)| (a - b).abs())
        .fold(0_f64, f64::max)
        / peak;
    ensure!(
        max_relative_change <= 1e-9,
        "Rust optimization changed spectrum: {max_relative_change}"
    );
    for _ in 0..10 {
        black_box(model.evaluate(black_box(state), black_box(&q.frequency_hz))?);
    }
    for _ in 0..10 {
        black_box(previous.evaluate(black_box(prior_state), black_box(&q.frequency_hz))?);
    }
    let mut elapsed_s = Vec::with_capacity(q.trials);
    let mut baseline_elapsed_s = Vec::with_capacity(q.trials);
    let mut cpu_elapsed_s = Vec::with_capacity(q.trials);
    let mut baseline_cpu_elapsed_s = Vec::with_capacity(q.trials);
    let float32_spectrum = if q.nu_e == 0. && q.nu_i == 0. {
        Some(precision_trial::evaluate(&q))
    } else {
        None
    };
    let mut float32_elapsed_s = Vec::new();
    if float32_spectrum.is_some() {
        for _ in 0..10 {
            black_box(precision_trial::evaluate(black_box(&q)));
        }
    }
    for trial in 0..q.trials {
        // Alternate order to reduce clock/load drift between the two kernels.
        for mode in if trial % 2 == 0 { [0, 1, 2] } else { [2, 1, 0] } {
            if mode == 2 && float32_spectrum.is_none() {
                continue;
            }
            let start = Instant::now();
            let cpu_start = cpu_seconds()?;
            for _ in 0..q.batch {
                if mode == 1 {
                    black_box(model.evaluate(black_box(state), black_box(&q.frequency_hz))?);
                } else if mode == 0 {
                    black_box(
                        previous.evaluate(black_box(prior_state), black_box(&q.frequency_hz))?,
                    );
                } else {
                    black_box(precision_trial::evaluate(black_box(&q)));
                }
            }
            let elapsed = start.elapsed().as_secs_f64() / q.batch as f64;
            let cpu = (cpu_seconds()? - cpu_start) / q.batch as f64;
            if mode == 1 {
                elapsed_s.push(elapsed);
                cpu_elapsed_s.push(cpu);
            } else if mode == 0 {
                baseline_elapsed_s.push(elapsed);
                baseline_cpu_elapsed_s.push(cpu);
            } else {
                float32_elapsed_s.push(elapsed);
            }
        }
    }
    #[cfg(not(target_arch = "x86_64"))]
    let backend = "scalar";
    #[cfg(target_arch = "x86_64")]
    let backend = if q.ions.len() == 1
        && q.nu_e == 0.
        && q.nu_i == 0.
        && q.frequency_hz.len() >= 4
        && std::is_x86_feature_detected!("avx2")
    {
        "AVX2"
    } else {
        "scalar"
    };
    serde_json::to_writer(
        std::io::stdout(),
        &Output {
            spectrum,
            elapsed_s,
            baseline_elapsed_s,
            max_relative_change,
            batch_size: q.batch,
            float32_spectrum,
            float32_elapsed_s,
            cpu_elapsed_s,
            baseline_cpu_elapsed_s,
            backend,
        },
    )?;
    Ok(())
}
