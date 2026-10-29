"""Record the actual clean Git checkouts used to generate portable tables."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parent


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()


def source_info(path, expected_commit=None):
    path = Path(path).resolve()
    root = Path(git(path.parent, 'rev-parse', '--show-toplevel'))
    relative = path.relative_to(root).as_posix()
    commit = git(root, 'rev-parse', 'HEAD')
    if expected_commit is not None and commit != expected_commit:
        raise ValueError(f'{path}: checkout {commit} does not match {expected_commit}')
    # A commit alone does not identify uncommitted or untracked source code.
    tracked = subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{relative}'])
    if tracked != path.read_bytes() or git(root, 'status', '--porcelain', '--untracked-files=no', '--', '*.py'):
        raise ValueError(f'Commit Python source changes before generating tables: {root}')
    return dict(git_url=git(root, 'remote', 'get-url', 'origin'), git_commit=commit,
                code_path=relative, code_sha256=hashlib.sha256(tracked).hexdigest(),
                code_checkout_clean=True)


def sources(juha_path=None, john_root=None):
    # Imported here to avoid a calculate -> provenance -> compare import cycle.
    from compare import JUHA_REV, JOHN_REV
    return {
        'Analytic': source_info(ROOT/'calculate.py'),
        'Kinetic': source_info(ROOT/'models/kinetic.py'),
        'Vierinen': source_info(juha_path or ROOT/'.cache/vierinen/isr_spec.py', JUHA_REV),
        'Swoboda': source_info((Path(john_root) if john_root else ROOT/'.cache/swoboda')/'ISRSpectrum/ISRSpectrum.py', JOHN_REV),
    }


def read_sources(group):
    return {name: dict(record.attrs) for name, record in group['provenance'].items()}


def stamp(group, records, generator):
    """Put source identity on each code table and spectrum, plus a manifest."""
    info = source_info(ROOT/generator)
    for key, value in info.items():
        group.attrs['generator_'+key] = value
    manifest = group.require_group('provenance')
    for name, record in records.items():
        targets = [manifest.require_group(name)]
        if name in group:
            targets.append(group[name])
            targets.extend(group[name][x] for x in ['S_ion','S_electron','S_total'] if x in group[name])
        elif len(records) == 1:
            targets.append(group)
            targets.extend(group[x] for x in ['S_ion','S_electron','S_total'] if x in group)
        for extra in ['Vierinen_10000_points', 'Swoboda_unconverted_mass_input']:
            if extra.startswith(name+'_') and extra in group:
                targets.append(group[extra])
        for target in targets:
            for key, value in record.items():
                target.attrs[key] = value
