FROM docker:dind

RUN apk add -q bash shadow git py-pip py3-setuptools build-base python3-dev \
    && python3 -m pip install -q --upgrade pip

RUN python3 -m pip install -q neoload
