# ISR spectrum validation

Nine implementations evaluated across eleven prescribed Maxwellian tests. Each test has a spectrum overlay and a residual panel. Martinez and Sandbem are listed but were not run after MATLAB license failures; Virtanen uses the working R/C implementation.

[Six ion-line tests and plots](COMPARISON_RESULTS.md) · [Five magnetic, collision and plasma-line tests and plots](EXTENDED_RESULTS.md)

## Coverage and measured agreement

The threshold is 10⁻⁶. Errors use `max(abs(A-B))/max(max(abs(A)),max(abs(B)))`, with fixed physical unit conversions and no fitted scaling. Kinetic is the plotting reference, not an assertion of ground truth. Results apply only to the cases and frequency samples evaluated.

| Code | Cases evaluated | Worst difference from Kinetic | Worst case |
|---|---:|---:|---|
| Analytic | 7/11 | 🟩 2.56e-12 | Electron plasma lines |
| Vierinen | 9/11 | 🟩 8.54e-09 | Electron plasma lines |
| Swoboda | 11/11 | 🟩 2.58e-12 | Electron plasma lines |
| Kinetic | 11/11 | reference | F region, 440.2 MHz |
| Buchert | 9/11 | 🟥 1.31e-03 | Magnetic field, 85° from B |
| Virtanen | 8/11 | 🟥 4.39e-04 | Topside, 440.2 MHz |
| Nicolls | 11/11 | 🟥 3.41e-04 | Electron plasma lines |
| Skolar | 7/11 | 🟩 1.33e-11 | Magnetic field, 42° from B |
| inscar | 5/11 | 🟥 1.93e-01 | Electron plasma lines |
| Martinez | 0/11 | not run | MATLAB execution cancelled |
| Sandbem (ISRTS) | 0/11 | not run | MATLAB execution cancelled |

**Convergence limitation:** inscar’s plasma-line spectrum changes by more than 10⁻⁶ between its recorded settings. Its plotted discrepancy is provisional. Native constants, approximations and floating-point precision differ among codes; these were retained rather than tuned to obtain agreement.

## Baseline pairwise agreement

Worst error over the six unmagnetized ion-line tests. Each cell includes the number of shared cases; Skolar and inscar support the two single-ion cases in this adapter.

| Code | Analytic | Vierinen | Swoboda | Kinetic | Buchert | Virtanen | Nicolls | Skolar | inscar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Analytic | — | 🟩 9.58e-11 (6) | 🟩 1.14e-15 (6) | 🟩 1.80e-15 (6) | 🟩 2.23e-09 (6) | 🟥 4.39e-04 (6) | 🟩 1.55e-07 (6) | 🟩 7.97e-12 (2) | 🟥 3.74e-04 (2) |
| Vierinen | 🟩 9.58e-11 (6) | — | 🟩 9.58e-11 (6) | 🟩 9.58e-11 (6) | 🟩 2.23e-09 (6) | 🟥 4.39e-04 (6) | 🟩 1.55e-07 (6) | 🟩 7.97e-12 (2) | 🟥 3.74e-04 (2) |
| Swoboda | 🟩 1.14e-15 (6) | 🟩 9.58e-11 (6) | — | 🟩 1.80e-15 (6) | 🟩 2.23e-09 (6) | 🟥 4.39e-04 (6) | 🟩 1.55e-07 (6) | 🟩 7.97e-12 (2) | 🟥 3.74e-04 (2) |
| Kinetic | 🟩 1.80e-15 (6) | 🟩 9.58e-11 (6) | 🟩 1.80e-15 (6) | — | 🟩 2.23e-09 (6) | 🟥 4.39e-04 (6) | 🟩 1.55e-07 (6) | 🟩 7.97e-12 (2) | 🟥 3.74e-04 (2) |
| Buchert | 🟩 2.23e-09 (6) | 🟩 2.23e-09 (6) | 🟩 2.23e-09 (6) | 🟩 2.23e-09 (6) | — | 🟥 4.39e-04 (6) | 🟩 1.52e-07 (6) | 🟩 2.23e-09 (2) | 🟥 3.74e-04 (2) |
| Virtanen | 🟥 4.39e-04 (6) | 🟥 4.39e-04 (6) | 🟥 4.39e-04 (6) | 🟥 4.39e-04 (6) | 🟥 4.39e-04 (6) | — | 🟥 4.39e-04 (6) | 🟥 1.46e-05 (2) | 🟥 3.70e-04 (2) |
| Nicolls | 🟩 1.55e-07 (6) | 🟩 1.55e-07 (6) | 🟩 1.55e-07 (6) | 🟩 1.55e-07 (6) | 🟩 1.52e-07 (6) | 🟥 4.39e-04 (6) | — | 🟩 1.55e-07 (2) | 🟥 3.74e-04 (2) |
| Skolar | 🟩 7.97e-12 (2) | 🟩 7.97e-12 (2) | 🟩 7.97e-12 (2) | 🟩 7.97e-12 (2) | 🟩 2.23e-09 (2) | 🟥 1.46e-05 (2) | 🟩 1.55e-07 (2) | — | 🟥 3.74e-04 (2) |
| inscar | 🟥 3.74e-04 (2) | 🟥 3.74e-04 (2) | 🟥 3.74e-04 (2) | 🟥 3.74e-04 (2) | 🟥 3.74e-04 (2) | 🟥 3.70e-04 (2) | 🟥 3.74e-04 (2) | 🟥 3.74e-04 (2) | — |

[HDF5 arrays and pairwise matrices](tables/expanded/) retain the original grids and plasma parameters. The [original four-code data](tables/comparison/) and [original extended data](tables/extended/) remain available, including their earlier refinement checks.

[Reproduce the expanded runs and figures](NEW_CODES.md) · [Original methods](METHODS.md) · [Original four-code adapters](DETAILS.md) · [Catalog and archives](OTHER_CODES.md)
