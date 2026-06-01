# docker/Dockerfile — production single-image build.
#
# Produces one image that serves both the static UI (via nginx on :80) and
# the FastAPI backend (uvicorn on :8000 internally). supervisord keeps both
# processes alive.  Users need only:
#
#   docker run -p 8080:80 -v ./data:/data ghcr.io/dgtalbug/cerebro:latest
#
# Build stages:
#   ui-builder   — Node 22 / pnpm — compiles the Vite SPA to /build/dist
#   final        — python:3.12-slim + nginx + supervisord + uv

# ---- Stage 1: UI build -------------------------------------------------------
FROM node:22-alpine AS ui-builder

ENV CI=true

RUN npm install -g pnpm@11.1.2

WORKDIR /build
COPY ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts

COPY ui/ ./

# VITE_API_URL must be /api so nginx can proxy it to localhost:8000
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

# ---- Stage 2: final image ----------------------------------------------------
FROM python:3.12-slim AS final

ENV CI=true

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CEREBRO_DATA_DIR=/data

# nginx  — serves static UI and reverse-proxies /api/
# supervisor — PID 1 process manager for nginx + uvicorn
# libgomp1 — LightGBM runtime (OpenMP threading)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       nginx \
       supervisor \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY schemas ./schemas
RUN uv sync --frozen --no-dev --extra api --extra ml

# Static UI assets
COPY --from=ui-builder /build/dist /usr/share/nginx/html

# nginx: proxy /api/ → localhost:8000 (not a separate container)
COPY docker/nginx-single.conf /etc/nginx/conf.d/default.conf
# Remove default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

# supervisord: manages nginx + uvicorn under a single PID 1
COPY docker/supervisord.conf /etc/supervisor/conf.d/cerebro.conf

# Persistent data directory
RUN mkdir -p /data/artifacts /data/logs

# Only port 80 is exposed — nginx is the single entry point
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/cerebro.conf"]
