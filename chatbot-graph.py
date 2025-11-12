# langgraph_gemini_console_input.py
# pip install langgraph google-generativeai
# export GOOGLE_API_KEY="your_key"

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
import os
import google.generativeai as genai

class State(TypedDict):
    text: str
    history: List[Dict[str, Any]]

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

def first(state: State):
    user_msg = state["text"]
    chat = model.start_chat(history=state["history"])
    resp = chat.send_message(f"Answer briefly: {user_msg}")
    reply = resp.text.strip()

    new_history = state["history"] + [
        {"role": "user",  "parts": [{"text": user_msg}]},
        {"role": "model", "parts": [{"text": reply}]},
    ]
    return {
        "text": state["text"] + f" -> gemini:{reply}",
        "history": new_history
    }

def second(state: State):
    return {"text": state["text"] + " -> second"}

builder = StateGraph(State)
builder.add_node("first", first)
builder.add_node("second", second)
builder.set_entry_point("first")
builder.add_edge("first", "second")
builder.add_edge("second", END)
graph = builder.compile()

# ---- minimal console input (one turn) ----
user_input = input("You: ").strip()
state = {"text": user_input, "history": []}
final_state = graph.invoke(state)
print("Bot:", final_state["text"])   # contains "... -> gemini:<reply> -> second"

# If you want a tiny loop (optional, still minimal):
# history = final_state["history"]
# while True:
#     user_input = input("You: ").strip()
#     if not user_input or user_input.lower() in {"quit", "exit"}:
#         break
#     final_state = graph.invoke({"text": user_input, "history": history})
#     print("Bot:", final_state["text"])
#     history = final_state["history"]
