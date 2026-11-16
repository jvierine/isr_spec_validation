// Experimental mixed-precision arithmetic: f32 widths, Gaussian, and spectrum
// algebra; scaled Dawson uses the existing f64 special function then rounds
// to f32. This is measured for accuracy and speed, not used by the model.
use errorfunctions::RealErrorFunctions;

pub fn evaluate(q: &super::Request) -> Vec<f64> {
    let pi = std::f32::consts::PI;
    let kb = 1.380649e-23_f32;
    let k = 4. * pi * q.radar_hz as f32 / 299792458.;
    // Calculate the Debye prefactor in f64 once: e^2 is subnormal in f32.
    let alpha = (q.ne * 1.602176634e-19_f64.powi(2)
        / (8.8541878188e-12 * 1.380649e-23 * (k as f64).powi(2))) as f32;
    let te = q.te as f32;
    let ti = q.ti as f32;
    let ewidth = k * (2. * kb * te / 9.1093837139e-31_f32).sqrt();
    let ions: Vec<_> = q
        .ions
        .iter()
        .map(|(_, m, f)| {
            (
                k * (2. * kb * ti / (*m as f32 * 1.66053906892e-27_f32)).sqrt(),
                *f as f32,
            )
        })
        .collect();
    q.frequency_hz
        .iter()
        .map(|f| {
            let omega = 2. * pi * (*f as f32) - k * q.velocity_m_s as f32;
            let response = |width: f32, scale: f32| {
                let x = omega / width;
                let gaussian = (-x * x).exp();
                let ar = 1. - pi.sqrt() * x * (x as f64).w_im() as f32;
                let ai = pi.sqrt() * x * gaussian;
                (ar * scale, ai * scale, 2. * pi.sqrt() / width * gaussian)
            };
            let (er, ei, fe) = response(ewidth, alpha / te);
            let (mut ir, mut ii, mut fi) = (0_f32, 0_f32, 0_f32);
            for (width, fraction) in &ions {
                let (a, b, free) = response(*width, alpha * fraction / ti);
                ir += a;
                ii += b;
                fi += fraction * free;
            }
            let numerator = ((1. + ir).powi(2) + ii * ii) * fe + (er * er + ei * ei) * fi;
            (numerator / ((1. + er + ir).powi(2) + (ei + ii).powi(2))) as f64
        })
        .collect()
}
