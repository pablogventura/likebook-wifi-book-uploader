#!/bin/bash
# Publish likebook-wifi-book-uploader to PyPI
# Requires: pip install build twine
# PyPI token: Create at https://pypi.org/manage/account/token/

set -e
cd "$(dirname "$0")"

echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

echo "Building package..."
python -m build

if [[ "$1" == "--test" ]]; then
    echo "Uploading to Test PyPI..."
    python -m twine upload --repository testpypi dist/*
else
    echo "Uploading to PyPI..."
    python -m twine upload dist/*
fi

echo "Done."
