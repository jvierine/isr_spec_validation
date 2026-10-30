# Additional comparisons

🟩 pass (error ≤ 10⁻⁶); 🟥 fail. Same metric as the README, with no fitted scaling.
Click a code name to see its function call and numerical settings.
Angles are measured from B. Parameters describe validation cases, not fitted observations.

## magnetic_42deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 42°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

| Code | [Kinetic](invocations.py#L31) | [Swoboda](invocations.py#L32) | [Vierinen](invocations.py#L33) |
|---|---:|---:|---:|
| [Kinetic](invocations.py#L31) | — | 🟩 7.20e-15 | 🟩 5.52e-15 |
| [Swoboda](invocations.py#L32) | 🟩 7.20e-15 | — | 🟩 4.70e-15 |
| [Vierinen](invocations.py#L33) | 🟩 5.52e-15 | 🟩 4.70e-15 | — |

## magnetic_85deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 85°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

| Code | [Kinetic](invocations.py#L54) | [Swoboda](invocations.py#L55) | [Vierinen](invocations.py#L56) |
|---|---:|---:|---:|
| [Kinetic](invocations.py#L54) | — | 🟩 2.17e-14 | 🟩 1.59e-14 |
| [Swoboda](invocations.py#L55) | 🟩 2.17e-14 | — | 🟩 1.25e-14 |
| [Vierinen](invocations.py#L56) | 🟩 1.59e-14 | 🟩 1.25e-14 | — |

## neutral_bgk_42deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 42°; f_r = 430 MHz. νen = 10000 s⁻¹; νei = 0 s⁻¹; νin = 1000 s⁻¹.

| Code | [Kinetic](invocations.py#L79) | [Swoboda](invocations.py#L80) |
|---|---:|---:|
| [Kinetic](invocations.py#L79) | — | 🟩 5.41e-15 |
| [Swoboda](invocations.py#L80) | 🟩 5.41e-15 | — |

## neutral_bgk_parallel

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 0°; f_r = 430 MHz. νen = 10000 s⁻¹; νei = 0 s⁻¹; νin = 1000 s⁻¹.

| Code | [Kinetic](invocations.py#L103) | [Swoboda](invocations.py#L104) |
|---|---:|---:|
| [Kinetic](invocations.py#L103) | — | 🟩 4.27e-15 |
| [Swoboda](invocations.py#L104) | 🟩 4.27e-15 | — |

## plasma_lines

ne = 1e+11 m⁻³; Te = 4000 K; Ti = 1000 K; vi = 0 m/s; B = 0 μT; angle(k,B) = 0°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

| Code | [Kinetic](invocations.py#L125) | [Swoboda](invocations.py#L126) | [Vierinen](invocations.py#L127) | [Analytic](invocations.py#L128) |
|---|---:|---:|---:|---:|
| [Kinetic](invocations.py#L125) | — | 🟩 2.58e-12 | 🟩 8.54e-09 | 🟩 2.56e-12 |
| [Swoboda](invocations.py#L126) | 🟩 2.58e-12 | — | 🟩 8.55e-09 | 🟩 3.39e-14 |
| [Vierinen](invocations.py#L127) | 🟩 8.54e-09 | 🟩 8.55e-09 | — | 🟩 8.55e-09 |
| [Analytic](invocations.py#L128) | 🟩 2.56e-12 | 🟩 3.39e-14 | 🟩 8.55e-09 | — |
