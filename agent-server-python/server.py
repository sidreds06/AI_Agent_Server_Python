from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import ChatRequest
from backend.llm_utils import sanitize_history, route_message, get_reply
from backend.rag_utils import get_user_data
from backend.models import ChatRequest, SummaryRequest
from backend.llm_utils import sanitize_history, route_message, get_reply, generate_chat_summary

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_message = req.message
    history = req.history or []
    user_id = req.uid

    if not user_message:
        return {"error": "message is required"}
    user_data = {}
    if user_id:
        try:
            user_data = get_user_data(user_id)
        except Exception as e:
            user_data = {}
    try:
        route = await route_message(user_message)
        simple_history = sanitize_history(history)
        simple_history.append({"role": "user", "content": user_message})
        reply = await get_reply(route, simple_history, user_data, user_id)
        if not reply:
            reply = "I'm here to help with your wellness journey! What would you like to work on today?"
        return {"reply": reply}
    except Exception as e:
        return {"reply": "Sorry, I'm having trouble right now. Could you try again in a moment?"}

@app.post("/summarize")
async def summarize_endpoint(req: SummaryRequest):
    try:
        messages = req.messages
        if not messages:
            return {"summary": "New Chat"}
        from backend.llm_utils import generate_chat_summary
        summary = await generate_chat_summary(messages)
        return {"summary": summary}
    except Exception as e:
        print("Summary endpoint error:", e)
        return {"summary": "New Chat"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
