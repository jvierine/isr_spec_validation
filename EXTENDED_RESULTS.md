# Additional comparisons

Same metric and 10⁻⁶ threshold as the README. Initial results are preserved; refined results change numerical resolution only.
Angles are measured from B. Parameters describe validation cases, not fitted observations.

## magnetic_42deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 42°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

**Initial numerical settings**

| Code | Kinetic | Swoboda | Vierinen |
|---|---:|---:|---:|
| Kinetic | — | 🟥 4.36e-06 | 🟥 1.14e-06 |
| Swoboda | 🟥 4.36e-06 | — | 🟥 4.13e-06 |
| Vierinen | 🟥 1.14e-06 | 🟥 4.13e-06 | — |

**Refined numerical settings**

| Code | Kinetic | Swoboda | Vierinen |
|---|---:|---:|---:|
| Kinetic | — | 🟩 7.20e-15 | 🟩 5.52e-15 |
| Swoboda | 🟩 7.20e-15 | — | 🟩 4.70e-15 |
| Vierinen | 🟩 5.52e-15 | 🟩 4.70e-15 | — |

Swoboda quadrature N = 800; last refinement changes the spectrum by 2.22e-11 of peak.

Vierinen: doubled time windows, 160,000 points; last point-count refinement changes the spectrum by 9.87e-16 of peak.

## magnetic_85deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 85°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

**Initial numerical settings**

| Code | Kinetic | Swoboda | Vierinen |
|---|---:|---:|---:|
| Kinetic | — | 🟥 5.52e-04 | 🟥 1.08e-06 |
| Swoboda | 🟥 5.52e-04 | — | 🟥 5.52e-04 |
| Vierinen | 🟥 1.08e-06 | 🟥 5.52e-04 | — |

**Refined numerical settings**

| Code | Kinetic | Swoboda | Vierinen |
|---|---:|---:|---:|
| Kinetic | — | 🟩 2.17e-14 | 🟩 1.59e-14 |
| Swoboda | 🟩 2.17e-14 | — | 🟩 1.25e-14 |
| Vierinen | 🟩 1.59e-14 | 🟩 1.25e-14 | — |

Swoboda quadrature N = 6400; last refinement changes the spectrum by 3.90e-11 of peak.

Vierinen: doubled time windows, 160,000 points; last point-count refinement changes the spectrum by 1.00e-15 of peak.

## neutral_bgk_42deg

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 42°; f_r = 430 MHz. νen = 10000 s⁻¹; νei = 0 s⁻¹; νin = 1000 s⁻¹.

**Initial numerical settings**

| Code | Kinetic | Swoboda |
|---|---:|---:|
| Kinetic | — | 🟥 3.49e-06 |
| Swoboda | 🟥 3.49e-06 | — |

**Refined numerical settings**

| Code | Kinetic | Swoboda |
|---|---:|---:|
| Kinetic | — | 🟩 5.41e-15 |
| Swoboda | 🟩 5.41e-15 | — |

Swoboda quadrature N = 800; last refinement changes the spectrum by 1.77e-11 of peak.

## neutral_bgk_parallel

ne = 1e+11 m⁻³; Te = 300 K; Ti = 300 K; vi = 0 m/s; B = 40 μT; angle(k,B) = 0°; f_r = 430 MHz. νen = 10000 s⁻¹; νei = 0 s⁻¹; νin = 1000 s⁻¹.

**Initial numerical settings**

| Code | Kinetic | Swoboda |
|---|---:|---:|
| Kinetic | — | 🟩 4.45e-10 |
| Swoboda | 🟩 4.45e-10 | — |

**Refined numerical settings**

| Code | Kinetic | Swoboda |
|---|---:|---:|
| Kinetic | — | 🟩 4.27e-15 |
| Swoboda | 🟩 4.27e-15 | — |

Swoboda quadrature N = 800; last refinement changes the spectrum by 4.62e-15 of peak.

## plasma_lines

ne = 1e+11 m⁻³; Te = 4000 K; Ti = 1000 K; vi = 0 m/s; B = 0 μT; angle(k,B) = 0°; f_r = 430 MHz. νen = 0 s⁻¹; νei = 0 s⁻¹; νin = 0 s⁻¹.

**Initial numerical settings**

| Code | Kinetic | Swoboda | Vierinen | Analytic |
|---|---:|---:|---:|---:|
| Kinetic | — | 🟩 2.58e-12 | 🟥 5.99e-06 | 🟩 2.56e-12 |
| Swoboda | 🟩 2.58e-12 | — | 🟥 5.99e-06 | 🟩 3.39e-14 |
| Vierinen | 🟥 5.99e-06 | 🟥 5.99e-06 | — | 🟥 5.99e-06 |
| Analytic | 🟩 2.56e-12 | 🟩 3.39e-14 | 🟥 5.99e-06 | — |

**Refined numerical settings**

| Code | Kinetic | Swoboda | Vierinen | Analytic |
|---|---:|---:|---:|---:|
| Kinetic | — | 🟩 2.58e-12 | 🟩 8.54e-09 | 🟩 2.56e-12 |
| Swoboda | 🟩 2.58e-12 | — | 🟩 8.55e-09 | 🟩 3.39e-14 |
| Vierinen | 🟩 8.54e-09 | 🟩 8.55e-09 | — | 🟩 8.55e-09 |
| Analytic | 🟩 2.56e-12 | 🟩 3.39e-14 | 🟩 8.55e-09 | — |

Swoboda quadrature N = 800; last refinement changes the spectrum by 0.00e+00 of peak.

Vierinen: doubled time windows, 160,000 points; last point-count refinement changes the spectrum by 1.02e-07 of peak.
