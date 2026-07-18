"""DashScope embedding and rerank client for project evidence retrieval."""

from __future__ import annotations

import logging
from typing import Literal

import dashscope
import numpy as np
from dashscope import TextEmbedding, TextReRank

from backend.app.config import settings

logger = logging.getLogger(__name__)

TextType = Literal["document", "query"]


def _configure_dashscope() -> None:
    dashscope.api_key = settings.dashscope_api_key
    dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"


def _call_embedding(
    texts: list[str],
    *,
    model: str,
    text_type: TextType,
) -> list[list[float]]:
    _configure_dashscope()
    response = TextEmbedding.call(
        model=model,
        input=texts,
        text_type=text_type,
        dimension=settings.embedding_dimensions,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Embedding API failed ({response.status_code}): {getattr(response, 'message', response)}"
        )
    embeddings = response.output.get("embeddings", [])
    return [item["embedding"] for item in embeddings]


def embed_texts(
    texts: list[str],
    *,
    text_type: TextType = "document",
) -> tuple[list[list[float]], str]:
    """Batch embed texts; returns vectors and model name used."""
    if not texts:
        return [], settings.embedding_model
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    batch_size = settings.embedding_batch_size
    model = settings.embedding_model
    all_vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        try:
            vectors = _call_embedding(batch, model=model, text_type=text_type)
        except Exception as exc:
            logger.warning("Primary embedding model failed, trying fallback: %s", exc)
            model = settings.embedding_fallback_model
            vectors = _call_embedding(batch, model=model, text_type=text_type)
        if len(vectors) != len(batch):
            raise RuntimeError("Embedding API returned unexpected vector count")
        all_vectors.extend(vectors)

    return all_vectors, model


def embed_query(text: str) -> tuple[list[float], str]:
    vectors, model = embed_texts([text], text_type="query")
    return vectors[0], model


def normalize_vectors(vectors: list[list[float]]) -> np.ndarray:
    arr = np.array(vectors, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def rerank_documents(
    query: str,
    documents: list[str],
    *,
    top_n: int | None = None,
) -> list[tuple[int, float]]:
    """Rerank documents; returns (original_index, score) pairs."""
    if not documents:
        return []
    if not settings.dashscope_api_key:
        return [(i, float(len(documents) - i)) for i in range(min(top_n or len(documents), len(documents)))]

    _configure_dashscope()
    top_n = top_n or settings.rerank_top_n
    try:
        response = TextReRank.call(
            model=settings.rerank_model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
            instruct=settings.rerank_instruct,
        )
        if response.status_code != 200:
            raise RuntimeError(response.message)
        results = response.output.get("results", [])
        return [(item["index"], float(item["relevance_score"])) for item in results]
    except Exception as exc:
        logger.warning("Rerank failed, caller should use RRF ordering: %s", exc)
        raise
