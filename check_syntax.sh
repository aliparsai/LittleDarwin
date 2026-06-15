#!/bin/bash
WS='/mnt/d/Education/03- PhD/02- TCD/Code/PR/littledarwin'
cd "$WS"
for f in MediumDarwin.py mediumdarwin/LittleDarwin.py mediumdarwin/__init__.py mediumdarwin/__main__.py setup.py tests/test_LittleDarwin.py tests/test_JavaParse.py; do
  python3 -c "import ast; ast.parse(open('$f').read())" && echo "$f: OK" || echo "$f: FAIL"
done
