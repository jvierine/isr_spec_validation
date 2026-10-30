# Expanded comparisons and reproduction

The inscar tests now use the pinned commit from [PR #537](https://github.com/engeir/inscar/pull/537),
with corrected SI permittivity and Simpson integration. The [accuracy study](INSCAR_ACCURACY.md)
retains the earlier upstream results and separates numerical resolution from
the permittivity effect. The PR is identified explicitly rather than treated as a released version.

Buchert, Virtanen, Nicolls, Skolar and inscar were evaluated using their native
Julia, R/C or Python implementations. Martinez and Sandbem (the ISRTS account,
interpreted from “sandberry”) are explicit **not run** entries. MATLAB execution
was cancelled after the installations checked on Revontuli failed licensing.
No MATLAB output is included or replaced by a translation.

The six existing unmagnetized ion-line cases and five existing extended cases
are reused without changing plasma parameters, mass definitions or frequency
samples. Original four-code arrays are copied exactly, selecting the configured
`refined` group for extended tests. New programs contribute total spectra;
their ion/electron components are not fabricated. All data products are HDF5.

## Implementations and scope

| Label | Pinned implementation | Cases evaluated | Exclusions in these adapters |
|---|---|---:|---|
| Buchert | [IncoherentScatter.jl](https://github.com/stephancb/IncoherentScatter.jl/tree/640110f6f7f2b3652498f18028ed4b8c9e03daeb) | 9 | No electron-neutral BGK input in the interface used here. |
| Virtanen | [ISspectrum R/C](https://github.com/ilkkavir/ISspectrum/tree/28458b2cefcce247e010a0f2555a934a051927a4) | 8 | No oblique magnetic response; a parallel Maxwellian response equals the unmagnetized response. |
| Nicolls | [ISR-school ISspec](https://github.com/isrsummerschool/lecture_supplements_2024/tree/5f02f3edaf09cc5b3f03617f50e9412ec12df4bd/is_spectral_model) | 11 | Coulomb collisions disabled, consistent with these tests. |
| Skolar | [crskolar/OO_Collisions](https://github.com/crskolar/OO_Collisions/tree/e3e212f6c31d364c2bd48f01b3ebafdf9769f533) | 7 | Native `calcSpectra` combines one ion species with electrons. Mixtures are omitted. |
| inscar | [PR #537 commit](https://github.com/jvierine/inscar/tree/532412a280a7e3373595fbaff763bcf12471622e) | 5 | One ion species; the inspected collision formula is not the number-conserving neutral BGK operator used here. |
| Martinez | [ISR_Model](https://github.com/miguel-martinez-ledesma/ISR_Model/tree/369e277c7d388b7b3e4c63d5402b31304ef954ef) | 0 | Not run: MATLAB execution cancelled. |
| Sandbem | [ISRTS](https://github.com/Sandbem/ISRTS/tree/d31ddafa87be19c957bb1949dcddc29a2f518432) | 0 | Not run: MATLAB execution cancelled. |

Coverage means successful evaluation, **not agreement**. Unsupported cases are
recorded separately from not-run programs. These restrictions describe the
invoked interfaces and matched physics, not every possible use of a package.
Shared ancestry also means these are not nine independent theoretical derivations.

## Units, limits and numerical settings

Every output is a PSD per electron per Hz. The conversions below are fixed
before comparison; no peak, area, amplitude or frequency is fitted. Source
checkouts exactly match the listed commits. Compatibility changes are confined to adapters.

**Buchert.** Invoke native `ScatterVolume`, `Ion`, `Plasma` and `pwrspec` with
`system=1/pi`, then divide by ne. This removes the native system factor and
matches the per-electron PSD. Use the dedicated DC expression at zero frequency.
For B=0 and parallel geometry, set the constructor's indeterminate perpendicular
factor to its exact zero limit. Ion fractions and amu masses are passed directly.
The implementation uses unmagnetized ion admittance and an approximate
magnetized electron response; oblique-field discrepancies are not a comparison
of identical equations. No adjustable quadrature refinement is claimed.

**Virtanen.** Run `ISspectrum.general` in R with its unchanged native C kernel
and plasma-dispersion interpolation table. Ion densities are ne times the
fractions; scattering angle is 180°. Multiply the native cross-section spectral
density by `2*pi/(9.978688e-29*ne)` to obtain a PSD per Hz per electron: the
cross-section factor and angular-frequency normalization are explicit in the
R wrapper. Its older physical constants and native interpolation are retained.
No interpolation-table refinement was performed, so differences cannot be
attributed solely to physics. The original C files are compiled without the
upstream x86-only flags on Apple Silicon; the C equations are unchanged.

**Nicolls.** Invoke `ISspec.computeSpec`, divide by ne, pass angles from B and
enable magnetic/neutral effects as applicable. Supply the exact Gaussian
integrand limit at zero field, where the original expression has a removable
0/0. Evaluate the same native Sommerfeld integrator in batches of 32 frequencies
to bound memory and require its success flag. Fine settings
`(tol,Nmax,maxLoops,Nstart,kmax)` are `(1e-20,262144,100,256,32)`; coarse settings
are `(1e-16,262144,100,128,16)`. For plasma lines, evaluate a full uniform grid
and select the exact requested samples. Disable the unneeded ACF calculation.
Native complex64 ion-response arrays are retained; quadrature refinement alone
does not establish freedom from floating-point error.
The plasma-line result also has a small numerical asymmetry, quantified in
the case table. Spectra are never symmetrized to conceal this error.

**Skolar.** Invoke the upstream Maxwellian harmonic formulas `calcU_Maxwellian`,
`calcM_Maxwellian`, `calcChi_Maxwellian`, then `calcSpectra`. Masses are kg,
frequencies radians/s, thermal speed `sqrt(2*kB*T/m)`. For B=0 use k-perpendicular=0
and harmonic n=0, independent of the dummy nonzero gyrofrequency. For magnetic
cases, the initial harmonic bound is `ceil(12*sqrt(k_perp²*rho²)+40)`, doubled
for the saved spectrum. To handle the explicit division by collision rate at
zero rate, compare 1e-6 with 1e-7 s⁻¹ and save the latter. Actual nonzero test
collision rates are passed unchanged. Single-ion spectra are not averaged to
manufacture mixtures.

**inscar.** Invoke the pinned PR's `SpectrumCalculation` with `IntMaxwell` and
`gordeyev_method='simpson'`; multiply its angular-frequency density PSD by `2*pi/ne`.
The required positive field is set to 40 μT with parallel geometry for B=0
tests: the perpendicular term vanishes exactly. All cases use 64,001/128,001
coarse/fine samples per species, exponent 3, and a fixed time cutoff
`15/(k*sqrt(kB*T/m)*abs(cos(theta)))`. The saved result uses 128,001 samples.
An independent check increases the cutoff factor from 15 to 18 at fixed sample
count. DC uses 1e-4 Hz and is checked separately at 1e-3 Hz. The pinned code uses
`scipy.constants.epsilon_0`. Arrays and errors for grid, cutoff and DC checks
are retained in each HDF5 group. All five compatible cases must pass 1e-6
against Kinetic and all three sensitivity checks in `verify_expanded.py`.

The refinement column uses the pairwise comparison metric. It is a two-setting
sensitivity check, not an error bound. Original four-code refinement records
remain in their original HDF5 files. Missing refinement values for added R
and Julia calculations mean “not assessed”, not exact evaluation.

## Reproduction

Run from the repository root. Python uses base conda. Commit source before
collection: hashes are checked against Git. First reproduce original data with
[DETAILS.md](DETAILS.md), or use the checked-in original HDF5 tables.

```sh
conda run -n base python additional.py prepare
conda run -n base python -m pip install --no-deps -e .cache/inscar-updated
conda run -n base python additional.py python
```

Python requires NumPy, SciPy, h5py, numba and the pinned inscar package; pip
installs its build backend. Runtime versions and adapter hashes are retained
in metadata. `--code Nicolls`, `--code Skolar` or `--code inscar` restricts a
rerun without removing the other saved raw results.

Julia 1.12 was used. The project and manifest record resolved dependencies.
The upstream module is included directly from its pinned checkout.

```sh
julia --project=runtimes/julia -e 'using Pkg; Pkg.instantiate()'
julia --project=runtimes/julia additional_julia.jl
```

The R program needs R and hdf5r. This creates an isolated runtime and builds
the original C source on macOS. On Linux use `-shared -fPIC` in place of
`-dynamiclib`, keeping the library name `ISspectrum.so`.

```sh
conda create -y -p .cache/r-env --override-channels -c conda-forge r-base r-hdf5r
mkdir -p .cache/virtanen-native
cc -O2 -dynamiclib .cache/ISspectrum/src/spec_worker.c .cache/ISspectrum/src/transf_worker.c -lm -o .cache/virtanen-native/ISspectrum.so
.cache/r-env/bin/Rscript additional_r.R
```

Collect, render every test with Rustplotlib, update reports, then verify:

```sh
conda run -n base python additional.py collect
cargo run --release --locked --manifest-path plots/Cargo.toml -- .
conda run -n base python report.py
conda run -n base python verify_tables.py
conda run -n base python verify_expanded.py
```

Rustplotlib is pinned in Cargo.toml/Cargo.lock and uses its ArticleWide default
typography and sizing. SVG and PNG are exported. The Rust HDF5 crate needs
a system HDF5 library; LaTeX labels need the TeX tools used by Rustplotlib.

Collection refuses stale adapter/source hashes. Expanded metadata includes
source URLs, full commits, source hashes, adapter hashes and runtime versions,
plus source-generator identifiers for imported original arrays. Verification
checks exact reuse of original grids and arrays, finite nonnegative
spectra, measured symmetry and pairwise metrics, refinement calculations, coverage and figure
files. It checks internal consistency without requiring every code to agree.
