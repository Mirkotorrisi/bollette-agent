from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from output_parsers import Match, response_parser, Response



def get_bet_amount(user_input:str) -> Response:
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    intent_prompt = '''
You are a betting assistant. 
Based on the user input, you need to understand how much the user wants to bet.

Final answer is the amount of the bet.

If the amount can't be evaluated from the answer, return a message to the user and the correct error status.

User Input: {user_input}

{format_instructions}
'''

    prompt_template = PromptTemplate(input_variables=["user_input"], template=intent_prompt, partial_variables={'format_instructions': response_parser.get_format_instructions()}
)

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = prompt_template | llm | response_parser
    res:Response = chain.invoke(input={'user_input':user_input})
    return res