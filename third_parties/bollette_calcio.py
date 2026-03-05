import requests
import os
from typing import Dict

import logging

def fetch_tournament_data(mock: bool = False) -> Dict[str, any]:
    """
    Fetches data for all tournaments synchronously using requests.

    Args:
        mock (bool): If True, returns mock data.

    Returns:
        dict: A dictionary with tournament keys as keys and API responses as values.
    """
    base_url = os.environ.get("BOLLETTE_SERVER_BASE_URL")
    results = {}

    if mock:
        return {}


    try:
        response = requests.get(base_url + "/championships/all", timeout=20)
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        results = {"error": str(e)}
    
    return results
