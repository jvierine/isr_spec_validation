"""Run the existing adapters with explicit numerical integration settings.

The upstream integrators and physical equations are unchanged. Temporary
settings are restored even if a calculation fails; calls are sequential.
"""
from functools import lru_cache
import sys
import numpy as np
from compare import (JUHA_REV, JOHN_REV, source, load_juha, vierinen,
                     swoboda, calculate)


@lru_cache
def _vierinen_module():
    return load_juha(source('https://github.com/jvierine/isr_analysis',
                            JUHA_REV, 'vierinen') / 'isr_spec.py')


@lru_cache
def _swoboda_type():
    root = source('https://github.com/jswoboda/ISRSpectrum', JOHN_REV, 'swoboda')
    sys.path.insert(0, str(root))
    from ISRSpectrum.ISRSpectrum import Specinit
    return Specinit


def run_vierinen(case, *, points, time_window_multiplier):
    mod = _vierinen_module()
    original = mod.gordoyev2

    def quadrature(*args, **kwargs):
        kwargs['inf'] = time_window_multiplier * kwargs.get('inf', 1e-3)
        return original(*args, **kwargs)

    mod.gordoyev2 = quadrature
    try:
        return vierinen(mod, case, points)
    finally:
        mod.gordoyev2 = original


def run_swoboda(case, *, quadrature_N, errF):
    Specinit = _swoboda_type()
    from ISRSpectrum.plugins import gordplugs
    namespace = gordplugs['default'].calcgordeyev.__func__.__globals__
    original = namespace['sommerfelderfrep']

    def quadrature(func, N, omega, b1, **kwargs):
        kwargs['errF'] = errF
        result = original(func, quadrature_N, omega, b1, **kwargs)
        if not result[1]:
            raise RuntimeError('Swoboda quadrature failed to converge')
        return result

    namespace['sommerfelderfrep'] = quadrature
    try:
        return swoboda(Specinit, case)
    finally:
        namespace['sommerfelderfrep'] = original


def run_analytic(case):
    return np.array(calculate.spectrum(case['radar_hz'], case['ne'],
                                      case['ti'], case['te'], case['ions'],
                                      case['frequency_hz']))
