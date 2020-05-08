#!/bin/bash
set -e

version_id=$(cat ./setup.py | grep -oE "(?:version=')(.*?)(?:')")
version_id=$(echo "${version_id/version=/}")
version_id=$(echo "${version_id//\'/}")

if [ -z "$version_id" ]; then
    echo "No version found"
    exit 1
fi

echo "Testing and packaging version $version_id"

python3 -m pytest tests -v
if [ "$?" -ne "0" ]; then
    echo "One or more tests failed."
    exit 2
fi

#rm -rf dist/*
## python3 -m pip install --user --upgrade setuptools wheel
python setup.py sdist bdist_wheel
if [ "$?" -ne "0" ]; then
    echo "Packaging to wheel step failed"
    exit 3
fi

## python3 -m pip install --user --upgrade twine
## echo 'export PATH="/Users/paul/.local/bin:$PATH"' >> ~/.bash_profile
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

#TODO: run this script with a new version number. afterwards, run Azure job and ensure JSON schema validation
echo "Waiting for < 1m after publishing to Dockerhub >> Pypi latest version dependency"
sleep 300 # allow for some time on pypi

./dockerhub.sh $version_id
