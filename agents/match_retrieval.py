from output_parsers import Response, TeamNames, tea_names_parser, response_parser
from langchain_openai import ChatOpenAI
from tools.match_list import find_match_in_list, find_match_in_store
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import create_agent 

from langchain_classic import hub

import logging


def retrieve_team_name(prompt: str) -> TeamNames:
    get_team_template = '''
    Given a human prompt about a match {prompt}, you must find the team name and return it.
    If you find more than one team name, return all of them in the same order.

    \n{format_instructions}
'''
    bet_place_prompt_template = PromptTemplate(input_variables=['prompt'], 
                                             template=get_team_template,
                                            partial_variables={'format_instructions': tea_names_parser.get_format_instructions()})

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")


    chain = bet_place_prompt_template | llm | tea_names_parser

    res:TeamNames = chain.invoke(input={'prompt': prompt })
    logging.info(res)
    return res

def retrieve_sign(prompt:str, match) -> Response:
    logging.info(prompt)
    retrieve_sign_template = '''
    Given a human prompt about a match {prompt}, and a match {match}, 
    you must find the desired result that the user is talking about.
    The predicted match result is called "sign".
    Possible signs are: home (home team wins), away (away team wins), draw, over (more than 2 goals), under (less than 2 goals).
    The user could use different words to refer to the signs. For example: 1 means home, X means draw, 2 means away
    
    Examples: 
    If the user says "Inter over 2.5" or "Inter over" you should return the sign "over".
    If the user says "Juve X" you should return the sign "draw".
    If the user says "Juve 2" you should return the sign "away".
    If the user says "Juve 1" you should return the sign "home".
    If the user says "Inter lose" and Inter is the home team, you should return the sign "away".

    If you can't determine the sign, return null.
    
    \n{format_instructions}
    '''

    get_sign_prompt_template = PromptTemplate(input_variables=['prompt', 'match'], 
                                             template=retrieve_sign_template,
                                            partial_variables={'format_instructions': response_parser.get_format_instructions()})

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")


    chain = get_sign_prompt_template | llm | response_parser

    res:Response = chain.invoke(input={'prompt': prompt, 'match': match })
    return res


def match_retrieval(prompt:str):
    team_names_res = retrieve_team_name(prompt)
    logging.info(team_names_res)
    # Find match using the team names
    search_term = " ".join(team_names_res.team_names)
    match_id = find_match_in_store(search_term)
    match = find_match_in_list(match_id)
    response = retrieve_sign(prompt, match)
    response.match_id = match_id
    return response