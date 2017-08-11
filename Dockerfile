FROM jfloff/alpine-python:2.7-slim

WORKDIR /usr/local/bin

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

ENV LISTENPORT 8601
ENV IP 192.168.1.34
ENV FREQUENCY 1
ENV VERSION 0.46

ADD claymore-exporter.py .
ADD entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8601

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

