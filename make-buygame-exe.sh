#!/bin/bash


rm pyi-buygame-win.spec
rm buygame.exe

pyi-makespec.exe -w -F --paths venv/Lib/site-packages --paths gui --paths common --add-data "gui\tiles;gui\tiles" buygame.py -n pyi-buygame-win

pyinstaller --clean ./pyi-buygame-win.spec

mv dist/pyi-buygame-win.exe buygame-0.1.exe

