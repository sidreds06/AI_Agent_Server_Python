from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import ChatRequest
from backend.llm_utils import sanitize_history, route_message, get_reply
from backend.rag_utils import get_user_data
from backend.models import ChatRequest, SummaryRequest
from backend.llm_utils import sanitize_history, route_message, get_reply, generate_chat_summary
from backend.voice.stt import transcribe_audio
from backend.voice.tts import synthesize_speech

from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
import json
import io
import base64

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
    
@app.post("/voice-chat")
async def voice_chat_endpoint(
    file: UploadFile = File(...),
    history: str = Form(None),
    uid: str = Form(None),
    voice: str = Form("alloy")
):
    try:
        audio_bytes = await file.read()
        filename = file.filename or "audio.m4a"
        print("Received file:", filename, "length:", len(audio_bytes))

        # Optional: Save for debugging - confirm m4a
        with open("debug_received.m4a", "wb") as f:
            f.write(audio_bytes)

        # Always use m4a extension for Whisper
        user_message = await transcribe_audio(audio_bytes, ".m4a")

        print("WHISPER transcript:", repr(user_message))

        # Prepare chat history
        simple_history = json.loads(history) if history else []
        simple_history.append({"role": "user", "content": user_message})

        # Chat logic
        user_data = {}
        if uid:
            try:
                user_data = get_user_data(uid)
            except Exception:
                user_data = {}
        route = await route_message(user_message)
        reply = await get_reply(route, simple_history, user_data, uid)
        if not reply:
            reply = "I'm here to help with your wellness journey! What would you like to work on today?"

        # Synthesize speech (should also be m4a, but OpenAI handles this)
        audio_data = await synthesize_speech(reply, voice)
        base64_audio = base64.b64encode(audio_data).decode()

        # Return JSON with transcript, reply, audio
        return {
            "user_transcript": user_message,
            "reply": reply,
            "audio_base64": base64_audio
        }
    except Exception as e:
        print("Voice chat error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
