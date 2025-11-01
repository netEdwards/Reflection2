"""
/modules/agent/agent_logic/main.py

This file will be the main branch of Logic.

All formations of memory, context retrieval, or other asssistants and orchestrations will integrate here.

This is the main component of the generation portion of the graph.
This will be responsible for being the non-task or specific category of RAG or Agentic workflows.
It will be more of a focus on the things that will be required regardless of special features or capabilities.

That said included are (not limited to):
- Generation node, final node of generation or the thing that returns the answer.
- Coordination from a supervisor defined here to other agent logic in the folder.
- Utility necessacities. Such as, thread management, global state control, etc...

The used graph in app or used in general will be compiled here!
"""
# modules/agent/agent_logic/main/main.py
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from .main_state import State
from .main_nodes import generate

def build_graph() -> StateGraph:
    graph = StateGraph(State)
    graph.add_node("generate", generate)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", END)
    return graph

G = build_graph().compile()

if __name__ == "__main__":
    cfg = RunnableConfig()  # empty – no tracing, no langsmith
    out = G.invoke({"prompt": "Give me a short haiku about GPUs 🖥️"}, cfg)
    print(out)

