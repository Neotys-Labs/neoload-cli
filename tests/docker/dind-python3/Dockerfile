FROM docker:dind

RUN apk --update add bash shadow
RUN groupadd docker && usermode -aG docker 'jenkins'
RUN chmod 777 /var/run/docker.sock

RUN apk add --no-cache bash git

RUN apk add --update --no-cache py-pip py3-setuptools

RUN apk add -q build-base python2-dev python3-dev

RUN python3 -m pip install -q --upgrade pip
