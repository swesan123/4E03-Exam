import re

PAGE_FOOTER_RE = re.compile(r"^\s*--\s*\d+\s+of\s+\d+\s+--\s*$")
# Page numbers as a single 1–2 digit line (sample PDF uses 1–6).
LONE_PAGE_NUM_RE = re.compile(r"^\s*\d{1,2}\s*$")
# Only left-margin numbered lines (0–2 leading spaces). Avoids wrapped T/F lines like
# "    23. The average response time..." inside part (f).
QUESTION_START_RE = re.compile(r"^ {0,2}(\d+)\.\s+(.*)$")


def strip_pdf_artifacts(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if PAGE_FOOTER_RE.match(line):
            continue
        if LONE_PAGE_NUM_RE.match(line):
            continue
        out.append(line)
    return out


def normalize_raw_text(raw: str) -> list[str]:
    text = raw.replace("\f", "\n")
    lines = text.splitlines()
    return strip_pdf_artifacts(lines)


def trim_before_first_question(lines: list[str]) -> list[str]:
    """Drop title/header lines until the first 'N. ' question line."""
    start = 0
    for i, line in enumerate(lines):
        if QUESTION_START_RE.match(line):
            start = i
            break
    return lines[start:]


def segment_questions(lines: list[str]) -> list[tuple[int, str]]:
    """Return (pdf_number, body) for each top-level question."""
    segments: list[tuple[int, str]] = []
    current_num: int | None = None
    current_lines: list[str] = []

    for line in lines:
        m = QUESTION_START_RE.match(line)
        if m:
            if current_num is not None:
                body = "\n".join(current_lines).strip()
                if body:
                    segments.append((current_num, body))
            current_num = int(m.group(1))
            rest = m.group(2).rstrip()
            current_lines = [rest] if rest else []
        elif current_num is not None:
            current_lines.append(line.rstrip())

    if current_num is not None:
        body = "\n".join(current_lines).strip()
        if body:
            segments.append((current_num, body))

    return segments


def is_true_false_question(body_plain: str) -> bool:
    """
    True when the stem (first line of body) introduces a True/False block.
    Excludes questions like Q8 where (a) is a calculation and (b) is T/F.
    """
    first = body_plain.strip().split("\n", 1)[0].strip()
    fl = first.lower()
    if fl.startswith("true or false"):
        return True
    if fl.startswith("true/false"):
        return True
    if fl.startswith("answer true or false"):
        return True
    return False
