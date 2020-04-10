FROM python:3.7-alpine

ARG PYPI_VERSION

RUN \
# Check for mandatory build arguments
    : "${PYPI_VERSION:?Build argument needs to be set and non-empty.}"

# add GCC deps, Python, and NeoLoad (to ensure installation from PyPi)
RUN apk add -q gcc musl-dev python3-dev curl && \
    python3 -m pip install -q --upgrade pip && \
    python3 -m pip install -q neoload==$PYPI_VERSION

# ADD DOCKER
# for use in CI with a build agent that is a docker host (or connected to one)
ENV DOCKERVERSION=18.03.1-ce
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
 && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 \
                -C /usr/local/bin docker/docker \
 && rm docker-${DOCKERVERSION}.tgz

RUN apk add -q bash shadow git
