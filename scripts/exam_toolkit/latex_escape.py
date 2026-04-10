import re

# Private-use glyphs (e.g. PDF matrix bracket pieces) are not valid in pdfLaTeX utf8.
_PUA_BMP = re.compile("[\uE000-\uF8FF]")
_PUA_SUPPLEMENT = re.compile("[\U000F0000-\U000FFFFD\U00100000-\U0010FFFD]")


def strip_private_use_for_latex(s: str) -> str:
    s = _PUA_BMP.sub(" ", s)
    s = _PUA_SUPPLEMENT.sub(" ", s)
    return s


def latex_escape_plain(s: str) -> str:
    """Escape plain text for LaTeX body (minimal; review math-heavy output)."""
    s = strip_private_use_for_latex(s)
    out: list[str] = []
    for ch in s:
        if ch == "\\":
            out.append(r"\textbackslash{}")
        elif ch == "{":
            out.append(r"\{")
        elif ch == "}":
            out.append(r"\}")
        elif ch == "$":
            out.append(r"\$")
        elif ch == "&":
            out.append(r"\&")
        elif ch == "#":
            out.append(r"\#")
        elif ch == "_":
            out.append(r"\_")
        elif ch == "%":
            out.append(r"\%")
        elif ch == "~":
            out.append(r"\textasciitilde{}")
        elif ch == "^":
            out.append(r"\textasciicircum{}")
        else:
            out.append(ch)
    return "".join(out)


