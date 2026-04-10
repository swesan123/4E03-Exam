from __future__ import annotations

import random
import re
from typing import Any


def count_letter_subparts(body_plain: str) -> int:
    """Count lines like '(a)' … '(z)' as sub-parts (common in T/F lists)."""
    return len(re.findall(r"^\s*\([a-z]\)", body_plain, flags=re.MULTILINE))


def usage_count(usage: dict[str, Any], qid: str) -> int:
    rec = usage.get(qid)
    if not rec:
        return 0
    if isinstance(rec, dict):
        return int(rec.get("count", 0))
    return int(rec)


def weighted_pick_without_replacement(
    pool: list[dict],
    usage: dict[str, Any],
    k: int,
    rng: random.Random,
) -> list[dict]:
    pool = list(pool)
    picked: list[dict] = []
    for _ in range(k):
        if not pool:
            break
        weights = [1.0 / (1 + usage_count(usage, q["id"])) for q in pool]
        choice = rng.choices(pool, weights=weights, k=1)[0]
        picked.append(choice)
        pool.remove(choice)
    return picked


def allocate_category_quotas(n: int, counts: dict[str, int]) -> dict[str, int]:
    """
    Split n picks across test1, test2, newer as evenly as possible, capped by availability.
    Empty categories get 0; remaining share goes to others.
    """
    cats = ("test1", "test2", "newer")
    quotas = {c: 0 for c in cats}
    nonempty = [c for c in cats if counts.get(c, 0) > 0]
    if not nonempty:
        return quotas
    m = len(nonempty)
    base, rem = divmod(n, m)
    for i, c in enumerate(nonempty):
        want = base + (1 if i < rem else 0)
        quotas[c] = min(want, counts[c])

    deficit = n - sum(quotas.values())
    while deficit > 0:
        progressed = False
        for c in nonempty:
            if deficit <= 0:
                break
            spare = counts[c] - quotas[c]
            if spare > 0:
                take = min(spare, deficit)
                quotas[c] += take
                deficit -= take
                progressed = True
        if not progressed:
            break
    return quotas


def pick_stratified_calc(
    calc_by_cat: dict[str, list[dict]],
    usage: dict[str, Any],
    n: int,
    rng: random.Random,
) -> list[dict]:
    counts = {c: len(calc_by_cat.get(c, [])) for c in ("test1", "test2", "newer")}
    if sum(counts.values()) < n:
        raise ValueError(f"Need at least {n} calculation questions; have {sum(counts.values())}.")

    empty = [c for c in ("test1", "test2", "newer") if counts[c] == 0]
    if empty:
        import sys

        print(
            f"Warning: no calculation questions tagged {', '.join(empty)}; "
            "redistributing picks across remaining categories.",
            file=sys.stderr,
        )

    quotas = allocate_category_quotas(n, counts)
    picked: list[dict] = []
    for c in ("test1", "test2", "newer"):
        need = quotas[c]
        pool = calc_by_cat.get(c, [])
        picked.extend(weighted_pick_without_replacement(pool, usage, need, rng))

    deficit = n - len(picked)
    if deficit > 0:
        remaining: list[dict] = []
        picked_ids = {q["id"] for q in picked}
        for c in ("test1", "test2", "newer"):
            for q in calc_by_cat.get(c, []):
                if q["id"] not in picked_ids:
                    remaining.append(q)
        picked.extend(weighted_pick_without_replacement(remaining, usage, deficit, rng))

    if len(picked) < n:
        raise RuntimeError("Could not fill calculation quota; bank too small after stratification.")

    rng.shuffle(picked)
    return picked


def pick_tf_question(
    tf_pool: list[dict],
    usage: dict[str, Any],
    rng: random.Random,
    min_subparts: int,
) -> dict:
    if not tf_pool:
        raise ValueError("No True/False questions in bank.")

    ranked = sorted(
        tf_pool,
        key=lambda q: count_letter_subparts(q["body_plain"]),
        reverse=True,
    )
    best_n = count_letter_subparts(ranked[0]["body_plain"])
    threshold = min(min_subparts, best_n)
    eligible = [q for q in tf_pool if count_letter_subparts(q["body_plain"]) >= threshold]
    if not eligible:
        eligible = tf_pool
    chosen = weighted_pick_without_replacement(eligible, usage, 1, rng)
    return chosen[0]
