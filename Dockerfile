FROM python:3.13-alpine

LABEL name="pwmgr-server"
LABEL maintainer="schnitz81"
LABEL description="Server for pwmgr, a centralized password manager with distributed encryption."
LABEL url="https://github.com/schnitz81/pwmgr"

RUN apk --no-cache update && apk add --no-cache openssl \
    && mkdir /pwmgr \
    && mkdir /db

ADD *.py /pwmgr/

# replace config with Docker-version
RUN mv /pwmgr/config-docker.py /pwmgr/config.py

WORKDIR /pwmgr
ENTRYPOINT ["python","-u","main.py"]

# build:
# docker build . -t pwmgr-server

# run:
# docker run --name pwmgr-server --restart unless-stopped -d -v /path/to/db-store:/db -p 48222:48222 pwmgr-server
