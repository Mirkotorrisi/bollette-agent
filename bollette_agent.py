from typing import List

from agents.bet_amount_retrieval import get_bet_amount
from agents.bet_removal import remove_bet
from agents.intent_recognition import recognize_intent
from agents.match_retrieval import match_retrieval

import uuid

from output_parsers import Match, ProcessActionResult
from typing import Dict

from tools.match_list import find_match_in_list


PAYSLIPS: Dict[str, List[Match]] = {}


def startup(input):
    id = uuid.uuid4().__str__()
    PAYSLIPS[id] = []
    res = process_action(id,input)
    return {'id': id, **res}

def add_to_payslip(payslip, match, sign: str):
    odd = match.get('odds').get(sign)
    if(not odd): 
        return payslip
    bet = Match(id=match.get('id'), sport_key=match.get('sport_key'), matchId=match.get('matchId'), teams=match.get('teams'), start=match.get('start'), odd=odd, sign=sign)
    for i, m in enumerate(payslip):
        if m.get('id') == bet.id:
            payslip[i] = bet.model_dump()
            return payslip
    payslip.append(bet.model_dump())
    return payslip
    
def process_action(session_id, input) -> ProcessActionResult:
    payslip = PAYSLIPS[session_id]
    action = recognize_intent(input)
    print('\nUser wants to',action)
    if action == "add":
        res = match_retrieval(input)
        print(res)
        match_found = find_match_in_list(res.match_id)
        if(match_found and res.sign):
            add_to_payslip(payslip, match_found, res.sign)
        return {'payslip': payslip, 'message': res.message}
    elif action == "remove":
        res = match_retrieval(input)
        payslip = [m for m in payslip if m.id != res.match_id]
        return {'payslip': payslip, 'message': res.message}

    elif action == "replace":
        res = match_retrieval(input)
        payslip = [m for m in payslip if m.get('id') != res.match_id]
        res = match_retrieval(input)
        match_found = find_match_in_list(res.match_id)
        if(match_found and res.sign):
            add_to_payslip(payslip, match_found, res.sign)
        return {'payslip': payslip, 'message': res.message}

    elif action == "checkout":
        product = 1.0
        get_bet_amount_res = get_bet_amount(input)
        if(get_bet_amount_res.amount == None):
            return get_bet_amount_res
        for match in payslip:
            product *= match.odd
        return { **get_bet_amount_res, 'payslip':payslip, 'multiplier': product*float(get_bet_amount_res.bet_amount) }