from typing import List
from output_parsers import Match, response_parser, Response
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


def remove_bet(prompt:str, betslip: List[Match]) -> str:
    bet_remove_template = '''
        given a betslip {betslip} and a human prompt about a match {prompt} I want you to find the match that the prompt is about and return its id, if present.

        Final answer is the id of the match to remove.

        {format_instructions}
    '''

    bet_remove_prompt_template = PromptTemplate(input_variables=['prompt','betslip'], 
                                             template=bet_remove_template,
                                            partial_variables={'format_instructions': response_parser.get_format_instructions()}
                                             )

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

    chain = bet_remove_prompt_template | llm | response_parser

    res:Response = chain.invoke(input={'prompt': prompt, 'betslip': betslip })
    return res