#!/bin/bash
WS='/mnt/d/Education/03- PhD/02- TCD/Code/PR/littledarwin'
cd "$WS"
git add -A
git commit -F - <<'MSG'
refactor: rename package from littledarwin to mediumdarwin

Rename the Python package directory and all internal import references:
- Rename littledarwin/ directory to mediumdarwin/
- Rename LittleDarwin.py entry-point to MediumDarwin.py
- Update all `from littledarwin.` imports to `from mediumdarwin.`
- Update setup.py package name and description
- Update __init__.py __package__ and __main__.py references

This is the foundational rename PR; all subsequent feature PRs will
build on top of this package structure.
MSG
echo "Commit done."
git log --oneline -3
