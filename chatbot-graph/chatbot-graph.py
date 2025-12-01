# app.py
import os
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from typing import List

# --- Import from our new files ---
from state import State, get_field_options
from utils import handle_tool_call
from tools import TriageNode
from prompts import build_triage_prompt

# --- Configuration ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash") # Use a modern model

# This list *drives* the triage logic.
# To add a new field, just add its name here!
TRIAGE_FIELDS_ORDER: List[str] = [
    "device_characteristics",
    "duration",
    "primary_purpose",
    "contact_scope",
    "contacts_critical_systems",
]

# --- Nodes ---

def triage_node(state: State):
    """
    This node is now data-driven. It finds the next empty field
    from TRIAGE_FIELDS_ORDER and asks about it.
    """
    user_msg = state["text"]
    chat = model.start_chat(history=state["history"])
    reply = ""

    # Find the first field in our list that is still None
    next_field_to_ask = None
    for field in TRIAGE_FIELDS_ORDER:
        if state.get(field) is None:
            next_field_to_ask = field
            break # Found the next field to ask

    if next_field_to_ask:
        # --- We still have questions to ask ---
        print(f"[Flow] Triage needs field: {next_field_to_ask}")
        options = get_field_options(next_field_to_ask)
        prompt = build_triage_prompt(next_field_to_ask, options, user_msg)
        
        llm_response = chat.send_message(prompt, tools=ALL_TOOLS)
        reply = handle_tool_call(llm_response, chat, state)

    else:
        # --- All fields are filled! ---
        print("[Flow] Triage complete.")
        state["triage_done"] = True # Set the flag for our router
        
        prompt = f"All information is collected. Confirm this with the user and tell them you will now analyze the results.\nUser's last message: {user_msg}"
        llm_response = chat.send_message(prompt)
        reply = llm_response.text.strip()

    # Update history and return new state
    new_history = state["history"] + [
        {"role": "user",  "parts": [{"text": user_msg}]},
        {"role": "model", "parts": [{"text": reply}]},
    ]
    return { **state, "history": new_history }


def second_node(state: State):
    """A placeholder for the next step after triage."""
    print("[Flow] Reached second_node.")
    reply = "This is the second node, for non-software devices."
    new_history = state["history"] + [
        {"role": "user",  "parts": [{"text": state["text"]}]},
        {"role": "model", "parts": [{"text": reply}]},
    ]
    return { **state, "history": new_history }

# ... add other nodes like software_node, invasive_node etc. ...


# --- Graph Definition ---

def choose_next(state: State):
    """
    This router checks if triage is
    done first, then routes to the correct flow.
    """
    if state.get("triage_done") is not True:
        # Triage is not finished, loop back.
        return "triage_node"

    # Triage is done! Now we can route based on the results.
    print("[Flow] Routing post-triage.")
    if state.get("device_type") == "SOFTWARE":
        # return "software_node" # (You would add this node)
        return "second_node" # Placeholder
    else:
        return "second_node"

builder = StateGraph(State)

builder.add_node("triage_node", triage_node)
builder.add_node("second_node", second_node)
# builder.add_node("software_node", software_node) # etc.

builder.set_entry_point("triage_node")

builder.add_conditional_edges(
    "triage_node",  # Run router AFTER triage_node
    choose_next,
    {
        # If choose_next returns "triage_node", it means we're not done.
        # We MUST END the graph here to wait for the user's next input.
        "triage_node": END, 
        
        # If choose_next returns "second_node", triage is done.
        # Go to the second node.
        "second_node": "second_node",
        
        # Add any other nodes you might route to
        # "software_node": "software_node",
    }
)

builder.add_edge("second_node", END) # second_node also ends
# builder.add_edge("software_node", END)

graph = builder.compile()


# --- Main Application Loop ---
if __name__ == "__main__":
    
    # Use the keys from State to build the initial state dynamically
    initial_state = {key: None for key in State.__annotations__}
    initial_state.update({
        "text": "",
        "history": [],
        "triage_done": False,
        "needs_non_invasive_section": False,
        "needs_invasive_section": False,
        "needs_active_section": False,
        "needs_software_section": False,
        "possible_special_rules": False,
    })

    print("Bot: Hello! I can help you with medical device classification.")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            current_state = initial_state.copy()
            current_state["text"] = user_input
            
            final_state = graph.invoke(current_state)
            
            model_reply = final_state["history"][-1]["parts"][0]["text"]
            print(f"Bot: {model_reply}")
            
            initial_state = final_state
            
        except KeyboardInterrupt:
            print("\nExiting chat.")
            break

    print("\n--- Final State ---")
    import json
    print(json.dumps(final_state, indent=2))