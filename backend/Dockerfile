FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY VERSION /app/VERSION
COPY backend /app/backend

RUN chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend

# TCP-level check only (not a full HTTP request) so it doesn't depend on curl/wget being present
# in the image, or on the request's Host header passing Django's ALLOWED_HOSTS check.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('127.0.0.1', 8000), 2).close()" || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
