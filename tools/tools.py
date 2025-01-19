from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

def get_profile_url_tavily(query:str):
    """Searches for Linkedin or Twitter profile page"""
    search = TavilySearchResults()
    res = search.run(f"{query}")
    return res