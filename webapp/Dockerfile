FROM python:3.12-alpine

LABEL name="pwmgr-webapp"
LABEL maintainer="schnitz81"
LABEL description="This is webapp for pwmgr."
LABEL url="https://github.com/schnitz81/pwmgr"

RUN apk --no-cache update && apk add --no-cache xterm bash openssl netcat-openbsd ncurses  \
    && wget -O /usr/local/bin/pwmgr https://raw.githubusercontent.com/schnitz81/pwmgr/main/client/pwmgr.sh  \
    && chmod +x /usr/local/bin/pwmgr  \
    && mkdir /pwmgr-webapp

WORKDIR /pwmgr-webapp
COPY requirements.txt /pwmgr-webapp/
COPY *.py /pwmgr-webapp/
COPY static /pwmgr-webapp/static
COPY templates /pwmgr-webapp/templates
RUN pip install -U pip  \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8888

ENTRYPOINT ["python","-u","main.py"]

# build:
# docker build . -t pwmgr-webapp

# run:
# docker run -d -p 8888:8888 --name pwmgr-webapp pwmgr-webapp
