"""LaTeX preamble snippets for generated practice exams."""

from __future__ import annotations

# pdflatex cannot read arbitrary Unicode (e.g. Greek) with inputenc alone; map common symbols.
_PDFLATEX_UNICODE: list[tuple[str, str]] = [
    ("λ", r"\ensuremath{\lambda}"),
    ("μ", r"\ensuremath{\mu}"),
    ("µ", r"\ensuremath{\mu}"),
    ("α", r"\ensuremath{\alpha}"),
    ("β", r"\ensuremath{\beta}"),
    ("γ", r"\ensuremath{\gamma}"),
    ("δ", r"\ensuremath{\delta}"),
    ("ε", r"\ensuremath{\varepsilon}"),
    ("ζ", r"\ensuremath{\zeta}"),
    ("η", r"\ensuremath{\eta}"),
    ("θ", r"\ensuremath{\theta}"),
    ("ι", r"\ensuremath{\iota}"),
    ("κ", r"\ensuremath{\kappa}"),
    ("ν", r"\ensuremath{\nu}"),
    ("ξ", r"\ensuremath{\xi}"),
    ("π", r"\ensuremath{\pi}"),
    ("ρ", r"\ensuremath{\rho}"),
    ("σ", r"\ensuremath{\sigma}"),
    ("τ", r"\ensuremath{\tau}"),
    ("φ", r"\ensuremath{\phi}"),
    ("χ", r"\ensuremath{\chi}"),
    ("ψ", r"\ensuremath{\psi}"),
    ("ω", r"\ensuremath{\omega}"),
    ("Ω", r"\ensuremath{\Omega}"),
    ("Λ", r"\ensuremath{\Lambda}"),
    ("≤", r"\ensuremath{\leq}"),
    ("≥", r"\ensuremath{\geq}"),
    ("×", r"\ensuremath{\times}"),
    ("·", r"\ensuremath{\cdot}"),
    ("−", r"\ensuremath{-}"),
    ("∞", r"\ensuremath{\infty}"),
    ("∼", r"\ensuremath{\sim}"),
    ("≈", r"\ensuremath{\approx}"),
    ("≠", r"\ensuremath{\neq}"),
    ("±", r"\ensuremath{\pm}"),
    ("→", r"\ensuremath{\rightarrow}"),
    ("←", r"\ensuremath{\leftarrow}"),
    ("⇒", r"\ensuremath{\Rightarrow}"),
    ("∈", r"\ensuremath{\in}"),
    ("∀", r"\ensuremath{\forall}"),
    ("∃", r"\ensuremath{\exists}"),
    ("∂", r"\ensuremath{\partial}"),
    ("∑", r"\ensuremath{\sum}"),
    ("∏", r"\ensuremath{\prod}"),
    ("∫", r"\ensuremath{\int}"),
    ("√", r"\ensuremath{\sqrt{\,}}"),
    ("⊂", r"\ensuremath{\subset}"),
    ("∪", r"\ensuremath{\cup}"),
    ("∩", r"\ensuremath{\cap}"),
    ("⊆", r"\ensuremath{\subseteq}"),
    ("⊇", r"\ensuremath{\supseteq}"),
    ("∅", r"\ensuremath{\emptyset}"),
    ("∗", r"\ensuremath{\ast}"),
]


def document_start_lines(latex_engine: str) -> list[str]:
    eng = latex_engine.lower().strip()
    if eng == "lualatex":
        return [
            "% !TEX program = lualatex",
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage{amsmath}",
            r"\usepackage{fvextra}",
            r"\begin{document}",
        ]
    if eng == "xelatex":
        return [
            "% !TEX program = xelatex",
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage{fontspec}",
            r"\defaultfontfeatures{Ligatures=TeX}",
            r"\usepackage{amsmath}",
            r"\usepackage{fvextra}",
            r"\begin{document}",
        ]
    if eng == "pdflatex":
        lines = [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{amsmath}",
            r"\usepackage{newunicodechar}",
            r"\usepackage{fvextra}",
        ]
        for ch, repl in _PDFLATEX_UNICODE:
            lines.append(f"\\newunicodechar{{{ch}}}{{{repl}}}")
        lines.append(r"\begin{document}")
        return lines
    raise ValueError(
        f"Unsupported --latex-engine {latex_engine!r} (use lualatex, pdflatex, or xelatex)"
    )
