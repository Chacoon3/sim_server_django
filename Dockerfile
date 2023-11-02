# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.4
FROM python:3.10-slim-bookworm as BASE
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=0
ENV PYTHONUNBUFFERED=0

# Copy the source code into the container.
COPY ./bmgt435_elp ./bmgt435_elp
COPY ./sim_server_django ./sim_server_django
COPY ./manage.py ./manage.py

USER root
RUN mkdir /app/media && \
    chmod -R 700 /app/media && \
    mkdir /app/static && \
    chmod -R -700 /app/static &&\
    python manage.py collectstatic --noinput

EXPOSE 8000

# CMD python manage.py makemigrations && python manage.py migrate && gunicorn -b 0.0.0.0:8000 sim_server_django.wsgi:application
CMD python manage.py makemigrations bmgt435_elp && \
    python manage.py migrate && \
    daphne -b 0.0.0.0 -p 8000 sim_server_django.asgi:application
# CMD python manage.py makemigrations && python manage.py migrate && python manage.py runserver
