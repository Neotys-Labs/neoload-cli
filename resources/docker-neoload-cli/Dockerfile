FROM python:3.7-alpine

ARG PYPI_VERSION

RUN \
# Check for mandatory build arguments
    : "${PYPI_VERSION:?Build argument needs to be set and non-empty.}"

# add GCC deps, Python, and NeoLoad
RUN apk add -q gcc musl-dev && \
    python3 -m pip install -q --upgrade pip && \
    python3 -m pip install --index-url https://test.pypi.org/simple/ \
                           --upgrade --no-cache-dir -q \
                           --extra-index-url=https://pypi.org/simple/ \
                           neoload==$PYPI_VERSION
