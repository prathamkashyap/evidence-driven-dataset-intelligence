#!/bin/sh
set -eu
cd "$(dirname "$0")"
latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex
