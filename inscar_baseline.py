"""Immutable pre-update tables used by the historical accuracy experiment."""
import subprocess
from compare import ROOT

BASELINE_COMMIT='4a5bf34f76bd741b5abfb11d4e0594f694c276f0'


def baseline_bytes(name):
    """Read committed HDF5 bytes, independent of the current benchmark version."""
    return subprocess.check_output(['git','-C',str(ROOT),'show',
                                   f'{BASELINE_COMMIT}:tables/expanded/{name}.h5'])
