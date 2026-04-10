from __future__ import annotations

from pathlib import Path
from typing import Any

VALID = frozenset({"test1", "test2", "newer"})


def load_question_tags(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise RuntimeError("PyYAML is required to read question_tags.yaml") from e

    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping of id -> category")
    out: dict[str, str] = {}
    for k, v in data.items():
        if v is None:
            continue
        cat = str(v).strip()
        if cat not in VALID:
            raise ValueError(f"Invalid category for {k!r}: {cat!r} (use test1, test2, newer)")
        out[str(k)] = cat
    return out


def effective_category(question: dict, tags: dict[str, str]) -> str:
    return tags.get(question["id"], question["category"])
