FROM python:3.9-alpine

ENV CELERY_BROKER_URL amqp://rabbitmq:5672
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

ENV HOST 0.0.0.0
ENV PORT 8081
ENV DEBUG True

COPY . /api
WORKDIR /api

RUN pip install -U setuptools pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
