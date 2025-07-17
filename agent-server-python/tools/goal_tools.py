from google.cloud import firestore
from langchain_core.tools import tool
from datetime import datetime, timedelta
import pytz

APP_TO_DB_CATEGORY = {
    "vocational": "occupational",
}

def to_db_category(slug):
    return APP_TO_DB_CATEGORY.get(slug, slug)

def add_goal_to_firestore(user_id, goal_name, goal_description, category_slug, 
                         timeframe="Month", reminder_enabled=True, duration_weeks=6):
    """
    Add a goal to Firestore with proper timestamps and fields
    
    Args:
        user_id: User's Firebase UID
        goal_name: Name of the goal
        goal_description: Description of the goal
        category_slug: Wellness dimension (physical, mental, etc.)
        timeframe: Goal timeframe (Month, Week, Year)
        reminder_enabled: Whether to enable reminders
        duration_weeks: How many weeks the goal should run
    """
    db = firestore.Client()
    
    # Map app slug to db slug
    category_slug = to_db_category(category_slug)
    
    # Look up the category
    cat_docs = db.collection("goals_categories").where("cat_slug", "==", category_slug).stream()
    cat_doc = next(cat_docs, None)
    if not cat_doc:
        raise Exception(f"Category with slug '{category_slug}' not found.")
    
    cat_id = cat_doc.id
    cat_data = cat_doc.to_dict()
    
    # Create timestamps
    now = datetime.now(pytz.UTC)
    end_date = now + timedelta(weeks=duration_weeks)
    
    goal_data = {
        "endDate": end_date,
        "goalDescription": goal_description,
        "goalName": goal_name,
        "goalReminder": reminder_enabled,
        "startDate": now,
        "status": True,
        "timeFrame": timeframe,
        "user_id": user_id,
        "wellnessDimension": cat_id,
        "wellnessDimension_ref": f"/goals_categories/{cat_id}",      
    }
    
    # Add to Firestore
    doc_ref = db.collection("goals").add(goal_data)
    
    # Return the data with the document ID
    result = goal_data.copy()
    result["id"] = doc_ref[1].id  # doc_ref is a tuple (timestamp, document_reference)
    
    return result

@tool("add_goal")
def add_goal_tool(user_id: str, goal_name: str, goal_description: str, category_slug: str, 
                 timeframe: str = "Month", reminder_enabled: bool = True, duration_weeks: int = 6):
    """
    Add a new user goal to Firestore with category_slug (physical, mental, social, etc).
    
    Args:
        user_id: User's Firebase UID
        goal_name: Short name for the goal
        goal_description: Detailed description of what the goal entails
        category_slug: Wellness dimension slug (physical, mental, spiritual, etc.)
        timeframe: Goal timeframe - "Month", "Week", or "Year" (default: "Month")
        reminder_enabled: Whether to enable reminders (default: True)
        duration_weeks: How many weeks the goal should run (default: 6)
    """
    try:
        result = add_goal_to_firestore(
            user_id, 
            goal_name, 
            goal_description, 
            category_slug,
            timeframe,
            reminder_enabled,
            duration_weeks
        )
        print("INSIDE TOOL RESULT:", result, type(result))
        
        if isinstance(result, dict):
            # Convert datetime objects to strings for JSON serialization
            serializable_result = {}
            for key, value in result.items():
                if isinstance(value, datetime):
                    serializable_result[key] = value.isoformat()
                else:
                    serializable_result[key] = value
            return serializable_result
        elif hasattr(result, "dict"):
            return result.dict()
        else:
            return {"error": "Unexpected result type", "result": str(result)}
            
    except Exception as e:
        print(f"Error in add_goal_tool: {e}")
        return {"error": str(e), "success": False}


@tool("list_goal_categories")
def list_goal_categories():
    """List all available wellness dimension categories for goals."""
    try:
        db = firestore.Client()
        categories = []
        
        for doc in db.collection("goals_categories").stream():
            cat_data = doc.to_dict()
            categories.append({
                "id": doc.id,
                "name": cat_data.get("cat_name", "Unknown"),
                "slug": cat_data.get("cat_slug", "unknown"),
                "description": cat_data.get("cat_description", "")
            })
        
        return {"categories": categories}
    except Exception as e:
        return {"error": str(e), "categories": []}