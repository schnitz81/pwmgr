FROM python:3.11-alpine

LABEL name="pwmgr-server"
LABEL maintainer="schnitz81"
LABEL description="Server for pwmgr, a centralized password manager with distributed encryption."
LABEL url="https://github.com/schnitz81/pwmgr"

RUN apk update --no-cache \
&& apk add --no-cache bash coreutils \
#&& ls /usr/share/zoneinfo && cp /usr/share/zoneinfo/Europe/Stockholm /etc/localtime && echo "Europe/Stockholm" > /etc/timezone \
#&& mkdir /pwmgr
# curl grep gcc gfortran build-base zlib zlib-dev jpeg libjpeg jpeg-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev tzdata font-opensans

ADD *.py /pwmgr/

WORKDIR /pwmgr
#RUN pip install -U pip \
#&& pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python","-u","main.py"]

# build:
# docker build . -t pwmgr

# run:
# docker run --name pwmgr-server --restart unless-stopped -d -p 48222:48222 pwmgr
