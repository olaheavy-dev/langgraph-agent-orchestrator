"""Settings, read once from the environment.

Everything configurable lives here rather than being read from os.environ at the
point of use, so the set of knobs is one file long and a missing key fails at
startup rather than three requests later.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='ORCHESTRATOR_', extra='ignore')

    model: str = 'openai:gpt-4.1-mini'
    embedding_model: str = 'openai:text-embedding-3-small'

    # Where the coding agent is allowed to work. Nothing outside this directory
    # is readable or writable -- see app.tools.workspace for the enforcement.
    workspace_root: Path = BACKEND_ROOT / 'workspace'

    # Durable rather than in-memory: an interrupt suspends a graph between two
    # HTTP requests, so the checkpoint has to outlive the request that created
    # it and be visible to whichever worker handles the resume.
    checkpoint_path: Path = BACKEND_ROOT / 'data' / 'checkpoints.sqlite'

    cors_origins: list[str] = Field(default_factory=lambda: ['http://localhost:3000'])

    # How many corpus chunks a retrieval returns. Three is enough to cover a
    # question that spans two documents without burying the answer.
    retrieve_count: int = 4

    # 'structured' asks one model call for complete file contents. 'claude_code'
    # delegates to the Claude Code CLI in a disposable copy of the workspace.
    # Both produce a proposal; neither may write to the workspace.
    code_agent: Literal['structured', 'claude_code'] = 'structured'
    code_agent_timeout: int = 600


@lru_cache
def get_settings() -> Settings:
    return Settings()
