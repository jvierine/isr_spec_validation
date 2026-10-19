# ISR spectrum validation

Reference tables for checking ISR spectrum calculations. The starting cases use
collisionless Maxwellian plasmas with zero magnetic field and zero bulk velocity.
The compositions and temperatures below define the tests; they are representative
examples, not an atmospheric model.

Each case is calculated at **440.2 MHz** and **930 MHz**.

| Case | Ion number fractions | ne / m⁻³ | Ti / K | Te / K |
|---|---|---:|---:|---:|
| F region | O⁺: 1.0 | 1e11 | 1000 | 2000 |
| Molecular | O₂⁺: 0.5, NO⁺: 0.3, N₂⁺: 0.2 | 1e11 | 500 | 500 |
| Topside | O⁺: 0.5, H⁺: 0.5 | 5e10 | 1500 | 3000 |

Ion masses are 16, 32, 30, 28 and 1 atomic mass units, respectively. All species
are singly charged. Ion densities sum to the electron density.

[Tables](tables/) are supplied as plain text and HDF5. Columns are frequency
in Hz, ion contribution, electron contribution and their sum. Spectra are
**per electron per Hz**, with both frequency signs retained. Multiply by ne
for the electron-density fluctuation spectrum. There is no peak or area
normalization. The finite frequency interval does not include the plasma-line
peaks and must not be used as a total-spectrum sum rule.

The frequency grid is −100000 to +100000 Hz in 250 Hz steps. The text tables
carry the same parameters as the HDF5 attributes.

## Calculation

The calculation uses the Maxwellian Gordeyev integral and the multispecies
dielectric response in Kudeki and Milla (2011), Part I:

- (G_s = \int_0^\infty \exp[-k^2 k_B T_s t^2/(2m_s)]\exp(-i\omega t)\,dt\).
- (\chi_s = [n_s q_s^2/(\epsilon_0 k_B T_s k^2)](1-i\omega G_s)\).
- (\epsilon = 1 + \chi_e + \sum_i\chi_i\), with (k=4\pi f_0/c\).
- (S_{ion}=|\chi_e/\epsilon|^2\sum_i(n_i/n_e)2\operatorname{Re}G_i\).
- (S_{electron}=|(1+\sum_i\chi_i)/\epsilon|^2 2\operatorname{Re}G_e\).

The integral is evaluated analytically using Dawson's integral. The script is
short enough to check directly against these equations.

```sh
conda run -n base python calculate.py
```

Requires NumPy, SciPy and h5py. To check another implementation, evaluate it at
the listed parameters and compare its unnormalized spectrum with `S_total`.
Check the separate contributions if its output distinguishes them. A suggested
initial tolerance is `max(abs(test-reference)) / max(reference) < 1e-6`.

## Reference

E. Kudeki and M. A. Milla (2011), “Incoherent Scatter Spectral Theories—Part I:
A General Framework and Results for Small Magnetic Aspect Angles,”
*IEEE Transactions on Geoscience and Remote Sensing*, 49, 315–328.
[doi:10.1109/TGRS.2010.2057252](https://doi.org/10.1109/TGRS.2010.2057252).
