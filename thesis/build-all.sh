#!/bin/sh
# Copyright (C) 2014-2023 by Thomas Auzinger <thomas@auzinger.name>

CLASS=vutinfth
SOURCE=thesis

# Build vutinfth documentation
pdflatex $CLASS.dtx
pdflatex $CLASS.dtx
makeindex -s gglo.ist -o $CLASS.gls $CLASS.glo
makeindex -s gind.ist -o $CLASS.ind $CLASS.idx
pdflatex $CLASS.dtx
pdflatex $CLASS.dtx

# Build the vutinfth class file
pdflatex $CLASS.ins

echo
echo
echo Class file compiled.

# Build the vutinfth example document
source build-thesis.sh
