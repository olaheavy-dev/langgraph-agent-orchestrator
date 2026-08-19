"""The application.

Thin on purpose: it mounts routers and configures CORS. Everything that could be
interesting has been put somewhere it can be tested without a server.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app import config  # noqa: E402
from app.routers import chat, health, threads  # noqa: E402

app = FastAPI(
    title='LangGraph Agent Orchestrator',
    version='0.1.0',
    description=(
        'Routes a message to a chat agent, a retrieval agent, or a coding agent. '
        'The coding agent reads the documentation before it writes code, and pauses '
        'for human approval before anything is applied.'
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_settings().cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(threads.router)
