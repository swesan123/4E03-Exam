"""Run latexmk or pdflatex/xelatex on a generated .tex file."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def compile_tex(tex_path: Path, engine: str) -> Path:
    """
    Build PDF next to ``tex_path``. Prefer ``latexmk`` when available.
    Returns the path to the PDF.
    """
    tex_path = tex_path.resolve()
    workdir = tex_path.parent
    pdf_path = tex_path.with_suffix(".pdf")
    tex_name = tex_path.name

    latexmk = shutil.which("latexmk")
    if latexmk:
        # Run in the .tex directory so aux/PDF land beside the source (works with older latexmk
        # that lacks -outdir/-auxdir).
        if engine == "xelatex":
            cmd = [
                latexmk,
                "-xelatex",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-halt-on-error",
                tex_name,
            ]
        elif engine == "lualatex":
            cmd = [
                latexmk,
                "-lualatex",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-halt-on-error",
                tex_name,
            ]
        else:
            cmd = [
                latexmk,
                "-pdf",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-halt-on-error",
                tex_name,
            ]
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        if proc.returncode != 0:
            if proc.stdout:
                sys.stderr.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            raise RuntimeError(f"latexmk exited with code {proc.returncode}")
        if not pdf_path.is_file():
            raise RuntimeError(f"latexmk succeeded but PDF missing: {pdf_path}")
        return pdf_path

    if engine == "xelatex":
        binary = "xelatex"
    elif engine == "lualatex":
        binary = "lualatex"
    else:
        binary = "pdflatex"
    exe = shutil.which(binary)
    if not exe:
        raise FileNotFoundError(
            f"Neither latexmk nor {binary} was found in PATH. Install TeX Live (e.g. latexmk, {binary}) "
            "or pass --no-compile to only write the .tex file."
        )

    args = [
        exe,
        "-synctex=1",
        "-interaction=nonstopmode",
        "-file-line-error",
        "-halt-on-error",
        "-output-directory",
        str(workdir),
        str(tex_path),
    ]
    for run in range(1, 3):
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode != 0:
            if proc.stdout:
                sys.stderr.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            raise RuntimeError(f"{binary} failed on pass {run} with code {proc.returncode}")

    if not pdf_path.is_file():
        raise RuntimeError(f"{binary} finished but PDF missing: {pdf_path}")
    return pdf_path
