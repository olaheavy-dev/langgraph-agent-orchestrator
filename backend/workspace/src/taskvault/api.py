"""HTTP surface.

Thin by intention: validation and auth happen here, everything else delegates.
The endpoint contract is documented in api.md and that document is the source of
truth -- if the two disagree, the code is wrong.
"""

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from taskvault import auth
from taskvault.models import Status
from taskvault.rate_limit import RateLimiter
from taskvault.storage import TaskStore

app = FastAPI(title='TaskVault', version='0.3.1')

store = TaskStore()
limiter = RateLimiter()


def require_key(x_api_key: str | None = Header(default=None)) -> str:
    """Reject unknown keys, then spend one token from that key's bucket."""
    if not auth.is_valid(x_api_key):
        raise HTTPException(status_code=401, detail='invalid or missing API key')
    assert x_api_key is not None
    if not limiter.allow(x_api_key):
        raise HTTPException(status_code=429, detail='rate limit exceeded')
    return x_api_key


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}


@app.post('/tasks', status_code=201)
def create_task(payload: dict, key: str = Depends(require_key)) -> dict:
    title = (payload.get('title') or '').strip()
    if not title:
        raise HTTPException(status_code=400, detail='title is required')
    return store.create(title, key).to_dict()


@app.get('/tasks')
def list_tasks(
    status: Status | None = Query(default=None),
    key: str = Depends(require_key),
) -> list[dict]:
    return [task.to_dict() for task in store.list(key, status)]


@app.post('/tasks/{task_id}/complete')
def complete_task(task_id: int, key: str = Depends(require_key)) -> dict:
    task = store.complete(task_id, key)
    if task is None:
        raise HTTPException(status_code=404, detail='no such task')
    return task.to_dict()
