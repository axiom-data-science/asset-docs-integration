[![Pipeline status](http://git.axiom/axiom/asset-docs-integration/badges/main/pipeline.svg)](http://git.axiom/axiom/asset-docs-integration/-/pipelines)

# asset-docs-integration

Integration tasks for asset docs

Copyright 2026 Axiom Data Science, LLC

See [LICENSE](LICENSE) for details.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

1. Install uv: <https://docs.astral.sh/uv/getting-started/installation/>.
2. Clone this project with `git`.
3. Install runtime + dev + test dependencies (creates `.venv/` and writes
   `uv.lock`):

   ```sh
   uv sync --extra test --extra dev
   ```

4. Activate the virtualenv (or prefix any command with `uv run`):

   ```sh
   source .venv/bin/activate
   ```

## Running tests

```sh
uv run pytest -sv --integration
```

## Usage

## Configuration

## Building with Docker

To build the docker image locally:

```sh
make docker-local
```

To run a built image:

```sh
docker run --rm asset-docs-integration:latest
```
