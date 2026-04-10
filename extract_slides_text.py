#!/usr/bin/env python3
"""Repo-root launcher for scripts/extract_slides_text.py."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
r = subprocess.run(
    [sys.executable, str(root / "scripts" / "extract_slides_text.py")],
    cwd=str(root),
)
raise SystemExit(r.returncode)
