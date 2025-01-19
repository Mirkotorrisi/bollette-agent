from output_parsers import Match


def build_bet(match: dict, sign: str) -> Match:
    odd = match.get('odds').get(sign)
    return Match(id=match.get('id'), sport_key=match.get('sport_key'), matchId=match.get('matchId'), teams=match.get('teams'), start=match.get('start'), odd=odd, sign=sign)