FROM python:3.7-alpine

ARG PYPI_VERSION

RUN \
# Check for mandatory build arguments
    : "${PYPI_VERSION:?Build argument needs to be set and non-empty.}"

RUN apk add -q gcc musl-dev python3-dev && \
    python3 -m pip install -q --upgrade pip && \
    python3 -m pip install -q neoload==$PYPI_VERSION


# for use in CI with a build agent that is a docker host (or connected to one)

RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-18.03.1-ce.tgz | \
    tar zxvf - --strip 1 -C /usr/bin docker/docker

RUN apk add -q bash shadow git
