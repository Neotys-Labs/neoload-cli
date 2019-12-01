#!/bin/bash

version_id=$(cat ./setup.py | grep -oE "(?:version=')(.*?)(?:')")
version_id=$(echo "${version_id/version=/}")
version_id=$(echo "${version_id//\'/}")

if [ -z "$version_id" ]; then
    echo "No version found"
    exit 1
fi

python3 -m pytest tests -v --runslow
if [ "$?" -ne "0" ]; then
    echo "One or more tests failed."
    exit 2
fi

#rm -rf dist/*
python setup.py sdist bdist_wheel
if [ "$?" -ne "0" ]; then
    echo "Packaging to wheel step failed"
    exit 3
fi

twine check dist/*
if [ "$?" -ne "0" ]; then
  echo "Checks on wheel failed"
  exit 4
fi

twine upload dist/*$version_id*
if [ "$?" -ne "0" ]; then
  echo "Twine upload failed"
  exit 5
fi
