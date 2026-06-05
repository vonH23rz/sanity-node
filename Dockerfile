FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SANITY_NODE_OUTPUT=/app/html/index.html
ENV SANITY_NODE_SSH_USER=truenas_admin
ENV SANITY_NODE_SSH_KEY=/app/ssh/id_ed25519
ENV SANITY_NODE_REFRESH_SECONDS=300
ENV SANITY_NODE_PORT=8099

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY scripts/ /app/scripts/
COPY web/ /app/web/

RUN chmod +x /app/scripts/generate-dashboard.py \
    && chmod +x /app/scripts/docker-entrypoint.sh

VOLUME ["/app/config", "/app/ssh", "/app/html", "/app/logs"]

EXPOSE 8099

HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${SANITY_NODE_PORT}/" || exit 1

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
