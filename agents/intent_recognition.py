from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


def recognize_intent(user_input:str) -> str:
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    intent_prompt = '''
You are a betting assistant. Based on the user input, identify the intent and provide the necessary details. 

Possible actions:
1. Add a bet to the slip (for example: "I want to bet on Manchester United to win", "Roma Over", etc.)
2. Remove a bet from the slip
3. Replace a bet in the slip
4. Checkout the slip (confirm the bets, says how much to bet, etc.)

User Input: {user_input}

Provide one of the following string:

add/remove/replace/checkout
'''

    prompt_template = PromptTemplate(input_variables=["user_input"], template=intent_prompt)

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = prompt_template | llm
    intent = chain.invoke(input={'user_input':user_input})
    return intent.content