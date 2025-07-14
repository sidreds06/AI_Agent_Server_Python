import os
from dotenv import load_dotenv
from backend.mood_extraction import get_recent_mood_entries


# Load from .env file
load_dotenv()

service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


from google.cloud import firestore

db = firestore.Client()

def get_user_profile(user_id: str):
    doc_ref = db.collection("users").document(user_id).collection("profile").document("general")
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else {}
    

def get_user_goals(user_id: str):
    goals_ref = db.collection("goals")
    query_ref = goals_ref.where("user_id", "==", user_id)
    results = query_ref.stream()
    return [doc.to_dict() for doc in results]

def get_user_data(user_id: str):
    profile = get_user_profile(user_id)
    goals = get_user_goals(user_id)
    recent_moods = get_recent_mood_entries(user_id, days=60)  # fetch last 7 days
    return {"profile": profile, "goals": goals, "recent_moods": recent_moods}

def format_profile_goals_and_moods(user_data):
    profile = user_data.get("profile", {})
    goals = user_data.get("goals", [])
    moods = user_data.get("recent_moods", [])

    profile_text = (
        f"User Profile:\n"
        f"Name: {profile.get('name', '[unknown]')}\n"
        f"Age: {profile.get('age', '[unknown]')}\n"
        f"Gender: {profile.get('gender', '[unknown]')}\n"
    )
    goals_text = ""
    if goals:
        goals_text = "User Goals:\n" + "\n".join(
            [f"- {g.get('goalName', '[No name]')}: {g.get('goalDescription', '[No description]')}" for g in goals]
        ) + "\n"
    moods_text = ""
    if moods:
        moods_text = "Recent Mood Entries:\n" + "\n".join(
            [f"{m.get('endDate', '[no date]')}: {m.get('mood', '[no mood]')} | Emotions: {', '.join(m.get('emotions', []))} | Note: {m.get('note', '')[:40]}..." for m in moods]
        ) + "\n"
    return profile_text + goals_text + moods_text


def format_profile_and_goals(user_data):
    profile = user_data.get("profile", {})
    goals = user_data.get("goals", [])
    profile_text = (
        f"User Profile:\n"
        f"Name: {profile.get('name', '[unknown]')}\n"
        f"Age: {profile.get('age', '[unknown]')}\n"
        f"Gender: {profile.get('gender', '[unknown]')}\n"
    )
    goals_text = ""
    if goals:
        goals_text = "User Goals:\n" + "\n".join(
            [f"- {g.get('goalName', '[No name]')}: {g.get('goalDescription', '[No description]')}" for g in goals]
        ) + "\n"
    return profile_text + goals_text
