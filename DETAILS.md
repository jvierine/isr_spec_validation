# Reproduce the comparisons

This document describes the original four-code runs. Expanded native-code
comparisons and all per-test figures are documented in [NEW_CODES.md](NEW_CODES.md).

```sh
conda run -n base python compare.py
conda run -n base python extended.py
conda run -n base python refine.py
conda run -n base python report.py
conda run -n base python verify_tables.py
```

Requires Git, NumPy, SciPy, h5py, matplotlib, mpi4py (with an MPI runtime),
and six. The commands fetch the pinned upstream commits listed in the README
into an ignored `.cache/` directory. They do not change those upstream files.
The recorded baseline run used SciPy 1.17.1. Exact versions and source hashes
are stored in the baseline HDF5 files.

Each HDF5 code table and spectrum carries `git_url`, `git_commit` (full checkout
hash), `code_path` and `code_sha256`. The `/provenance` group lists every code
used; `generator_git_*` attributes identify the adapter/generator checkout.
The existing text tables include the URL and full commit in their headers.
Generation rejects uncommitted Python source changes and mismatched upstream
checkouts. The Kinetic code is identified by its tracked snapshot in this
repository, since its original workspace was not a Git repository.

The original test definitions and analytical equations are in [METHODS.md](METHODS.md).
The local kinetic implementation is preserved verbatim in `models/kinetic.py`;
it was copied from the Vlasov–Boltzmann project's `isr/kinetic.py`.

## What is compared

Every baseline file contains the same frequency grid and plasma parameters,
and each code's ion-source contribution, electron-source contribution and total.
Spectra are per electron per Hz. No amplitude, frequency, peak or area is fitted.
The README matrix uses total spectra and reports the worst case for each pair.
Separate component errors and quadrature-refinement errors are also retained.

The comparison metric is symmetric:
`max(abs(A-B)) / max(max(abs(A)), max(abs(B)))`.
The pass threshold is 1e-6, chosen before running the comparison. A green result
only applies to the tested parameters and frequency samples.

## Adapters and findings

**Vierinen.** The spectrum equations agree. The adapter handles three interface
limits without changing them:

- Recent SciPy requires `simpson(y, x=x)` instead of positional `x`.
- At B=0, select the upstream `gaussian_disp` function. The default magnetic
  displacement function otherwise divides by zero in its gyrofrequency term.
- At exactly zero frequency, numerator and denominator both vanish in the
  conductivity formulation. Use its limit at 1e-6 Hz; 1e-5 Hz was also checked
  during refinement. This is not a physical spectral singularity.

The returned spectrum includes electron density; divide by ne to match these
tables. `include_electron_component=False` actually retains the electron-source
term and removes the ion-source term. The adapter accounts for that naming
mismatch when saving the separate components. Magnetic field input is in tesla
despite the upstream nT comment; alpha is degrees away from perpendicular.

The baseline calculation uses 20,000 quadrature points, compared with 10,000.
The upstream time cutoffs are retained (electron 1e-4 s, ion 1e-3 s).
The largest baseline total-spectrum discrepancy is 9.58e-11 of peak;
separate contributions also pass 1e-6. A finite time cutoff remains an
independent convergence condition, especially near perpendicular.

For the additional cold-ion cases, the 1 ms ion cutoff leaves a roughly 1e-6
error even when doubling the number of points. Extending the cutoff resolves
it. In the plasma-line case, refining the point count is needed because the
small dielectric denominator amplifies quadrature errors. `refine.py` retains
the original results and adds a `refined` group using doubled time cutoffs and
160,000 points, checked against 80,000.

**Swoboda.** Its plugin multiplies the ion mass argument by the proton mass,
although the docstring labels the input AMU. Pass `mass_u * atomic_mass / m_p`
to give the same physical mass. Supplying identical numbers without this
conversion produces 0.35–1.14% differences in these baseline total spectra.
Those unconverted spectra are retained as `Swoboda_unconverted_mass_input`.
The output is density scaled, despite a stale docstring describing unit-peak
normalization; divide by ne. Use the separate-line output directly.

For magnetic tests, set `alphamax=91` to evaluate the magnetic response at all
tested angles. Its default `alphamax=30` neglects magnetic effects farther
than 30 degrees from perpendicular. No charged-particle collisions are used
in comparisons to the local neutral BGK model.

**Kinetic.** This code measures angle from B, so the other codes receive
`alpha = 90 - theta`. Its opposite Fourier convention conjugates susceptibilities
but leaves these stationary power spectra unchanged.

## Additional cases

[Extended matrices](EXTENDED_RESULTS.md) and [HDF5 data](tables/extended/) cover
430 MHz, a 40 μT magnetic field at 42 and 85 degrees from B, neutral BGK
collisions at 42 degrees and parallel to B, and an unmagnetized plasma-line case.
These are prescribed validation parameters, not fitted Arecibo measurements.
Each case displays one pass/fail matrix for the configured calculation.
Clicking a code name opens its executable call in [invocations.py](invocations.py),
including the numerical settings used for the displayed result. For example:

```sh
conda run -n base python invocations.py --case magnetic_85deg --code Swoboda
```

This reruns the selected code and checks its spectrum against the saved table;
it does not overwrite the data. Earlier numerical settings remain in HDF5 for
convergence auditing, rather than appearing as an extra comparison matrix.

The original collision cases use electron/ion rates 10,000/1,000 s⁻¹ and compare only
Swoboda and Kinetic: Vierinen's tested spectrum entry point does not implement
those collisions. Exact perpendicular, Coulomb collisions, non-Maxwellian
distributions and HF-driven waves are outside this validation set.

Swoboda's initial magnetic quadrature uses N=100. The refined tests increase
this adaptively until the last refinement changes the total spectrum by less
than 1e-8 of peak, and tighten `errF` from 1e-6 to 1e-12. N=800 suffices at
42 degrees; the 85-degree case requires N=6400. After refinement, all original tested
pairs pass 1e-6. The worst plasma-line discrepancy is 8.55e-9; the magnetic
and neutral-collision discrepancies are below 2.2e-14.
The same upstream integrator and physical equations are used; every convergence
flag is checked. Refinements are explicit in the HDF5 metadata, never applied
as an empirical correction to a spectrum.
