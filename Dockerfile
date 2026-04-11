FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    TERM=xterm-256color \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

COPY pyproject.toml README_PYPI.md ./
COPY password_manager ./password_manager

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir . \
    && pip install --no-cache-dir "textual-serve>=1.1.0,<2"

COPY packaging/docker/irondome_serve_web.py /usr/local/bin/irondome-serve-web.py
RUN chmod +x /usr/local/bin/irondome-serve-web.py

WORKDIR /root

EXPOSE 8000

CMD ["irondome"]
