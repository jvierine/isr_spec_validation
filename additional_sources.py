"""Pinned, unmodified upstream checkouts for the expanded comparisons."""
from pathlib import Path
import subprocess
from compare import ROOT, source
from provenance import source_info

SOURCES = {
    'Buchert': ('stephancb/IncoherentScatter.jl', '640110f6f7f2b3652498f18028ed4b8c9e03daeb', 'IncoherentScatter.jl', 'src/IncoherentScatter.jl'),
    'Virtanen': ('ilkkavir/ISspectrum', '28458b2cefcce247e010a0f2555a934a051927a4', 'ISspectrum', 'R/ISspectrum.general.R'),
    'Martinez': ('miguel-martinez-ledesma/ISR_Model', '369e277c7d388b7b3e4c63d5402b31304ef954ef', 'ISR_Model', 'Model_ISR/ISR_simulator.m'),
    'Nicolls': ('isrsummerschool/lecture_supplements_2024', '5f02f3edaf09cc5b3f03617f50e9412ec12df4bd', 'isr_school', 'is_spectral_model/ismodel.py'),
    'Sandbem': ('Sandbem/ISRTS', 'd31ddafa87be19c957bb1949dcddc29a2f518432', 'ISRTS', 'src/ISR_spectrumKM.m'),
    'Skolar': ('crskolar/OO_Collisions', 'e3e212f6c31d364c2bd48f01b3ebafdf9769f533', 'OO_Collisions', 'ISRSpectraFunctions.py'),
    'inscar': ('engeir/inscar', '3bb9b1217c9a9b1cb5e5c320635cea1cf4ca9e05', 'inscar', 'src/inscar/spectrum_calculation.py'),
}


def checkout(name):
    repo, commit, folder, entry = SOURCES[name]
    return source('https://github.com/'+repo, commit, folder)


def record(name):
    repo, commit, folder, entry = SOURCES[name]
    root = ROOT/'.cache'/folder
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=no'],text=True).strip():
        raise ValueError(f'Modified upstream checkout: {root}')
    return source_info(root/entry, commit)
