import pytest
from fastapi.testclient import TestClient

KEY = 'test-key-aaa'
OTHER_KEY = 'test-key-bbb'


@pytest.fixture
def key() -> str:
    return KEY


@pytest.fixture
def other_key() -> str:
    return OTHER_KEY


@pytest.fixture(autouse=True)
def _configured_keys(monkeypatch):
    monkeypatch.setenv('TASKVAULT_API_KEYS', f'{KEY},{OTHER_KEY}')


@pytest.fixture
def client():
    from taskvault import api
    from taskvault.rate_limit import RateLimiter
    from taskvault.storage import TaskStore

    # A fresh store and fresh buckets per test: the module-level singletons would
    # otherwise carry one test's tasks and spent tokens into the next.
    api.store = TaskStore()
    api.limiter = RateLimiter()
    return TestClient(api.app)
