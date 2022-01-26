#!/bin/bash

version=0.2

if [[ "`uname`" =~ "MINGW64" ]]; then
  rm pyi-buygame-win.spec
  rm buygame-${version}.exe

  pyi-makespec.exe -w -F --paths venv/Lib/site-packages --paths gui --paths common --add-data "gui\tiles;gui\tiles" buygame.py -n pyi-buygame-win

  pyinstaller --clean ./pyi-buygame-win.spec

  mv dist/pyi-buygame-win.exe buygame-${version}.exe

elif [[ "`uname`" =~ "Darwin" ]]; then
  rm pyi-buygame-mac.spec
  rm buygame-${version}-mac
  rm -r dist/pyi-buygame-mac.app

 pyi-makespec -w -F --paths venv/Lib/site-packages --paths gui --paths common --add-data "gui/tiles:gui/tiles" buygame.py -n pyi-buygame-mac

  pyinstaller --clean ./pyi-buygame-mac.spec

  mv dist/pyi-buygame-mac buygame-${version}-mac
fi

echo "Buygame binary buygame-${version}.exe successfully created"

