import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# LangChain models
gpt4o = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)
deepseek = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com/v1",
)

# Session memory (in-memory for now)
sessions = {}

# Business logic for routing (as simple Python function)
async def route_message(user_message: str):
    system = (
        "You are a routing assistant. Decide if the following message is about mental wellness, career, or physical health."
        " Reply with one word: 'mental', 'career', or 'physical'."
    )
    routing_response = await gpt4o.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user_message),
    ])
    route = routing_response.content.strip().lower()
    return route if route in ["mental", "career", "physical"] else "main"


async def get_reply(agent_type, history):
    # Message list for LangChain
    lc_messages = []
    if agent_type == "mental":
        lc_messages.append(SystemMessage(content="You are a mental wellness coach. You help users with emotions, stress, and anxiety."))
    elif agent_type == "career":
        lc_messages.append(SystemMessage(content="You are a career coach. You help users with jobs, resumes, and interviews."))
    elif agent_type == "physical":
        lc_messages.append(SystemMessage(content="You are a physical wellness coach. You help users with fitness, diet, sleep, and physical health. Do not use tools or structured output. Respond only using plain text. If asked what model you are, reply: 'I'm powered by DeepSeek.'"))
    else:
        lc_messages.append(SystemMessage(content="You are a friendly wellness assistant.\n→ For stress/emotion queries → Mental Coach\n→ For fitness/diet/workouts → Physical Coach\n→ For resumes/interviews → Career Coach\nOtherwise, answer directly."))

    for h in history:
        if h["role"] == "user":
            lc_messages.append(HumanMessage(content=h["content"]))
        else:
            lc_messages.append(AIMessage(content=h["content"]))  # Use AIMessage for assistant replies

    # Choosing the right model
    if agent_type == "physical":
        return await deepseek.ainvoke(lc_messages)
    else:
        return await gpt4o.ainvoke(lc_messages)

class ChatRequest(BaseModel):
    sessionId: str
    message: str

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = req.sessionId
    user_message = req.message
    if not session_id or not user_message:
        return {"error": "sessionId and message are required"}
    # Restore or create session history
    history = sessions.get(session_id, [])
    history.append({"role": "user", "content": user_message})
    agent_type = await route_message(user_message)  
    print(f"User message: {user_message} | Routed to: {agent_type}")

    try:
        reply_obj = await get_reply(agent_type, history)
        reply = reply_obj.content if hasattr(reply_obj, "content") else str(reply_obj)
        # Save bot message in history
        history.append({"role": "assistant", "content": reply})
        sessions[session_id] = history
        return {"reply": reply}
    except Exception as e:
        print(f"Agent error: {e}")
        return {"reply": "Sorry, something went wrong."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
