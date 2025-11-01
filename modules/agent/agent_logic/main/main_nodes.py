"""
/modules/agent/agent_logic/main_nodes.py

The main nodes used to orchestrate most of the basic and required logic of a Agent graph!

"""
# modules/agent/agent_logic/main/main_nodes.py
from typing import Iterable

from .main_state import State
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
# from modules.agent.agent_logic.utils.serializer import serialize_messages
# from modules.agent.agent_logic.models.mistral_q import model_config_1
from modules.agent.agent_logic.models.main_models import GPT4O


# grab the singleton quantised model
SYSTEM_PROMPT = SystemMessage(
    content=(
        """
        You are Reflection, that is your name. You are chatting with an intelligent engineer and asipring thinker and independant mind.
        You are to assistant him in a symbollic relationship to achiece better mind and better intellegence. 
        From questions about philosophy to programming and help with code!

        Keep responses to the point. Chat casually with the user in resposnes, but do not stray away from the prompts or conversation as the focus. 
        """
    )
)

model = GPT4O

def generate(state: State) -> State:
    # 1) Build the prompt list: system + all past turns
    prompt_messages = [SYSTEM_PROMPT] + state["messages"]

    # 2) Ask the chat model for the next reply
    #    use generate_messages(), not invoke()
    chat_result = model.invoke(prompt_messages)

    # 3) Extract the AIMessage it returned

    # 4) Append that AIMessage into the state.history  
    state["messages"].append(chat_result)

    # 5) Return the updated state; LangGraph will pass it on
    return state
