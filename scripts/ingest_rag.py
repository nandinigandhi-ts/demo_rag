import os
import uuid
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from google import genai
from google.genai import types

# Load env from the agent folder so the script works no matter where you run it
load_dotenv("agents/kai_agent/.env", override=True)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "admissions_rag")

DOCS_DIR = Path("agents/kai_agent/rag_docs")
EMBED_MODEL = "gemini-embedding-001"
DIM = 768  # recommended dimension for storage/perf
BATCH = 16

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        i += max(1, chunk_size - overlap)
    return chunks

def l2_normalize(vec: list[float]) -> list[float]:
    arr = np.array(vec, dtype=np.float32)
    n = np.linalg.norm(arr)
    if n == 0:
        return arr.tolist()
    return (arr / n).tolist()

def main():
    # Qdrant client
    qc = QdrantClient(url=QDRANT_URL)

    # (Re)create collection
    qc.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=qmodels.VectorParams(size=DIM, distance=qmodels.Distance.COSINE),
    )

    # GenAI client picks GOOGLE_API_KEY / GEMINI_API_KEY from env
    gclient = genai.Client()

    points = []

    for fp in sorted(DOCS_DIR.glob("**/*")):
        if fp.is_dir():
            continue
        if fp.suffix.lower() not in [".md", ".txt"]:
            continue

        text = fp.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text)

        # Embed in batches (RETRIEVAL_DOCUMENT)
        for start in range(0, len(chunks), BATCH):
            batch = chunks[start:start+BATCH]
            result = gclient.models.embed_content(
                model=EMBED_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=DIM,
                ),
            )

            for j, emb in enumerate(result.embeddings):
                vec = l2_normalize(emb.values)  # needed for 768 dims
                idx = start + j
                pid = str(uuid.uuid4())
                points.append(
                    qmodels.PointStruct(
                        id=pid,
                        vector=vec,
                        payload={
                            "source": fp.name,
                            "chunk_index": idx,
                            "text": batch[j],
                        },
                    )
                )

    if points:
        qc.upsert(collection_name=COLLECTION, points=points)

    print(f"✅ Ingested {len(points)} chunks into Qdrant collection '{COLLECTION}' at {QDRANT_URL}")

if __name__ == "__main__":
    main()
