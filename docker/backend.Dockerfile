FROM python:3.12-slim

ENV CI=true

COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CEREBRO_DATA_DIR=/data

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install core runtime + the API/CLI surface (fastapi, uvicorn, typer).
# The [ml] extra (lightgbm, shap, numpy) is intentionally excluded from
# the image — artifacts are extracted on the host and fed in via the
# mounted /data volume.
RUN uv sync --frozen --no-dev --extra api

RUN mkdir -p /data/artifacts /data/logs
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "cerebro.api.app:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--log-level", "info"]
