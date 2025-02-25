FROM python:3.13.2-slim
LABEL maintainer="kashpur.v.f@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /uploads

RUN adduser \
    --disabled-password \
    --no-create-home \
    my_user

RUN chown -R my_user /uploads
RUN chmod -R 755 /uploads

USER my_user
