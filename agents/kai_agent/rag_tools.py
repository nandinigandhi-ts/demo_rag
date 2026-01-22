import os
from dotenv import load_dotenv
import numpy as np

from qdrant_client import QdrantClient
from google import genai
from google.genai import types

load_dotenv("agents/kai_agent/.env", override=True)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "admissions_rag")
EMBED_MODEL = "gemini-embedding-001"
DIM = 768

def _l2_normalize(vec: list[float]) -> list[float]:
    arr = np.array(vec, dtype=np.float32)
    n = np.linalg.norm(arr)
    if n == 0:
        return arr.tolist()
    return (arr / n).tolist()

def rag_search(query: str, limit: int = 4) -> dict:
    """
    Vector search over admissions documents.
    Returns top chunks with sources so answers are grounded.
    """
    if not query or not query.strip():
        return {"status": "error", "message": "query is required"}

    qc = QdrantClient(url=QDRANT_URL)
    gclient = genai.Client()

    emb_res = gclient.models.embed_content(
        model=EMBED_MODEL,
        contents=query.strip(),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=DIM,
        ),
    )

    [emb] = emb_res.embeddings
    qvec = _l2_normalize(emb.values)

    if hasattr(qc, "search"):
        hits = qc.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=int(limit),
            with_payload=True,
        )
    else:
        res = qc.query_points(
            collection_name=COLLECTION,
            query=qvec,              # vector query
            limit=int(limit),
            with_payload=True,
        )
        hits = res.points

    results = []
    for h in hits:
        payload = h.payload or {}
        results.append({
            "score": float(h.score),
            "source": payload.get("source"),
            "chunk_index": payload.get("chunk_index"),
            "text": payload.get("text"),
        })

    return {"status": "ok", "results": results}
