# app.py
import os
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from state import State
from utils import calculate_pending_nodes
from tools import TriageNode, InvasiveNode, ActiveNode, SoftwareNode

# --- LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0 
)

# ============================================================
# NODE ENGINE
# ============================================================

def run_node(state: State, tool_class: type[BaseModel], node_name: str, is_triage: bool = False) -> dict:
    """Generic engine: Intent Check → (Clarify OR Extract) → Find Missing → Ask."""
    print(f"\n[DEBUG] Running Node: {node_name.upper()}") 
    
    messages = state.messages
    updates = {}
    
    user_input = ""
    last_ai_msg = "None"

    # --- SETUP CONTEXT ---
    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        if len(messages) > 1 and isinstance(messages[-2], AIMessage):
            last_ai_msg = messages[-2].content

    # ============================================================
    # STEP 1: CHECK INTENT (CLARIFICATION VS ANSWER)
    # ============================================================
    
    is_clarification = False
    
    if user_input:
        print(f"[DEBUG] Checking intent for input: '{user_input}'...")
        
        # We tell the model to be very strict with classification
        intent_prompt = f"""
        Analyze the conversation.
        
        Bot asked: "{last_ai_msg}"
        User replied: "{user_input}"
        
        Task: Determine if the User is answering the question OR asking for help/clarification.
        
        Return ONLY one word:
        - "ANSWER" (if user provides info, says yes/no, or ignores the question)
        - "CLARIFICATION" (if user asks "what do you mean?", "I don't understand", "define X")
        """
        
        intent_result = llm.invoke(intent_prompt).content.strip().upper()
        print(f"[DEBUG] Intent detected: {intent_result}")
        
        if "CLARIFICATION" in intent_result:
            is_clarification = True

    # ============================================================
    # STEP 2: HANDLE CLARIFICATION (IF NEEDED)
    # ============================================================
    
    if is_clarification:
        print("[DEBUG] Handling clarification request...")
        
        explain_prompt = f"""
        The user did not understand the previous question.
        
        Previous Question: "{last_ai_msg}"
        User's Question: "{user_input}"
        
        Task:
        1. Explain the medical device concept clearly and simply.
        2. Re-state the original question in a friendlier way.
        
        CRITICAL OUTPUT RULES:
        - Speak directly to the user.
        - Do NOT provide a list of options.
        - Do NOT say "Here is an explanation". Just explain it.
        """
        explanation = llm.invoke(explain_prompt).content
        return {"messages": [AIMessage(content=explanation)]}

    # ============================================================
    # STEP 3: EXTRACT DATA (ONLY IF NOT CLARIFICATION)
    # ============================================================
    
    current_facts = {k: getattr(state, k, None) for k in tool_class.model_fields}
    
    prompt = f"""
    TASK: Update the medical device data based on the conversation.
    
    CONTEXT:
    1. Current Known Data: {current_facts}
    2. The Bot just asked: "{last_ai_msg}"
    3. The User just answered: "{user_input}"
    
    INSTRUCTIONS:
    - Update fields based strictly on the User's answer.
    - If the user says "No" or "Yes", apply it ONLY to the field relevant to the Bot's last question.
    """

    try:
        result = llm.with_structured_output(tool_class).invoke(prompt)
        extracted_data = result.model_dump(exclude_unset=True, exclude_none=True)
        
        if extracted_data:
            print(f"[DEBUG] Extracted: {extracted_data}")
            updates.update(extracted_data)
        else:
            print(f"[DEBUG] No data extracted.")
            
    except Exception as e:
        print(f"[Extract Error]: {e}")

    # ============================================================
    # STEP 4: FIND MISSING & ACT
    # ============================================================
    
    missing = None
    temp_state = state.model_copy(update=updates)
    
    for name, info in tool_class.model_fields.items():
        if getattr(temp_state, name, None) is None:
            missing = (name, info.description)
            break

    if missing:
        name, desc = missing
        print(f"[DEBUG] Missing field: {name}")
        
        # --- FIX IS HERE: STRICT SINGLE OUTPUT ---
        q_prompt = f"""
        You are a helpful Medical Device Classification Assistant.
        You need to collect information about this field: '{name}'
        Field Description: {desc}
        
        Task: Ask the user a SINGLE, clear question to get this information.
        
        CRITICAL OUTPUT RULES:
        - Return ONLY the question text.
        - Do NOT give options (like "Option 1", "Option 2").
        - Do NOT add meta-text like "Here is a question".
        - If it is a Yes/No question, keep it simple.
        - If it is an Enum (multiple choice), list the options naturally in the sentence.
        """
        q = llm.invoke(q_prompt).content
        
        # Cleanup: sometimes LLMs still wrap text in quotes or add newlines
        q_clean = q.strip().replace('"', '')
        
        updates["messages"] = [AIMessage(content=q_clean)]
    
    elif is_triage:
        print("[DEBUG] Triage complete.")
        merged = state.model_copy(update=updates)
        updates["pending_nodes"] = calculate_pending_nodes(merged)
        updates["triage_complete"] = True
        updates["messages"] = [AIMessage(content="✓ Triage complete. Moving to specifics...")]
    
    else:
        print(f"[DEBUG] Node {node_name} done.")
        updates["pending_nodes"] = list(state.pending_nodes[1:]) if state.pending_nodes else []
        updates["messages"] = [AIMessage(content=f"✓ {node_name} data collected.")]

    return updates

# ============================================================
# NODES
# ============================================================

def triage_node(state: State) -> dict:
    return run_node(state, TriageNode, "triage", is_triage=True)

def invasive_node(state: State) -> dict:
    return run_node(state, InvasiveNode, "invasive")

def active_node(state: State) -> dict:
    return run_node(state, ActiveNode, "active")

def software_node(state: State) -> dict:
    return run_node(state, SoftwareNode, "software")

def classify_node(state: State) -> dict:
    print("\n[DEBUG] Running Node: CLASSIFY")
    exclude = {"messages", "pending_nodes", "triage_complete"}
    facts = {k: v for k, v in state.model_dump().items() if v is not None and k not in exclude}
    
    prompt = f"""Classify this medical device according to MDR (EU) 2017/745 Annex VIII.

    Facts gathered:
    {facts}

    Output format:
    - **Class**: (I, IIa, IIb, or III)
    - **Rule**: (Applicable Rule numbers)
    - **Reasoning**: Brief explanation.
    """

    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=f"📋 CLASSIFICATION REPORT:\n\n{response.content}")]}


# ============================================================
# ROUTER
# ============================================================

def router(state: State) -> str:
    if state.messages and isinstance(state.messages[-1], AIMessage):
        last_msg = state.messages[-1].content
        if "✓" not in last_msg and "📋" not in last_msg:
             return END

    if not state.triage_complete:
        return "triage"
    if state.pending_nodes:
        return state.pending_nodes[0]
    return "classify"


# ============================================================
# GRAPH CONFIG
# ============================================================

builder = StateGraph(State)

builder.add_node("triage", triage_node)
builder.add_node("invasive", invasive_node)
builder.add_node("active", active_node)
builder.add_node("software", software_node)
builder.add_node("classify", classify_node)

builder.set_entry_point("triage")

ROUTES = {"triage": "triage", "invasive": "invasive", "active": "active", "software": "software", "classify": "classify", END: END}

builder.add_conditional_edges("triage", router, ROUTES)
builder.add_conditional_edges("invasive", router, ROUTES)
builder.add_conditional_edges("active", router, ROUTES)
builder.add_conditional_edges("software", router, ROUTES)
builder.add_edge("classify", END)

graph = builder.compile()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("🏥 MDR Bot (Strict) | 'exit' = quit | 'state' = show\n")
    
    current_state = State()
    print("Bot: Please describe the medical device you want to classify.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "state":
                print("\n--- CURRENT STATE ---")
                for k, v in current_state.model_dump().items():
                    if v not in (None, [], False) and k != "messages":
                        print(f"{k}: {v}")
                print("---------------------\n")
                continue
            if not user_input:
                continue
            
            current_state.messages.append(HumanMessage(content=user_input))
            result = graph.invoke(current_state)
            current_state = State(**{k: v for k, v in result.items() if k in State.model_fields})
            
            if current_state.messages and isinstance(current_state.messages[-1], AIMessage):
                print(f"\nBot: {current_state.messages[-1].content}\n")
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error]: {e}")