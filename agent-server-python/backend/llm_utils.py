from backend.config import (
    gpt4o_router,
    gpt4o_with_tools,
    deepseek_with_tools,
)
from backend.goal_extraction import extract_goal_details, generate_confirmation_prompt
from backend.prompts.personas import PERSONA_PROMPTS
from tools.goal_tools import add_goal_tool, list_goal_categories
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from backend.rag_utils import format_profile_and_goals

def sanitize_history(history):
    sanitized = []
    for h in history:
        if hasattr(h, "role") and hasattr(h, "content"):
            sanitized.append({"role": h.role, "content": h.content})
        elif isinstance(h, dict):
            sanitized.append(h)
    return sanitized

async def route_message(user_message: str):
    system = (
        "You are a routing assistant for a wellness chatbot. "
        "Given a user's message, decide which wellness domain it best fits. "
        "Reply with only one word (all lowercase) from this list: "
        "'mental', 'physical', 'spiritual', 'vocational', 'environmental', 'financial', 'social', or 'intellectual'."
        " If it does not fit any, reply with 'main'."
    )
    try:
        routing_response = await gpt4o_router.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=user_message),
        ])
        route = routing_response.content.strip().lower()
        allowed = [
            "mental", "physical", "spiritual", "vocational", 
            "environmental", "financial", "social", "intellectual"
        ]
        return route if route in allowed else "main"
    except Exception as e:
        print(f"Routing error: {e}")
        return "main"

async def execute_tool_call(tool_call, user_id):
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    if user_id:
        tool_args["user_id"] = user_id  
    try:
        if tool_name in ("add_goal", "add_goal_tool"):
            return add_goal_tool.invoke(tool_args)
        elif tool_name == "list_goal_categories":
            return list_goal_categories.invoke(tool_args)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        print(f"Tool execution error: {e}")
        import traceback; traceback.print_exc()
        return {"error": str(e)}

async def get_reply(agent_type, history, user_data=None, user_id=None):
    print(f"Getting reply for agent_type: {agent_type}, user_id: {user_id}")
    lc_messages = []
    context_text = ""
    context_text = format_profile_and_goals(user_data) if user_data else ""
    persona_prompt = PERSONA_PROMPTS.get(agent_type, PERSONA_PROMPTS["main"])
    lc_messages.append(SystemMessage(content=f"{context_text}\n{persona_prompt}"))
    for h in history:
        if h["role"] == "user":
            lc_messages.append(HumanMessage(content=h["content"]))
        else:
            lc_messages.append(AIMessage(content=h["content"]))
    model_router = {
        "physical": deepseek_with_tools,
        "mental": gpt4o_with_tools,
        "spiritual": gpt4o_with_tools,
        "vocational": gpt4o_with_tools,
        "environmental": deepseek_with_tools,
        "financial": gpt4o_with_tools,
        "social": gpt4o_with_tools,
        "intellectual": gpt4o_with_tools,
        "main": deepseek_with_tools,
    }
    model = model_router.get(agent_type, gpt4o_with_tools)
    try:
        response = await model.ainvoke(lc_messages)
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                result = await execute_tool_call(tool_call, user_id)
                tool_results.append(result)
            lc_messages.append(response)
            for i, tool_call in enumerate(response.tool_calls):
                tool_result = tool_results[i]
                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
                lc_messages.append(tool_message)
            final_response = await model.ainvoke(lc_messages)
            if hasattr(final_response, 'content') and final_response.content:
                return final_response.content
            else:
                if tool_results and isinstance(tool_results[0], dict):
                    if "error" not in tool_results[0]:
                        return "Great! I've added your goal. 🚀 What would you like to work on next?"
                    else:
                        return f"I had trouble adding that goal: {tool_results[0].get('error', 'Unknown error')}. Could you clarify your goal or try again?"
                return "I've noted your goal request. What would you like to work on next?"
        if hasattr(response, 'content') and response.content:
            return response.content
        else:
            return "I'm here to help with your wellness journey! What would you like to work on today?"
    except Exception as model_error:
        print(f"Model invocation error: {model_error}")
        import traceback
        traceback.print_exc()
        return "I'm having trouble processing that right now. Could you try rephrasing your request?"
