from langchain_core.messages import BaseMessage, HumanMessage

def serialize_messages(msgs: list[BaseMessage]) -> str:
    s = ""
    for m in msgs:
        if isinstance(m, HumanMessage):
            s += f"User: {m.content}\n"
        else:  # AIMessage
            s += f"Assistant: {m.content}\n"
    # finally cue the assistant for the next response
    s += "Assistant: "
    return s