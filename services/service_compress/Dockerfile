FROM python:3.9-slim

ENV CELERY_BROKER_URL amqp://rabbitmq:5672
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install -U setuptools pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /worker