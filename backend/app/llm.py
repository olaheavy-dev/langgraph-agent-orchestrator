"""Model construction, in one place and behind a cache.

Built lazily rather than at import: the graph, the nodes and the corpus loader
must all be importable without an API key present, or the test suite would need
credentials to check routing logic that never calls a model.
"""

from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain.embeddings import init_embeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app import config


@lru_cache
def get_model() -> BaseChatModel:
    return init_chat_model(config.get_settings().model)


@lru_cache
def get_embeddings() -> Embeddings:
    return init_embeddings(config.get_settings().embedding_model)
