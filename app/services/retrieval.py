from dataclasses import dataclass

import numpy as np

from app.services.embeddings import embed
from app.services.ingestion import Chunk, load_corpus


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


class Retriever:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = load_corpus()
        self.embeddings: np.ndarray = embed([c.text for c in self.chunks])

    def search(self, query: str, top_k: int) -> list[RetrievalResult]:
        query_vec = embed([query])[0]
        scores = self.embeddings @ query_vec
        order = np.argsort(-scores)[:top_k]
        return [RetrievalResult(chunk=self.chunks[i], score=float(scores[i])) for i in order]

    def by_section_id(self, section_id: str) -> Chunk:
        for chunk in self.chunks:
            if chunk.section_id == section_id:
                return chunk
        raise KeyError(section_id)
