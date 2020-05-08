#!/bin/bash
set -e

version_id=$1

if [ -z "$version_id" ]; then
    echo "No version found"
    exit 1
fi

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
