FROM python:3.12-slim

ENV CI=true

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CEREBRO_DATA_DIR=/data

# libgomp is required by LightGBM at runtime (OpenMP threading).
# python-multipart is required by FastAPI for multipart/form-data uploads.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY schemas ./schemas

# Install API surface + full ML stack so the /ingest endpoint can run
# extraction server-side without requiring a local Python environment.
RUN uv sync --frozen --no-dev --extra api --extra ml

RUN mkdir -p /data/artifacts /data/logs
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "cerebro.api.app:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--log-level", "info"]
