FROM python:3.7-alpine

ARG PYPI_VERSION

RUN \
# Check for mandatory build arguments
    : "${PYPI_VERSION:?Build argument needs to be set and non-empty.}"

RUN apk add gcc musl-dev && \
    python3 -m pip install -q --upgrade pip && \
    python3 -m pip install -q neoload==$PYPI_VERSION
