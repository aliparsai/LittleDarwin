#!/bin/bash
set -e

WS='/mnt/d/Education/03- PhD/02- TCD/Code/PR/littledarwin'
cd "$WS"

# Fix imports from littledarwin to mediumdarwin
for f in mediumdarwin/LittleDarwin.py mediumdarwin/__main__.py MediumDarwin.py tests/test_LittleDarwin.py setup.py; do
  sed -i 's/from littledarwin import/from mediumdarwin import/g' "$f"
  sed -i 's/import littledarwin\./import mediumdarwin./g' "$f"
done

# Fix __package__ in __init__.py
sed -i "s/__package__ = 'littledarwin'/__package__ = 'mediumdarwin'/g" mediumdarwin/__init__.py

# Fix program name in LittleDarwin.py
sed -i 's/prog="littledarwin"/prog="mediumdarwin"/g' mediumdarwin/LittleDarwin.py

# Fix setup.py name
sed -i "s/name='littledarwin'/name='mediumdarwin'/g" setup.py
sed -i "s/description=\"LittleDarwin/description=\"MediumDarwin/g" setup.py
sed -i "s/console_scripts': \['littledarwin/console_scripts': ['mediumdarwin/g" setup.py

echo "All imports and names fixed."
