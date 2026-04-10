#!/usr/bin/env python3
"""Extract numbered questions from PDFs under the sample questions folder."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from exam_toolkit.paths import DATA_DIR, DEFAULT_SAMPLE_DIR, QUESTIONS_JSON
from exam_toolkit.text_clean import (
    is_true_false_question,
    normalize_raw_text,
    segment_questions,
    trim_before_first_question,
)


def pdf_stem_slug(pdf_path: Path) -> str:
    stem = pdf_path.stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    return stem.strip("_") or "questions"


def pdftotext_layout(pdf_path: Path) -> str:
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        print("pdftotext not found. Install poppler-utils (e.g. apt install poppler-utils).", file=sys.stderr)
        raise SystemExit(1) from e
    except subprocess.CalledProcessError as e:
        print(e.stderr or str(e), file=sys.stderr)
        raise SystemExit(1) from e
    return proc.stdout


def category_for_pdf(pdf_path: Path, fallback: str) -> str:
    name = pdf_path.stem.lower()
    if "test1" in name:
        return "test1"
    if "test2" in name:
        return "test2"
    return fallback


def extract_from_pdf(pdf_path: Path, default_category: str) -> list[dict]:
    raw = pdftotext_layout(pdf_path)
    lines = normalize_raw_text(raw)
    lines = trim_before_first_question(lines)
    slug = pdf_stem_slug(pdf_path)
    category = category_for_pdf(pdf_path, default_category)
    out: list[dict] = []
    for num, body in segment_questions(lines):
        qid = f"{slug}_q{num}"
        out.append(
            {
                "id": qid,
                "source_pdf": pdf_path.name,
                "number_in_pdf": num,
                "category": category,
                "is_true_false": is_true_false_question(body),
                "body_plain": body,
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=DEFAULT_SAMPLE_DIR,
        help="Directory containing sample PDFs",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=QUESTIONS_JSON,
        help="Output JSON path",
    )
    parser.add_argument(
        "--default-category",
        default="newer",
        choices=("newer", "test1", "test2"),
        help="Category for questions unless overridden by question_tags.yaml at build time",
    )
    args = parser.parse_args()

    sample_dir: Path = args.sample_dir
    if not sample_dir.is_dir():
        print(f"Sample directory not found: {sample_dir}", file=sys.stderr)
        raise SystemExit(1)

    pdfs = sorted(sample_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files in {sample_dir}", file=sys.stderr)
        raise SystemExit(1)

    all_questions: list[dict] = []
    for pdf in pdfs:
        all_questions.extend(extract_from_pdf(pdf, args.default_category))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(all_questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_questions)} questions to {args.out}")


if __name__ == "__main__":
    main()
