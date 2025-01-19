from typing import List
from dotenv import load_dotenv

from agents.bet_amount_retrieval import get_bet_amount
from agents.bet_removal import remove_bet
from agents.intent_recognition import recognize_intent
from agents.match_retrieval import retrieve_teams_and_sign

import uuid

from output_parsers import Match, ProcessActionResult
from typing import Dict
from typing import TypedDict

from third_parties.bollette_calcio import fetch_tournament_data
from tools.build_bet import build_bet
from tools.find_match import find_match_by_teams, find_match_in_list, find_match_in_payslip


PAYSLIPS: Dict[str, List[Match]] = {}

tournaments_data = fetch_tournament_data(mock=False)

def startup(input):
    id = uuid.uuid4().__str__()
    PAYSLIPS[id] = []
    if(len(tournaments_data) == 0):
        return {
            'status':'api-error',
            "payslip": [],
            "message": 'Something went wrong while grabbing the data from the server'
            }
    res = process_action(id,input)
    return {'id': id, **res}

def add_to_payslip(payslip, match: Match):
    for i, m in enumerate(payslip):
        if m.get('id') == match.id:
            payslip[i] = match.model_dump()
            return payslip
    payslip.append(match.model_dump())
    return payslip
    
def process_action(session_id, input) -> ProcessActionResult:
    payslip = PAYSLIPS[session_id]
    action = recognize_intent(input)
    print('User wants to',action)
    if action == "add":
        retrive_res = retrieve_teams_and_sign(input)
        match_found = find_match_in_list(retrive_res.teams, tournaments_data)
        if(match_found):
            bet = build_bet(match_found, retrive_res.sign)
            add_to_payslip(payslip, bet)
        return {'payslip': payslip, 'message': retrive_res.message}
    elif action == "remove":
        retrive_res = retrieve_teams_and_sign(input)
        match_found = find_match_in_payslip(retrive_res.teams, tournaments_data)
        payslip = [m for m in payslip if m.id != match_found.id]
        return {'payslip': payslip, 'message': remove_res.message}

    elif action == "replace":
        retrive_res = retrieve_teams_and_sign(input)
        print("🚀 ~ retrive_res:", retrive_res)
        if(retrive_res.removed_match_id):
            payslip = [m for m in payslip if m.get('id') != remove_res.removed_match_id]
        retrive_res = retrieve_teams_and_sign(input)
        if(retrive_res.match_found):
            add_to_payslip(payslip, retrive_res.match_found)
        return {'payslip': payslip, 'message': retrive_res.message}

    elif action == "checkout":
        product = 1.0
        get_bet_amount_res = get_bet_amount(input)
        if(get_bet_amount_res.amount == None):
            return get_bet_amount_res
        for match in payslip:
            product *= match.odd
        return { **get_bet_amount_res, 'payslip':payslip, 'multiplier': product*float(get_bet_amount_res.bet_amount) }