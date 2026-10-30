# ISR spectrum validation

This is an effort to document and cross-validate different open source incoherent scatter radar spectrum calculation programs.

| Code | Source |
|---|---|
| Analytic | [This repository](calculate.py): Maxwellian Gordeyev integral |
| Vierinen | [Juha Vierinen, isr_analysis/isr_spec.py](https://github.com/jvierine/isr_analysis/blob/9c743981bc9e0340a219dfac4685509a38d7f93d/isr_spec.py) |
| Swoboda | [John Swoboda, ISRSpectrum](https://github.com/jswoboda/ISRSpectrum/tree/76265c6478aafa3f5bdb918dd44e6f6d2473a832) |
| Kinetic | [Snapshot of the Vlasov–Boltzmann project calculation](models/kinetic.py) |

**Pairwise agreement:** worst error across six collisionless, unmagnetized ion-line cases
(F region, molecular ions and topside; 440.2 and 930 MHz).

🟩 agrees (error ≤ 10⁻⁶); 🟥 disagrees. Error = maximum absolute difference
divided by the larger spectrum peak. No fitted scaling.

| Code | Analytic | Vierinen | Swoboda | Kinetic |
|---|---:|---:|---:|---:|
| Analytic | — | 🟩 9.58e-11 | 🟩 1.14e-15 | 🟩 1.80e-15 |
| Vierinen | 🟩 9.58e-11 | — | 🟩 9.58e-11 | 🟩 9.58e-11 |
| Swoboda | 🟩 1.14e-15 | 🟩 9.58e-11 | — | 🟩 1.80e-15 |
| Kinetic | 🟩 1.80e-15 | 🟩 9.58e-11 | 🟩 1.80e-15 | — |

[HDF5 tables](tables/comparison/) contain every code’s spectrum and comparison results.
Mass units, spectrum units and zero-frequency limits are matched explicitly;
[details and reproduction](DETAILS.md). Each table includes its code’s Git URL and full checkout commit.

Magnetic, collision and plasma-line checks: [pass/fail results](EXTENDED_RESULTS.md).

Other available calculators: [catalog of ISR spectrum software](OTHER_CODES.md),
including GitHub implementations and Zenodo/DataverseNO archives. Catalog entries
have not been added to the numerical comparisons.
