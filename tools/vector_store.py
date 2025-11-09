import numpy as np
from typing import List, Dict, Any, Optional

import warnings

from sentence_transformers import SentenceTransformer
warnings.filterwarnings("ignore")

import chromadb
from logger_config import setup_logger

logger = setup_logger(__name__)

class EmbeddingEngine:
    '''Class to handle embedding generation using Sentence Transformers.'''
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        if not texts:
            return np.array([])
        
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    
    def encode_query(self, query: str) -> np.ndarray:
        return self.model.encode([query])[0]


class VectorStore:
    '''Simplified vector store for soccer match retrieval.'''
    def __init__(self, persist_dir: str = '../assets/chroma_db'):
        self.client = chromadb.PersistentClient(path=persist_dir)

        try: 
            self.client.delete_collection("matches")
        except: 
            pass

        self.collection = self.client.create_collection(
            name="matches", 
            metadata={"hnsw:space": "cosine"}
        )
        
    def clear_matches(self):
        """Clear all matches from the vector store."""
        try:
            self.client.delete_collection("matches")
        except:
            pass
        self.collection = self.client.create_collection(
            name="matches", 
            metadata={"hnsw:space": "cosine"}
        )

    def add_matches(self, matches: List[Dict], embeddings: List[np.ndarray]):
        """
        Add matches to the vector store.
        
        Args:
            matches: List of match dictionaries with 'matchId', 'teams', 'start'
            embeddings: List of embeddings for each match string
        """
        if not matches:
            logger.warning("No matches to add to vector store.")
            return
        
        logger.info(f"Adding {len(matches)} matches to vector store")
        
        # Convert matches to the format: "Team1 vs Team2 YYYY-MM-DD"
        match_strings = []
        match_ids = []
        
        for match in matches:
            match_string = f"{match['teams'][0]} {match['teams'][1]}"
            match_strings.append(match_string)
            match_ids.append(match['matchId'])
        
        # Add to ChromaDB
        self.collection.add(
            documents=match_strings,
            ids=match_ids,
            embeddings=[embedding.tolist() for embedding in embeddings]
        )
        
        logger.info(f"Successfully added {len(matches)} matches")

    def find_match(self, query_embedding: np.ndarray, similarity_threshold: float = 0.7) -> Optional[str]:
        """
        Find a match given a query embedding.
        
        Args:
            query_embedding: The embedding of the user query
            similarity_threshold: Minimum similarity score (default 0.7)
            
        Returns:
            Match ID if found with sufficient similarity, None otherwise
        """

        logger.info("Querying vector store for match...")
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=1,
            include=['documents', 'distances']
        )
        
        logger.info(f"Vector store query results: {results}")

        if results['ids'] and len(results['ids'][0]) > 0:
            # ChromaDB returns distance, convert to similarity
            similarity = 1 - results['distances'][0][0]
            
            if similarity >= similarity_threshold:
                match_id = results['ids'][0][0]
                match_document = results['documents'][0][0]
                logger.info(f"Found match: {match_document} (similarity: {similarity:.3f})")
                return match_id
            else:
                logger.debug(f"Best match similarity {similarity:.3f} below threshold {similarity_threshold}")
                return None
        
        logger.debug("No matches found")
        return None

    def debug_query(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        """Debug method to see top matches with their similarities."""
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=['documents', 'distances']
        )
        
        debug_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                similarity = 1 - results['distances'][0][i]
                debug_results.append({
                    "match_id": results['ids'][0][i],
                    "match_string": results['documents'][0][i],
                    "similarity": similarity
                })
        
        return debug_results