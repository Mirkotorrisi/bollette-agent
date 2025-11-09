from dotenv import load_dotenv
from third_parties.bollette_calcio import fetch_tournament_data
import threading
import logging
from tools.vector_store import VectorStore, EmbeddingEngine
from logger_config import setup_logger

# Load environment variables at the start
load_dotenv()

logger = setup_logger(__name__)

tournaments_data = []
vector_store = VectorStore()
embeddings_engine = EmbeddingEngine()

def fetch_data_periodically():
    global tournaments_data
    logger.info("Fetching tournament data...")
    tournaments_data = fetch_tournament_data(mock=False)
    logger.info(f"Fetched {len(tournaments_data)} matches")
    
    # Create embeddings for match strings
    match_strings = [convert_match_to_string(match) for match in tournaments_data]
    embeddings = embeddings_engine.encode_texts(match_strings)
    
    logger.info("Updating vector store with new data...")
    vector_store.clear_matches()
    vector_store.add_matches(tournaments_data, embeddings)
    
    threading.Timer(300, fetch_data_periodically).start()

def convert_match_to_string(match: dict) -> str:
    """Convert match to format: 'Team1 Team2'"""
    return f"{match['teams'][0]} {match['teams'][1]}"

# Initialize data fetching
fetch_data_periodically()

def find_match_in_store(query: str, similarity_threshold: float = 0.7) -> str:
    """
    Find a match using similarity search.
    
    Args:
        query: User query (e.g., "Brentford match")
        similarity_threshold: Minimum similarity required
        
    Returns:
        Match ID if found, "No match found" otherwise
    """
    logger.info(f"Finding match for query: {query} with threshold {similarity_threshold}")

    query_embedding = embeddings_engine.encode_query(query)
    match_id = vector_store.find_match(query_embedding, similarity_threshold)
    if match_id:
        logger.info(f"Match found with ID: {match_id}")
        return match_id
    else:
        # For debugging, show top matches
        logger.debug(f"No match found for query: {query}")
        debug_results = vector_store.debug_query(query_embedding, top_k=3)
        logger.debug("Top 3 closest matches:")
        for result in debug_results:
            logger.debug(f"  {result['match_string']} (similarity: {result['similarity']:.3f})")
        return "No match found"

def find_match_in_list(match_id: str) -> dict:
    """Find match details by match_id."""
    for match in tournaments_data:
        if match['matchId'] == match_id:  # Note: using 'matchId' not 'id'
            return match
    return {}

def get_match_list(args):
    """Get formatted list of all matches."""
    logging.info(args)
    formatted_list = []
    for match in tournaments_data:
        formatted_match = {
            'id': match.get('matchId'),  # Note: using 'matchId'
            'home': match.get('teams')[0],
            'away': match.get('teams')[1],
        }
        formatted_list.append(formatted_match)
    return formatted_list