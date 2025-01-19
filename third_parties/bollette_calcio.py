import requests
import os
from typing import Dict

def fetch_tournament_data(mock: bool = False) -> Dict[str, any]:
    """
    Fetches data for all tournaments synchronously using requests.

    Args:
        tournament_keys (list): A list of tournament keys (strings).
        mock (bool): If True, fetches data from a mock endpoint.

    Returns:
        dict: A dictionary with tournament keys as keys and API responses as values.
    """
    base_url = os.environ.get("BOLLETTE_SERVER_API_KEY")
    mocked_url = "https://mocked-api-url.com"  # Example mocked URL
    results = {}

    if mock:
        try:
            response = requests.get(mocked_url, timeout=10)
            response.raise_for_status()
            results = response.json()
        except Exception as e:
            print(f"Error fetching mock data: {e}")
        return results


    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        results = {"error": str(e)}
    
    return results
