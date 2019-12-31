FROM python:3.7-alpine

ARG PYPI_VERSION

RUN \
# Check for mandatory build arguments
    : "${PYPI_VERSION:?Build argument needs to be set and non-empty.}"

RUN apk add gcc musl-dev && \
    python3 -m pip install -q --upgrade pip && \
    python3 -m pip install -q neoload==$PYPI_VERSION


# for use in CI with a build agent that is a docker host (or connected to one)
FROM docker:dind

RUN apk add -q bash shadow git
