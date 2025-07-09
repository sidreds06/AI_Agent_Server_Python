import re
from backend.config import gpt4o_router

async def extract_goal_details(user_message: str, conversation_history: list = None) -> dict:
    details = {
        "goal_name": None,
        "goal_description": None,
        "category_slug": None,
        "timeframe": "Month",  # default
        "reminder_enabled": True,  # default
        "duration_weeks": 6,  # default
        "missing_fields": []
    }
    message_lower = user_message.lower()
    timeframe_patterns = {
        "week": ["week", "weekly", "7 days"],
        "month": ["month", "monthly", "30 days"],
        "quarter": ["quarter", "quarterly", "3 months"],
        "year": ["year", "yearly", "annual", "12 months"]
    }
    for timeframe, patterns in timeframe_patterns.items():
        if any(pattern in message_lower for pattern in patterns):
            details["timeframe"] = timeframe.capitalize()
            break
    duration_match = re.search(r'(\d+)\s*(week|month|day)s?', message_lower)
    if duration_match:
        num, unit = duration_match.groups()
        if unit == "week":
            details["duration_weeks"] = int(num)
        elif unit == "month":
            details["duration_weeks"] = int(num) * 4
        elif unit == "day":
            details["duration_weeks"] = max(1, int(num) // 7)
    goal_name_patterns = [
        r'(?:goal|want|need|plan) (?:to|is to) (.+?)(?:\.|,|$)',
        r'i want to (.+?)(?:\.|,|$)',
        r'help me (?:to )?(.+?)(?:\.|,|$)',
        r'set a goal (?:to )?(.+?)(?:\.|,|$)',
        r'my goal is (?:to )?(.+?)(?:\.|,|$)',
        r'add (.+?) to my goals?',
        r'can you add (.+?) to my goals?'
    ]
    for pattern in goal_name_patterns:
        match = re.search(pattern, message_lower)
        if match:
            goal_name = match.group(1).strip()
            goal_name = re.sub(r'\s+', ' ', goal_name)
            details["goal_name"] = goal_name[:50]
            details["goal_description"] = user_message.strip()
            break
    # LLM fallback for goal name
    if not details["goal_name"]:
        llm_title = await gpt4o_router.ainvoke([
            {
                "role": "system",
                "content": "Return a concise (≤50 chars) goal title:"
            },
            {
                "role": "user",
                "content": user_message
            }
        ])
        details["goal_name"] = llm_title.content.strip()[:50]
    category_keywords = {
        "physical": ["exercise", "workout", "fitness", "weight", "lose", "gain", "run", "walk", "swim", "gym", "strength", "cardio", "nutrition", "diet", "water", "drink", "hydrate", "sleep", "rest"],
        "mental": ["stress", "anxiety", "meditation", "mindfulness", "therapy", "mental health", "depression", "mood", "emotional", "journal", "gratitude"],
        "spiritual": ["meditate", "pray", "spiritual", "faith", "religion", "mindfulness", "purpose", "meaning", "soul", "inner peace"],
        "financial": ["save", "budget", "money", "invest", "debt", "financial", "income", "expense", "retirement", "emergency fund"],
        "social": ["friends", "family", "social", "relationship", "network", "community", "volunteer", "connect", "communication"],
        "intellectual": ["read", "learn", "study", "course", "book", "skill", "knowledge", "education", "research", "write"],
        "vocational": ["career", "job", "work", "professional", "promotion", "skill", "certification", "resume", "interview", "business"],
        "environmental": ["environment", "green", "eco", "sustainable", "recycle", "nature", "climate", "pollution", "conservation"]
    }
    if not details["category_slug"]:
        for category, keywords in category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                details["category_slug"] = category
                break
    required_fields = ["goal_name", "category_slug"]
    for field in required_fields:
        if not details[field]:
            details["missing_fields"].append(field)
    return details

def generate_confirmation_prompt(details: dict) -> str:
    missing = details["missing_fields"]
    if not missing:
        return None
    prompts = []
    if "goal_name" in missing:
        prompts.append("What would you like to name this goal?")
    if "category_slug" in missing:
        prompts.append("Which wellness area does this goal focus on? (Physical, Mental, Spiritual, Social, Financial, Intellectual, Career, or Environmental)")
    if len(prompts) == 1:
        return prompts[0]
    elif len(prompts) == 2:
        return f"{prompts[0]} Also, {prompts[1].lower()}"
    else:
        return "Could you provide a bit more detail about your goal?"
