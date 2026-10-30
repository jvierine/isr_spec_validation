# Other ISR spectrum programs

Catalog checked on **30 October 2026** using upstream documentation, source
files, and archive records. These programs calculate theoretical incoherent
scatter spectra; packages that only read or plot measured ISR data are excluded.

**Execution status:** Buchert, Virtanen's R/C program, Nicolls, Skolar and inscar
now have [numerical comparisons](README.md) and [documented adapters](NEW_CODES.md).
Martinez and Sandbem are listed as not run following cancellation of MATLAB
execution. Remaining entries are catalog only. Capabilities below describe
the inspected implementation or its author's documentation, not verified accuracy.

## Calculators and implementations

| Program | Language | Scope and relationship |
|---|---|---|
| [inscar](#inscar) | Python | Maxwellian, kappa, and arbitrary isotropic velocity distributions; magnetic field and collisions. |
| [Nicolls ISspec](#nicolls-isspec) | Python | Multiple ions, drifts, magnetic response, neutral and Coulomb collision options; ISR-school and AMISR versions. |
| [OO_Collisions](#oo_collisions) | Python | Numerical velocity-distribution integrals, including non-Maxwellian examples. |
| [ISRTS](#isrts) | MATLAB | Multiple ions, drifts, collisions, magnetic field; two Gordeyev evaluation methods. |
| [ISR_Model](#isr_model) | MATLAB | Collisionless, unmagnetized Kudeki–Milla spectrum. |
| [diffx](#diffx) | MATLAB / C | Maxwellian spectra and additional distribution-function routines. |
| [IncoherentScatter.jl](#incoherentscatterjl) | Julia | Spectrum and ACF calculation with unmagnetized ion admittance and a magnetized electron response. |
| [GUISDAP](#guisdap-and-its-interfaces) | MATLAB / native routines | EISCAT analysis suite containing the spectrum calculation used by the next two interfaces. |
| [ISspectrum](#isspectrum-r) | R / C | R interface to GUISDAP spectrum routines. |
| [ISspectrumMATLAB](#isspectrummatlab) | MATLAB | Extracted GUISDAP spectrum routines with a GUI. |
| [ISgeometry](#isgeometry) | R | Radar-performance package containing a directly callable spectrum implementation. |
| [Charged-dust spectrum](#charged-dust-spectrum) | MATLAB | D-region spectrum with charged dust; archived on DataverseNO. |

These are software entries, **not twelve independent theories or validation
votes**. In particular, the GUISDAP interfaces share ancestry, and the two
Nicolls distributions below belong to the same model family.

### inscar

The main comparisons use the updated [PR #537 commit](https://github.com/jvierine/inscar/tree/532412a280a7e3373595fbaff763bcf12471622e)
with SI permittivity and Simpson quadrature. The [accuracy study](INSCAR_ACCURACY.md)
retains results from the earlier upstream version cataloged below.

[Eirik R. Enger, engeir/inscar](https://github.com/engeir/inscar).
The documentation describes `IntMaxwell`, `IntKappa`, and `IntLong` for an
arbitrary isotropic distribution, based on Hagfors (1961) and Mace (2003).
Inputs include electron/ion temperatures, densities, masses and collision
frequencies, radar frequency, magnetic field and aspect angle. Useful for
extending comparisons beyond Maxwellians; it is not advertised as an arbitrary
anisotropic-distribution solver.

[Calculation source](https://github.com/engeir/inscar/blob/3bb9b1217c9a9b1cb5e5c320635cea1cf4ca9e05/src/inscar/spectrum_calculation.py)
and [examples](https://github.com/engeir/inscar/blob/3bb9b1217c9a9b1cb5e5c320635cea1cf4ca9e05/assets/examples.py).
License: MIT. Archived release: [v3.0.3, Zenodo 6587001](https://doi.org/10.5281/zenodo.6587001);
that release is older than the inspected GitHub source.

### Nicolls ISspec

[ISR Summer School 2024 spectral-model materials](https://github.com/isrsummerschool/lecture_supplements_2024/tree/5f02f3edaf09cc5b3f03617f50e9412ec12df4bd/is_spectral_model).
The `ISspec` class credits M. Nicolls (2011–2013), exposes `computeSpec()`, and
returns spectra and ACFs. Its inputs support multiple ion species, separate
species velocities and temperatures, magnetic field, and switches for Coulomb
and neutral BGK collisions. Angle is measured from B: 90 degrees is
perpendicular. Numerical convergence settings are exposed.

[Model source](https://github.com/isrsummerschool/lecture_supplements_2024/blob/5f02f3edaf09cc5b3f03617f50e9412ec12df4bd/is_spectral_model/ismodel.py).
The school repository has a GPL-3.0 license. An older related implementation is
in [amisr/overspread](https://github.com/amisr/overspread/blob/c26a736c9b356f55fd7845ad5a093504e684f434/src/ISfit/amisr_py/ismodel/spec.py);
that version contains Python 2 syntax and local import-path assumptions. Treat
these as one family, and check current Python/SciPy compatibility before use.

### OO_Collisions

[crskolar/OO_Collisions](https://github.com/crskolar/OO_Collisions).
The source contains numerical susceptibility and fluctuation integrals,
Maxwellian and bi-Maxwellian formulas, and spectrum assembly through
`calcSpectra`. Examples cover Maxwellian, kappa, super-Gaussian, and toroidal
ion distributions. This is a useful candidate for comparisons involving
velocity-space quadrature and non-Maxwellian spectra.

[Core functions](https://github.com/crskolar/OO_Collisions/blob/e3e212f6c31d364c2bd48f01b3ebafdf9769f533/ISRSpectraFunctions.py)
and [spectrum examples](https://github.com/crskolar/OO_Collisions/tree/e3e212f6c31d364c2bd48f01b3ebafdf9769f533/spectrumScripts).
The README is minimal and no top-level license file was found. The examples
require their own convergence and normalization checks; inclusion here is not a
claim that their collision operator matches any existing benchmark.

### ISRTS

[Sandbem/ISRTS](https://github.com/Sandbem/ISRTS).
The documented `ISR_main` interface supports ion mixtures, species drifts,
neutral collisions, magnetic field, and a Coulomb-collision switch. Gordeyev
integrals can use Sommerfeld integration or a Bessel expansion; the interface
also selects Kudeki–Milla or a second spectral formulation. Its magnetic angle
is measured from B, while its separate scattering angle is 180 degrees for
backscatter.

[Entry point](https://github.com/Sandbem/ISRTS/blob/d31ddafa87be19c957bb1949dcddc29a2f518432/src/ISR_main.m)
and [input documentation](https://github.com/Sandbem/ISRTS/blob/d31ddafa87be19c957bb1949dcddc29a2f518432/README.md)
(Chinese). No top-level license file was found; bundled numerical routines have
their own attribution. The collision options have not been checked here.

### ISR_Model

[Miguel Martínez Ledesma, ISR_Model](https://github.com/miguel-martinez-ledesma/ISR_Model).
The README explicitly limits this Kudeki–Milla (2011) model to **no collisions
and no magnetic-field effects**. It includes species-management routines and a
test example, making it a candidate for the existing unmagnetized baseline.

[Spectrum routine](https://github.com/miguel-martinez-ledesma/ISR_Model/blob/369e277c7d388b7b3e4c63d5402b31304ef954ef/Model_ISR/ISR_simulator.m)
and [example](https://github.com/miguel-martinez-ledesma/ISR_Model/blob/369e277c7d388b7b3e4c63d5402b31304ef954ef/Test_Model_ISR.m).
The repository bundles Linux and Windows Dawson-function MEX binaries; other
platforms need a compatible dependency. No top-level license file was found.

### diffx

[Patrick Guio / uit-space-physics/diffx](https://github.com/uit-space-physics/diffx).
`diffx` constructs total, electron-source and ion-source spectra from plasma
response functions. The repository includes Maxwellian, two-temperature, and
power-law routines plus complex-error-function helpers. The power-law branch
inside the inspected `diffx` entry point is disabled, so its presence should
not be read as a tested default capability.

[Entry point](https://github.com/uit-space-physics/diffx/blob/9b11a2159f89421f606bfa1a1506324604404023/diffx.m)
and [test example](https://github.com/uit-space-physics/diffx/blob/9b11a2159f89421f606bfa1a1506324604404023/test_spec.m).
The spectrum files carry GPL-2.0-or-later notices. MATLAB/C dependencies and
older example assumptions need checking before running.

### IncoherentScatter.jl

[Stephan C. Buchert, IncoherentScatter.jl](https://github.com/stephancb/IncoherentScatter.jl).
Defines `ScatterVolume`, `Plasma`, `CollisionalPlasma`, `pwrspec`, and ACF
transforms. The inspected implementation has unmagnetized ion admittances and
a magnetized electron response; it should not be assumed equivalent to a full
magnetized response for every species and angle.

[Implementation](https://github.com/stephancb/IncoherentScatter.jl/blob/640110f6f7f2b3652498f18028ed4b8c9e03daeb/src/IncoherentScatter.jl).
License: MIT. The package declares Julia dependencies but has not been installed
here. Use the repository ending in `.jl`: the similarly named
`stephancb/IncoherentScatter` repository contained only a README, license and
Git ignore file when inspected.

### GUISDAP and its interfaces

[EISCAT GUISDAP](https://gitlab.com/eiscat/guisdap9) is the parent analysis suite
for the spectrum routines exposed by the following two packages. Its role is
documented in [Lehtinen and Huuskonen (1996)](https://doi.org/10.1016/0021-9169(95)00047-X).
These interfaces are useful access routes to the model, but are not independent
physical cross-checks of GUISDAP. Consult the distribution's file-level notices
before redistributing its components.

### ISspectrum (R)

[Ilkka Virtanen, ilkkavir/ISspectrum](https://github.com/ilkkavir/ISspectrum).
An R interface to GUISDAP C routines. `ISspectrum.general` documents up to seven
singly charged ion species, separate temperatures, collision frequencies and
drifts, with arbitrary radar frequency and scattering angle. `ISspectrum.guisdap`
accepts parameters resembling GUISDAP fit output.

[General interface](https://github.com/ilkkavir/ISspectrum/blob/28458b2cefcce247e010a0f2555a934a051927a4/R/ISspectrum.general.R)
and [C calculation](https://github.com/ilkkavir/ISspectrum/blob/28458b2cefcce247e010a0f2555a934a051927a4/src/spec_worker.c).
The package metadata declares `FreeBSD`. It has no magnetic-field input in the
general interface. Its scaled spectral output needs an explicit unit conversion
before comparison with the per-electron, per-Hz tables here.

### ISspectrumMATLAB

[Ilkka Virtanen, ilkkavir/ISspectrumMATLAB](https://github.com/ilkkavir/ISspectrumMATLAB).
Extracted GUISDAP routines with the `ISspectrum` GUI and callable
`guisdap_spec(f,elec,ions,radar)`. The latter accepts ion composition,
temperatures, drifts and collision frequencies; its scattering angle is in
**radians**, unlike the R interface. Collision-frequency helper routines require
MATLAB's Aerospace Toolbox, according to the README.

[Calculator](https://github.com/ilkkavir/ISspectrumMATLAB/blob/c8b4482a60d2601a4a4e72afd0dfcef46d856fcb/guisdap_spec.m)
and [usage](https://github.com/ilkkavir/ISspectrumMATLAB/blob/c8b4482a60d2601a4a4e72afd0dfcef46d856fcb/README.md).
No top-level license file was found; the repository identifies its GUISDAP
origin. Check the actual function header when supplying ion parameters.

### ISgeometry

[Ilkka Virtanen and Mikko Orispää, ilkkavir/ISgeometry](https://github.com/ilkkavir/ISgeometry).
Although primarily a radar-performance package, it contains an R spectrum
calculation: `incoherentScatterSpectrum`, plus the two-ion convenience interface
`ISspectrumSimple`. The former evaluates plasma dispersion functions without the
tabulated values used by the older interface. Inputs include species properties,
drifts, collisions and scattering geometry; there is no B-field input.

[Spectrum implementation](https://github.com/ilkkavir/ISgeometry/blob/94085b4928000670dd6ecbec5ac4406703d56938/R/incoherentScatterSpectrum.R).
License: BSD-2-Clause. [Zenodo v0.5-6](https://doi.org/10.5281/zenodo.6623187)
is a release archive, not a claim that it is identical to the inspected GitHub
revision. The [e3doubt paper](https://doi.org/10.5194/angeo-43-633-2025) describes
the spectrum used in its experiment-design application.

### Charged-dust spectrum

[Gunnarsdottir and Mann (2021), DataverseNO](https://doi.org/10.18710/GHZIIY),
*Replication Data for: Charged dust in the D-region incoherent scatter spectrum*.
This archive includes MATLAB code, not only data: `Basic_run.m`, `dustIRS.m`,
`dustIRS_Charge.m`, and collision-frequency helpers. Its documented scope is
charged dust in the approximately 50–100 km altitude region.

The dataset declares CC0-1.0. This is a different physical regime from the
current F-region and topside baseline, and would need dedicated dust-containing
benchmark cases. See the archive's `00_README.txt` for its input assumptions.

## Additional archives and related applications

| Resource | What it adds | How to count it |
|---|---|---|
| [ISRSpectrum 4.1.0, Zenodo 12609623](https://doi.org/10.5281/zenodo.12609623) | Archived release of John Swoboda's calculator. | The Swoboda family is already compared here; the archive is an additional citation/download route, not another calculator. |
| [Synthetic EISCAT UHF/VHF spectra from TIE-GCM, Zenodo 13947114](https://doi.org/10.5281/zenodo.13947114) | Günzkofer et al. (2024), MATLAB software and data. The inspected `software.zip` contains synthetic-spectrum/fitting scripts and GUISDAP `spec`/`transf` routines. Record license: CC-BY-4.0; retain bundled files' own notices. | A reproducible application of GUISDAP-family routines, not an independent spectrum theory. Local input paths in the scripts need adapting. |
| [EISCAT3D interferometric imaging, Zenodo 14711480](https://doi.org/10.5281/zenodo.14711480) | Huyghebaert et al. (2025), imaging and spectrum reconstruction software. | The archive explicitly credits Swoboda's ISRSpectrum for spectrum generation. |
| [SimISR](https://github.com/jswoboda/SimISR) | Synthetic ISR voltage/data simulator; lists `isrspectrum` as a dependency. | Useful for simulation, but not another independent theoretical spectrum calculator. |

The search covered GitHub repository/code search, Zenodo records, GitLab, and
DataverseNO. It is a curated starting point, not an exhaustive inventory.
Public source availability alone does not establish a reuse license; missing
license notes above describe the inspected repository, not permission to copy it.
