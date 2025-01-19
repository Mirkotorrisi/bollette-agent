from output_parsers import Response, TeamNames,Sign, tea_names_parser, response_parser, sign_parser
from langchain_openai import ChatOpenAI
from tools.match_list import find_match_in_list, get_match_list
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)

from langchain import hub

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
    return res


def retrieve_match(teams) -> Response:
    bet_place_template = '''
    Given a list of teams {teams}, you must find the fetch the match list and find the first match that the teams are about to play.

    Final answer is the match id.
    '''


    bet_place_prompt_template = PromptTemplate(input_variables=['teams'], 
                                             template=bet_place_template)

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")


    tools_for_agent = [
        Tool(
            name ="Match list retrieval",
            func = get_match_list,
            description="Useful to fetch a match list",
        )
    ]

    react_prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=tools_for_agent, prompt=react_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, verbose=True)

    result = agent_executor.invoke(
        input={"input": bet_place_prompt_template.format_prompt(teams=teams)},
        handle_parsing_errors=True
    )
    
    return result['output']


def retrieve_sign(prompt:str, match) -> Response:
    print(prompt)
    # retrieve_sign_template = '''
    # Given a human prompt about a match {prompt}, 
    # and a match {match}, 
    # you must find the desired result that the user is talking about.
    # The predicted match result is called "sign".
    # Possible signs are: home (home team wins), away (away team wins), draw, over (more than 2 goals), under (less than 2 goals).
    # The user could use different words to refer to the signs. For example: 1 means home, X means draw, 2 means away
    # For example, if the user says "Inter lose" and Inter is the home team, you should return the sign "away".
    # The user could also give the raw sign directly. For example, if the user says "Inter over 2.5" or "Inter over" you should return the sign "over".
    # If you can't determine the sign, return null.
    # '''
    retrieve_sign_template = '''
    Given a human prompt about a match {prompt}, 
    and a match {match}, 
    Find the desired sign of the match.

    Use this list to parse some ambiguous words:
    1=home, X=draw, 2=away, over=more than 2 goals, under=less than 2 goals.

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
    match_id = retrieve_match(team_names_res.team_names)
    match = find_match_in_list(match_id)
    response = retrieve_sign(prompt, match)
    response.match_id = match_id
    return response