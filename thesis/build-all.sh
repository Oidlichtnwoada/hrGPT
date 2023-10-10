#!/bin/sh

CLASS=thesisclass
SOURCE=thesis

# Build thesisclass documentation
pdflatex $CLASS.dtx
pdflatex $CLASS.dtx
makeindex -s gglo.ist -o $CLASS.gls $CLASS.glo
makeindex -s gind.ist -o $CLASS.ind $CLASS.idx
pdflatex $CLASS.dtx
pdflatex $CLASS.dtx

# Build the thesisclass class file
pdflatex $CLASS.ins

echo
echo
echo Class file compiled.

# Build the thesisclass example document
source build-thesis.sh
