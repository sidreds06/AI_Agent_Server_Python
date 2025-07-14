import re
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
from backend.config import gpt4o

db = firestore.Client()

COMMON_EMOTIONS = [
    "grateful", "hope", "content", "connected", "drained",
    "envy", "disappointed", "relief", "happy", "sad", "angry",
    "anxious", "excited", "calm", "lonely", "overwhelmed"
]

def get_recent_mood_entries(user_id: str, days: int = 60):
    now = datetime.now(timezone.utc)
    min_date = now - timedelta(days=days)

    entries_ref = db.collection("mood_entries").document("entries").collection(user_id)
    docs = entries_ref.stream()
    recent_entries = []

    for doc in docs:
        data = doc.to_dict()
        end_date_val = data.get("endDate")
        if end_date_val:
            try:
                if isinstance(end_date_val, datetime):
                    end_date = end_date_val
                else:
                    end_date = datetime.fromisoformat(str(end_date_val))
                if end_date.tzinfo:
                    end_date_utc = end_date.astimezone(timezone.utc)
                else:
                    end_date_utc = end_date.replace(tzinfo=timezone.utc)
                if end_date_utc >= min_date:
                    recent_entries.append(data)
            except Exception as e:
                continue
    return recent_entries


def _find_emotions(text):
    emotions_found = []
    for e in COMMON_EMOTIONS:
        if re.search(r'\b' + re.escape(e) + r'\b', text, re.IGNORECASE):
            emotions_found.append(e)
    return list(set(emotions_found))

def _find_mood(text):
    moods = ["good", "bad", "neutral", "happy", "sad", "ok", "great", "awful", "fine"]
    for mood in moods:
        if re.search(r'\b' + re.escape(mood) + r'\b', text, re.IGNORECASE):
            return mood
    return None

async def extract_mood_details(user_message: str, conversation_history: list = None) -> dict:
    details = {
        "emotions": [],
        "mood": None,
        "note": None,
        "endDate": None,
        "missing_fields": []
    }
    text = user_message.strip()
    details["emotions"] = _find_emotions(text)
    details["mood"] = _find_mood(text)
    details["note"] = text
    # Set endDate to now unless extracted
    details["endDate"] = datetime.now(timezone.utc).isoformat()

    # Fallback to LLM if missing
    if not details["emotions"] or not details["mood"]:
        llm_resp = await gpt4o.ainvoke([
            {
                "role": "system",
                "content": (
                    "Extract the following from the user's message:\n"
                    "1. A list of specific emotions (words only, as a JSON list)\n"
                    "2. The overall mood (one word, like 'good', 'bad', or 'neutral')\n"
                    "Reply in strict JSON:\n"
                    "{\"emotions\": [...], \"mood\": \"...\"}"
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ])
        import json
        try:
            llm_json = json.loads(llm_resp.content)
            if not details["emotions"] and "emotions" in llm_json:
                details["emotions"] = llm_json["emotions"]
            if not details["mood"] and "mood" in llm_json:
                details["mood"] = llm_json["mood"]
        except Exception:
            pass

    if not details["mood"]:
        details["missing_fields"].append("mood")
    if not details["emotions"]:
        details["missing_fields"].append("emotions")

    return details

def generate_mood_confirmation_prompt(details: dict) -> str:
    missing = details["missing_fields"]
    if not missing:
        return None
    prompts = []
    if "mood" in missing:
        prompts.append("How would you describe your overall mood?")
    if "emotions" in missing:
        prompts.append("Which emotions did you experience? (e.g., grateful, anxious, calm, etc.)")
    if len(prompts) == 1:
        return prompts[0]
    elif len(prompts) == 2:
        return f"{prompts[0]} Also, {prompts[1].lower()}"
    else:
        return "Could you share more about how you're feeling?"
