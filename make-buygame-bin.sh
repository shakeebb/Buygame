#!/bin/bash

version=0.5

[[ -d build ]] && rm -r build
[[ -d dist ]] && rm -r dist

if [[ "`uname`" =~ "MINGW64" ]]; then
  [[ -f pyi-buygame-win.spec ]] && rm pyi-buygame-win.spec 
  [[ -f buygame-${version}.exe ]] && rm buygame-${version}.exe

  pyi-makespec.exe -w -F --paths venv/Lib/site-packages --paths gui --path gui/login --path gui/survey --path gui/gui_common --paths common --add-data "gui\tiles;gui\tiles" buygame.py -n pyi-buygame-win

  pyinstaller --clean ./pyi-buygame-win.spec

  [[ -d dist ]] && mv dist/pyi-buygame-win.exe buygame-${version}.exe
  echo "Buygame binary buygame-${version}.exe successfully created"

elif [[ "`uname`" =~ "Darwin" ]]; then
#  [[ -f pyi-buygame-mac.spec ]] && rm pyi-buygame-mac.spec 
  [[ -d buygame-${version}-mac.app ]] && rm -r buygame-${version}-mac.app

#  pyi-makespec -w -F --paths venv/Lib/site-packages --paths gui --path gui/login --path gui/survey --path gui/gui_common --paths common --add-data "gui/tiles:gui/tiles" buygame.py --windowed --onefile -n pyi-buygame-mac

  pyinstaller --clean ./pyi-buygame-mac.spec

  [[ -d dist ]] && mv dist/pyi-buygame-mac.app buygame-${version}-mac.app
  echo "Buygame binary buygame-${version}-mac.app successfully created"
fi


