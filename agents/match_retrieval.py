from typing import List
from output_parsers import Match, Response, response_parser
from third_parties.bollette_calcio import fetch_tournament_data
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

def retrieve_teams_and_sign(prompt:str) -> Response:
    bet_place_template = '''
    Given a human prompt about a match {prompt}

    You must find the team name that the user is talking about.
    
    If more than one team is mentioned, return both
    If you can't find any team name, return null

    You must also determine the result of the match based on the human prompt.

    The predicted match result is called "sign".
    Possible signs are: home (first team wins), away (second team wins), draw, over (more than 2 goals), under (less than 2 goals).

    The user could use different words to refer to the signs. For example: 1 means home, X means draw, 2 means away

    For example, if the user says "Inter lose" and the nearest Inter's match is Inter - Verona, you should return the sign "away".

    If you can't determine the sign, return null.

    \n{format_instructions}
    '''

    bet_place_prompt_template = PromptTemplate(input_variables=['tournaments_data', 'prompt'], 
                                             template=bet_place_template,
                                            partial_variables={'format_instructions': response_parser.get_format_instructions()})

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

    chain = bet_place_prompt_template | llm | response_parser


    res:Response = chain.invoke(input={'prompt': prompt})
    return res