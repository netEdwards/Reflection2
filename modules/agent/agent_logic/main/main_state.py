"""
/modules/agent/agent_logic/main_state.py

The core state driving the glolabl graph state. Basic things such as the user conversation, files reference, or aux data is placed.

It will be used as both the foundation and the trunk of the tree. 
Nodes built out will expand off of this and mutate it.
This makes branching and combining states easier!

"""


from typing import Optional, TypedDict, List, Literal
from langgraph.graph import StateGraph, MessagesState

# modules/agent/agent_logic/main/main_state.py
from typing import TypedDict, List

class State(MessagesState):
    stream: bool              # whether caller requested streaming
