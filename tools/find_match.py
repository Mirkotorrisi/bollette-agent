from typing import Dict, List

from output_parsers import Match
from difflib import SequenceMatcher


def find_match_in_list(teams: List[str], tournaments_data: List[Match]) -> dict:
    print("Found teams", teams)
    for match in tournaments_data:
        for team in teams:
            for match_team in match.get('teams'):
                is_similar = SequenceMatcher(None, team.lower(), match_team.lower()).ratio() > 0.8
                is_included = team.lower() in match_team.lower()
                if is_similar or is_included:
                    return match
    pass

def find_match_in_payslip(teams: List[str], payslip: List[Match]) -> dict:
    print("Found teams", teams)
    for match in payslip:
        for team in teams:
            for match_team in match.teams:
                is_similar = SequenceMatcher(None, team.lower(), match_team.lower()).ratio() > 0.8
                is_included = team.lower() in match_team.lower()
                if is_similar or is_included:
                    return match
    pass