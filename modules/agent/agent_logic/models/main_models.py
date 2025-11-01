from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

GPT4O = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_KEY"),
)