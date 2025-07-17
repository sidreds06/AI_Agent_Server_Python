import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools.goal_tools import add_goal_tool, list_goal_categories

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_HIDE_INPUTS"] = "false"
os.environ["LANGCHAIN_HIDE_OUTPUTS"] = "false"

# GPT-4o-mini
gpt4o_mini = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
)
gpt4o_mini_with_tools = gpt4o_mini.bind_tools([add_goal_tool, list_goal_categories])

# GPT-4o
gpt4o = ChatOpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
)
gpt4o_with_tools = gpt4o.bind_tools([add_goal_tool, list_goal_categories])

# DeepSeek
deepseek = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)
deepseek_with_tools = deepseek.bind_tools([add_goal_tool, list_goal_categories])
