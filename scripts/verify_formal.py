"""Strict, end-to-end Lean/Python/JS arithmetic verification.

Run from the repository root with `uv run python scripts/verify_formal.py`.
Unlike the regular pytest suite, this requires a working Lean + Mathlib setup.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, check=True, cwd=ROOT)


def main():
    if shutil.which('lake') is None:
        print('ERROR: lake is unavailable; install elan and run lake exe cache get',
              file=sys.stderr)
        return 2
    if shutil.which('node') is None:
        print('ERROR: node is required for strict offline-JavaScript parity checks',
              file=sys.stderr)
        return 2
    run(sys.executable, 'scripts/generate_formal_fixtures.py', '--check')
    run('lake', 'build', 'SeedBayes')
    run(sys.executable, '-m', 'pytest', '-q')
    print('Lean kernel proofs and Python/JavaScript fixture conformance passed.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as ex:
        raise SystemExit(ex.returncode) from ex
