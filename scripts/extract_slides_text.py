#!/usr/bin/env python3
"""Extract each slides/*.pdf to slides/text/<stem>.txt with parseable page markers."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def page_count(pdf: Path) -> int:
    out = subprocess.run(
        ["pdfinfo", str(pdf)],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(f"pdfinfo failed for {pdf}: {out.stderr}")
    m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.MULTILINE)
    if not m:
        raise RuntimeError(f"No Pages: line for {pdf}")
    return int(m.group(1))


def extract_pdf(pdf: Path, dest: Path) -> None:
    n = page_count(pdf)
    lines: list[str] = [
        f"source_pdf: {pdf.name}",
        f"source_path: slides/{pdf.name}",
        f"pages: {n}",
        "format_version: 1",
        "",
    ]
    for p in range(1, n + 1):
        proc = subprocess.run(
            ["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pdftotext failed for {pdf} page {p}: {proc.stderr}")
        body = proc.stdout.strip()
        lines.append(f"--- PAGE {p} ---")
        lines.append(body if body else "(no text)")
        lines.append("")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    slides = root / "slides"
    out_dir = slides / "text"
    pdfs = sorted(slides.glob("*.pdf"))
    if not pdfs:
        print("No PDFs in slides/", file=sys.stderr)
        return 1
    for pdf in pdfs:
        stem = pdf.stem
        dest = out_dir / f"{stem}.txt"
        extract_pdf(pdf, dest)
        print(dest.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
