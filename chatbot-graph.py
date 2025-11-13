# langgraph_gemini_console_input_happy.py
# pip install langgraph google-generativeai
# export GEMINI_API_KEY="your_key"

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import os
import google.generativeai as genai

class State(TypedDict):
    text: str
    history: List[Dict[str, Any]]
    happy: Optional[bool]  # <--- NEW: will be True if tool is called, else None

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ---- minimal tool setup ----
# Tool has no parameters; if the model calls it, we mark the user as happy.
TOOLS = [{
    "function_declarations": [{
        "name": "set_happy_true",
        "description": "Mark that the user is happy.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        },
    }]
}]

def first(state: State):
    user_msg = state["text"]
    chat = model.start_chat(history=state["history"])

    # Tell Gemini *when* to use the tool
    prompt = (
        "Answer briefly to the user.\n"
        "If the user clearly says they are happy, "
        "call the tool set_happy_true."
        f"\nUser: {user_msg}"
    )

    resp = chat.send_message(prompt, tools=TOOLS)

    happy = state.get("happy")  # start from previous value (usually None)

    # --- check if model decided to call the tool ---
    parts = resp.candidates[0].content.parts if resp.candidates else []
    if parts and hasattr(parts[0], "function_call"):
        fc = parts[0].function_call
        if fc.name == "set_happy_true":
            # We treat the tool as "called" → happy = True
            happy = True

            # Send a function_response back so the model can produce final text
            resp2 = chat.send_message([{
                "function_response": {
                    "name": "set_happy_true",
                    "response": {"happy": True}
                }
            }])
            reply = resp2.text.strip()
        else:
            reply = resp.text.strip()
    else:
        reply = resp.text.strip()

    new_history = state["history"] + [
        {"role": "user",  "parts": [{"text": user_msg}]},
        {"role": "model", "parts": [{"text": reply}]},
    ]

    return {
        "text": state["text"] + f" -> gemini:{reply}",
        "history": new_history,
        "happy": happy,  # <--- state now carries the happy flag
    }

def second(state: State):
    return {"text": state["text"] + " -> second (happy route)"}

builder = StateGraph(State)
builder.add_node("first", first)
builder.add_node("second", second)
builder.set_entry_point("first")

# ---- conditional routing based on happy ----
def choose_next(state: State):
    # Only go to 'second' if happy is True; otherwise stop the graph
    return state.get("happy") is True

builder.add_conditional_edges(
    "first",
    choose_next,
    {
        True: "second",   # happy → go to second node
        False: END,       # not happy (None/False) → end graph
    }
)

builder.add_edge("second", END)
graph = builder.compile()

# ---- minimal console input (one turn) ----
user_input = input("You: ").strip()
state: State = {"text": user_input, "history": [], "happy": None}
final_state = graph.invoke(state)

print("Bot state:", final_state)
print("Bot text:", final_state["text"])
print("Happy flag:", final_state["happy"])
