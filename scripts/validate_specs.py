"""Compatibility entry point for the canonical pytest contract suite."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "pytest", "tests/contracts", *sys.argv[1:]],
            cwd=root,
        )
    )
