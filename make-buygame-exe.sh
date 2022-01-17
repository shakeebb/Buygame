#!/bin/bash


version=0.2
rm pyi-buygame-win.spec
rm buygame-${version}.exe

pyi-makespec.exe -w -F --paths venv/Lib/site-packages --paths gui --paths common --add-data "gui\tiles;gui\tiles" buygame.py -n pyi-buygame-win

pyinstaller --clean ./pyi-buygame-win.spec

mv dist/pyi-buygame-win.exe buygame-${version}.exe

echo "Buygame binary buygame-${version}.exe successfully created"
