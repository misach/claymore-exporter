FROM jfloff/alpine-python:2.7-slim

WORKDIR /usr/local/bin

RUN pip install prometheus_client

ENV LISTENPORT 8601
ENV IP 192.168.1.34
ENV FREQUENCY 1
ENV VERSION 0.4

ADD claymore-exporter.py .
ADD entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8601

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

