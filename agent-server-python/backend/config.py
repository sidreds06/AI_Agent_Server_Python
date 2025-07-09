import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools.goal_tools import add_goal_tool, list_goal_categories

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

gpt4o_router = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)
gpt4o = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)
gpt4o_with_tools = gpt4o.bind_tools([add_goal_tool, list_goal_categories])

deepseek = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com/v1",
)
deepseek_with_tools = deepseek.bind_tools([add_goal_tool, list_goal_categories])
