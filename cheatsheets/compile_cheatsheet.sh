#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p build generated
# Aux/log/pdf written under build/; only cheatsheet.pdf copied to generated/
lualatex -synctex=0 -interaction=nonstopmode -file-line-error -halt-on-error -output-directory=build main.tex
lualatex -synctex=0 -interaction=nonstopmode -file-line-error -halt-on-error -output-directory=build main.tex
cp -f build/main.pdf generated/cheatsheet.pdf
echo "Wrote $ROOT/generated/cheatsheet.pdf"
