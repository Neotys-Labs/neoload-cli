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

#TODO: run this script with a new version number. afterwards, run Azure job and ensure JSON schema validation
echo "Waiting for < 1m after publishing to PyPi"
sleep 30 # allow for some time on pypi

docker build --build-arg PYPI_VERSION=$version_id -t neoload-cli --file resources/docker-neoload-cli/Dockerfile .
if [ "$?" -ne "0" ]; then
  echo "Docker-minimalist build failed"
  exit 6
fi
docker run --rm neoload-cli neoload --version
if [ "$?" -ne "0" ]; then
  echo "Docker-minimalist image failed"
  exit 7
fi
docker tag neoload-cli paulsbruce/neoload-cli:$version_id
docker push paulsbruce/neoload-cli:$version_id
if [ "$?" -ne "0" ]; then
  echo "Docker-minimalist push failed"
  exit 8
fi
docker rmi neoload-cli
