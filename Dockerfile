# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.4
FROM python:3.10-slim-bookworm as base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser


RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY ./bmgt435_elp ./bmgt435_elp
COPY ./sim_server_django ./sim_server_django
COPY ./manage.py ./manage.py
COPY ./static/admin ./static/admin

USER root
RUN mkdir /app/media
# give permissions to media folder which stores the detailed case records
RUN chown -R appuser /app/media
RUN chmod -R 700 /app/media
RUN python manage.py collectstatic --noinput
RUN chown -R appuser /app/static
RUN chmod -R -700 /app/static

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000
# Run the application with daphne asgi server

# CMD python manage.py makemigrations && python manage.py migrate && gunicorn -b 0.0.0.0:8000 sim_server_django.wsgi:application
CMD python manage.py makemigrations && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 sim_server_django.asgi:application
# CMD python manage.py makemigrations && python manage.py migrate && python manage.py runserver
