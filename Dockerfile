# syntax=docker/dockerfile:1.4
FROM python:3.12-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# postgresql-devel

ENV PROJECT_NAME=asset-docs-integration
ENV PROJECT_ROOT=/opt/asset-docs-integration
ENV VIRTUAL_ENV=/opt/asset-docs-integration/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV UV_LINK_MODE=copy

WORKDIR $PROJECT_ROOT/

# Stage 1: install dependencies (cached when only source files change)
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Stage 2: install the project itself
COPY asset_docs_integration ./asset_docs_integration/
COPY tests ./tests/
COPY conftest.py ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# ARGs go HERE, not at the top — declaring an ARG invalidates every layer
# below it whenever the build-arg changes, so keep them just above the
# LABELs that consume them.
ARG GIT_COMMIT=unknown
ARG GIT_REF=unknown
ARG BUILD_DATE=unknown
ARG VERSION=0.0.1

LABEL org.opencontainers.image.title="asset-docs-integration"
LABEL org.opencontainers.image.description="Integration tasks for asset docs"
LABEL org.opencontainers.image.authors="Josh Rhoades <dev@axiomdatascience.com>"
LABEL org.opencontainers.image.url="https://git.axiom/axiom/asset-docs-integration/"
LABEL org.opencontainers.image.source="https://git.axiom/axiom/asset-docs-integration/"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.ref.name="${GIT_REF}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"

FROM base AS develop

RUN apt-get update && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra test --extra dev
