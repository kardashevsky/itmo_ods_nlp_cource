FROM python:3.11-slim

ENV CELERY_BROKER_URL amqp://rabbitmq:5672
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install -U setuptools pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /worker