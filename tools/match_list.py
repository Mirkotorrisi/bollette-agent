from third_parties.bollette_calcio import fetch_tournament_data
import threading


tournaments_data = []

def fetch_data_periodically():
    global tournaments_data
    tournaments_data = fetch_tournament_data(mock=False)
    threading.Timer(300, fetch_data_periodically).start()

fetch_data_periodically()

def find_match_in_list(match_id: str) -> dict:
    for match in tournaments_data:
        if match['id'] == match_id:
            return match

def get_match_list(args):
    print(args)
    formatted_list = []
    for match in tournaments_data:
        formatted_match = {
            'id': match.get('id'),
            'home': match.get('teams')[0],
            'away': match.get('teams')[1],
        }
        formatted_list.append(formatted_match)
    return formatted_list