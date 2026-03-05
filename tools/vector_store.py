import numpy as np
from typing import List, Dict, Any, Optional
from openai import OpenAI
from logger_config import setup_logger
import os

logger = setup_logger(__name__)

from langchain_openai import OpenAIEmbeddings

class EmbeddingEngine:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.embeddings = OpenAIEmbeddings(model=model_name)

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def encode_query(self, query: str) -> List[float]:
        return self.embeddings.embed_query(query)

class VectorStore:
    '''Ultra-lightweight Vector Store using simple Cosine Similarity.'''
    def __init__(self):
        self.matches_data = [] # Lista di dict: {"id": str, "doc": str, "embedding": list}

    def clear_matches(self):
        self.matches_data = []
        logger.info("Vector store cleared.")

    def add_matches(self, matches: List[Dict], embeddings: List[List[float]]):
        if not matches:
            return
        
        for match, emb in zip(matches, embeddings):
            match_string = f"{match['teams'][0]} {match['teams'][1]}"
            self.matches_data.append({
                "id": str(match['matchId']),
                "doc": match_string,
                "embedding": np.array(emb)
            })
        logger.info(f"Added {len(matches)} matches to memory store.")

    def find_match(self, query_embedding: List[float], similarity_threshold: float = 0.7) -> Optional[str]:
        if not self.matches_data:
            return None

        q_emb = np.array(query_embedding)
        best_similarity = -1
        best_match_id = None

        for item in self.matches_data:
            # Cosine similarity semplice con numpy
            sim = np.dot(q_emb, item["embedding"]) / (np.linalg.norm(q_emb) * np.linalg.norm(item["embedding"]))
            if sim > best_similarity:
                best_similarity = sim
                best_match_id = item["id"]

        if best_similarity >= similarity_threshold:
            logger.info(f"Found match ID: {best_match_id} (sim: {best_similarity:.3f})")
            return best_match_id
        
        return None
    
    def debug_query(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Debug method: calculates cosine similarity locally and returns top K."""
        if not self.matches_data:
            return []

        q_emb = np.array(query_embedding)
        scored_results = []

        for item in self.matches_data:
            # Calcolo Cosine Similarity: (A dot B) / (||A|| * ||B||)
            norm_q = np.linalg.norm(q_emb)
            norm_i = np.linalg.norm(item["embedding"])
            
            if norm_q == 0 or norm_i == 0:
                similarity = 0
            else:
                similarity = np.dot(q_emb, item["embedding"]) / (norm_q * norm_i)
            
            scored_results.append({
                "match_id": item["id"],
                "match_string": item["doc"],
                "similarity": float(similarity)
            })

        # Ordina per similarità decrescente e prendi i primi K
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_results[:top_k]