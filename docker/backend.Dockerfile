# docker/backend.Dockerfile — PLACEHOLDER.
# Proves the build step is wired and the package installs on a slim base.
# The real multi-stage build (builder + slim runtime, non-root, healthcheck,
# uvicorn CMD) and digest-pinned bases land alongside the API layer.
FROM python:3.12-slim

# uv pinned by version (pin by digest when the build is hardened).
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CEREBRO_DATA_DIR=/data

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Runtime deps only (core: pydantic + structlog). No dev, no heavy ML extra.
RUN uv sync --frozen --no-dev

RUN mkdir -p /data/artifacts /data/logs
EXPOSE 8000

# Placeholder: the FastAPI app and uvicorn CMD arrive with the API layer. For
# now, prove the package imports inside the image.
CMD ["uv", "run", "python", "-c", "import cerebro; print('cerebro', cerebro.__version__)"]
