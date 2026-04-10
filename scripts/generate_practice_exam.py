#!/usr/bin/env python3
"""Assemble a practice exam (8 calculation + 1 ten-part T/F) with usage tracking."""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from exam_toolkit.latex_escape import latex_escape_plain, strip_private_use_for_latex
from exam_toolkit.paths import (
    GENERATED_EXAMS_DIR,
    GENERATED_EXAMS_WORK_DIR,
    QUESTIONS_JSON,
    QUESTION_TAGS_YAML,
    USAGE_JSON,
)
from exam_toolkit.sampling import (
    count_letter_subparts,
    pick_stratified_calc,
    pick_tf_question,
)
from exam_toolkit.tags import effective_category, load_question_tags
from exam_toolkit.latex_compile import compile_tex
from exam_toolkit.tex_preamble import document_start_lines


def _default_latex_engine() -> str:
    return "lualatex" if shutil.which("lualatex") else "pdflatex"


def latex_body_lines(body_plain: str) -> str:
    return "\n".join(latex_escape_plain(L) + r"\\" for L in body_plain.split("\n"))


def latex_body_flowing(body_plain: str) -> str:
    """
    Reflow pdftotext-wrapped lines into readable paragraphs while keeping
    obvious sub-question markers on separate lines.
    """
    marker_re = re.compile(r"^\s*(\([a-zivx]+\)|\(\w+\)|\d+\.)\s*", re.IGNORECASE)
    lines = [strip_private_use_for_latex(x).rstrip() for x in body_plain.split("\n")]
    paragraphs: list[str] = []
    cur = ""

    for raw in lines:
        line = raw.strip()
        if not line:
            if cur:
                paragraphs.append(cur)
                cur = ""
            continue

        if marker_re.match(line):
            if cur:
                paragraphs.append(cur)
            cur = line
            continue

        if not cur:
            cur = line
            continue

        # Repair PDF hyphenation breaks: "circulat-" + "ing" -> "circulating"
        if cur.endswith("-") and line and line[0].islower():
            cur = cur[:-1] + line
        else:
            cur = f"{cur} {line}"

    if cur:
        paragraphs.append(cur)

    return "\n\n".join(_render_paragraph_for_latex(p) for p in paragraphs)


def _looks_equation_paragraph(p: str) -> bool:
    t = p.strip()
    if not t:
        return False
    if "=" not in t:
        return False
    if len(t) > 120:
        return False
    if t.endswith(".") or t.endswith("?"):
        return False
    return True


def _equationify(line: str) -> str:
    # Normalize common OCR forms from sample PDFs.
    t = line.replace("−", "-")
    t = re.sub(r"\bf([A-Za-z])\s*\(\s*([A-Za-z])\s*\)", r"f_\1(\2)", t)
    t = re.sub(r"\be\s*-\s*([0-9]*\.?[0-9]*\s*[A-Za-z]+)\b", r"e^{-\1}", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _render_paragraph_for_latex(p: str) -> str:
    if _looks_equation_paragraph(p):
        eq = _equationify(strip_private_use_for_latex(p))
        return r"\[" + "\n" + eq + "\n" + r"\]"
    return latex_escape_plain(p)


def latex_body_preserve_layout(body_plain: str) -> str:
    text = strip_private_use_for_latex(body_plain).rstrip()
    return (
        r"\begin{Verbatim}[breaklines=true,breakanywhere=true,fontsize=\small]" + "\n"
        + text
        + "\n"
        + r"\end{Verbatim}"
    )


def load_questions(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_usage(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def save_usage(path: Path, usage: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(usage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def bump_usage(usage: dict, qids: list[str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for qid in qids:
        rec = usage.setdefault(qid, {"count": 0, "last_run": now})
        rec["count"] = int(rec.get("count", 0)) + 1
        rec["last_run"] = now


def parse_marks(s: str, n: int) -> list[int]:
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) != n:
        raise ValueError(f"Expected {n} comma-separated marks, got {len(parts)} from {s!r}")
    return [int(p) for p in parts]


def build_document(
    calc_qs: list[dict],
    tf_q: dict,
    marks_calc: list[int],
    tf_marks: int,
    with_answers: bool,
    preserve_layout: bool,
    latex_engine: str | None = None,
) -> str:
    if latex_engine is None:
        latex_engine = _default_latex_engine()
    lines: list[str] = document_start_lines(latex_engine)
    lines.extend(
        [
            r"\title{COMP SCI/SFWR ENG 4E03 --- Practice Exam (generated)}",
            r"\date{}",
            r"\maketitle",
            r"\section*{Instructions}",
            r"This document was generated automatically. "
            r"Eight questions involve calculations or short analysis; "
            r"one question is True/False (one mark per part). "
            r"Default build uses \textbf{LuaLaTeX} when available (good Unicode from PDFs); "
            r"otherwise pdfLaTeX with a limited symbol map.\par",
            r"\begin{enumerate}",
        ]
    )

    for i, q in enumerate(calc_qs):
        m = marks_calc[i]
        lines.append(f"\\item \\textbf{{[{m} marks]}} \\texttt{{{latex_escape_plain(q['id'])}}}\\par\\smallskip")
        if preserve_layout:
            lines.append(latex_body_preserve_layout(q["body_plain"]))
        else:
            lines.append(latex_body_flowing(q["body_plain"]))
        if with_answers:
            lines.append(r"\textit{(Answer space.)}\par\smallskip")

    n_parts = count_letter_subparts(tf_q["body_plain"])
    lines.append(
        f"\\item \\textbf{{[{tf_marks} marks total --- {n_parts} True/False parts]}} "
        f"\\texttt{{{latex_escape_plain(tf_q['id'])}}}\\par\\smallskip"
    )
    if preserve_layout:
        lines.append(latex_body_preserve_layout(tf_q["body_plain"]))
    else:
        lines.append(latex_body_flowing(tf_q["body_plain"]))
    if with_answers:
        lines.append(r"\textit{(Answer space.)}\par\smallskip")

    lines.extend([r"\end{enumerate}", r"\end{document}", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_JSON)
    parser.add_argument("--tags", type=Path, default=QUESTION_TAGS_YAML)
    parser.add_argument("--usage", type=Path, default=USAGE_JSON)
    parser.add_argument("--output-dir", type=Path, default=GENERATED_EXAMS_DIR, help="PDF output directory")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=GENERATED_EXAMS_WORK_DIR,
        help="Working directory for .tex/.aux/.log files",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--marks",
        default="10,10,10,10,10,10,15,5",
        help="Comma-separated marks for the eight calculation questions",
    )
    parser.add_argument(
        "--tf-marks",
        type=int,
        default=10,
        help="Total marks shown for the True/False block (typically 10)",
    )
    parser.add_argument(
        "--min-tf-subparts",
        type=int,
        default=10,
        help="Prefer T/F questions with at least this many (a)--(z) sub-parts",
    )
    parser.add_argument(
        "--with-answers",
        action="store_true",
        help="Insert placeholder answer lines after each question",
    )
    parser.add_argument(
        "--preserve-layout",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Preserve PDF line layout in question bodies (default: off for readability)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selection to stderr and do not write files or update usage",
    )
    parser.add_argument(
        "--latex-engine",
        choices=("lualatex", "pdflatex", "xelatex"),
        default=_default_latex_engine(),
        help="LuaLaTeX if installed (default), else pdfLaTeX; or choose explicitly",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Only write the .tex file; do not run latexmk/pdflatex",
    )
    parser.add_argument(
        "--reset-usage",
        action="store_true",
        help="Clear usage history before selecting this exam",
    )
    parser.add_argument(
        "--clear-usage-only",
        action="store_true",
        help="Clear usage history and exit without generating",
    )
    args = parser.parse_args()

    if not args.questions.is_file():
        print(f"Missing {args.questions}", file=sys.stderr)
        raise SystemExit(1)

    questions = load_questions(args.questions)
    try:
        tags = load_question_tags(args.tags)
    except (RuntimeError, ValueError) as e:
        print(e, file=sys.stderr)
        raise SystemExit(1) from e

    eff_cat = {q["id"]: effective_category(q, tags) for q in questions}

    calc_pool = [q for q in questions if not q.get("is_true_false")]
    tf_pool = [q for q in questions if q.get("is_true_false")]

    calc_by_cat: dict[str, list[dict]] = {"test1": [], "test2": [], "newer": []}
    for q in calc_pool:
        calc_by_cat[eff_cat[q["id"]]].append(q)

    rng = random.Random(args.seed)
    usage = load_usage(args.usage)
    if args.reset_usage or args.clear_usage_only:
        usage = {}
        save_usage(args.usage, usage)
        print(f"Cleared usage history at {args.usage}", flush=True)
        if args.clear_usage_only:
            return
    try:
        marks_calc = parse_marks(args.marks, 8)
        calc_picked = pick_stratified_calc(calc_by_cat, usage, 8, rng)
        tf_pick = pick_tf_question(tf_pool, usage, rng, args.min_tf_subparts)
    except (ValueError, RuntimeError) as e:
        print(e, file=sys.stderr)
        raise SystemExit(1) from e

    if args.dry_run:
        print("Calculation questions:", [q["id"] for q in calc_picked], file=sys.stderr)
        print("True/False question:", tf_pick["id"], file=sys.stderr)
        return

    bump_usage(usage, [q["id"] for q in calc_picked] + [tf_pick["id"]])
    save_usage(args.usage, usage)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_dir: Path = args.output_dir
    work_dir: Path = args.work_dir
    pdf_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = work_dir / f"practice_exam_{stamp}.tex"
    tex = build_document(
        calc_picked,
        tf_pick,
        marks_calc,
        args.tf_marks,
        args.with_answers,
        args.preserve_layout,
        latex_engine=args.latex_engine,
    )
    out_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {out_path}", flush=True)
    print(f"Updated usage counts in {args.usage}", flush=True)

    if args.no_compile:
        print("Skipped PDF (--no-compile).")
        return

    try:
        pdf_path = compile_tex(out_path, args.latex_engine)
    except (OSError, RuntimeError) as e:
        print(f"PDF build failed: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    final_pdf = pdf_dir / pdf_path.name
    shutil.copy2(pdf_path, final_pdf)
    print(f"Built {final_pdf}")


if __name__ == "__main__":
    main()
