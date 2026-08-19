# uv rather than pip: the workspace sandbox is a second project with its own
# lockfile, and the coding agent shells out to `uv run` to check its own work.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /srv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependencies first, so editing application code does not re-resolve them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY app ./app
COPY workspace ./workspace
RUN uv sync --frozen

# The sandbox's own environment, so run_checks() can lint and test the agent's
# work the same way its CI would.
RUN cd workspace && uv sync --frozen --extra dev

# Checkpoints and published pull requests live here. Declared as a volume so an
# approval survives a container restart -- an interrupt that outlives the request
# is only durable if its storage is.
RUN mkdir -p /srv/data
VOLUME /srv/data

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
