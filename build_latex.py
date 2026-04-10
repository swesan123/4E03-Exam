#!/usr/bin/env python3
"""Launcher: runs scripts/build_latex.py (imports need scripts/ on sys.path)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    script = root / "scripts" / "build_latex.py"
    sys.path.insert(0, str(root / "scripts"))
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
