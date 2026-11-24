# Assignments service image
FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Unprivileged user the service runs as
RUN useradd --create-home --uid 10001 appuser

# Dependencies first, so this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code, file by file (no COPY . .)
COPY app.py database.py assignment_service.py courses_client.py ./
COPY migrations/ ./migrations/

USER appuser

# DATABASE_URL is not set here: it holds a password and is given at runtime
ENV PORT=8000

EXPOSE 8000

# Shell form via sh -c so ${PORT} is expanded at runtime; exec makes gunicorn PID 1.
# --timeout 120: a request that has to wait for the paused Azure database to resume
# (the retries in database.py take up to about 100 s) must not be killed by gunicorn's
# default 30 s worker timeout.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 app:app"]
