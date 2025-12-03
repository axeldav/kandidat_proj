# app.py
import os
import time
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from state import State
from utils import calculate_pending_nodes
from tools import TriageNode, NonInvasiveNode, InvasiveNode, ActiveNode, SoftwareNode, SpecialRulesNode

# --- LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0 
)

# ============================================================
# NODE ENGINE
# ============================================================

def run_node(state: State, tool_class: type[BaseModel], node_name: str, is_triage: bool = False) -> dict:
    """
    Robust engine: 
    1. Checks if input is fresh (User) or stale (AI transition).
    2. Checks Intent (Answer vs Clarification).
    3. Extracts Data.
    4. Finds missing fields & Asks single questions.
    """
    print(f"\n[DEBUG] Running Node: {node_name.upper()}") 
    
    # --- EARLY EXIT: Skip triage if already complete ---
    # This prevents triage from "consuming" user input meant for other nodes
    if is_triage and state.triage_complete:
        print(f"[DEBUG] Triage already complete, passing through to router...")
        return {}  # Return empty - don't process input, let router handle it
    
    messages = state.messages
    updates = {}
    
    # --- 1. DETERMINE IF WE SHOULD PROCESS INPUT ---
    # We only analyze input if the LAST message was from a Human.
    # If the last message was from AI (e.g., "Triage complete"), we skip extraction
    # and go straight to finding the next missing field.
    
    user_input = ""
    last_ai_msg = "None"
    should_process_input = False

    if messages:
        last_message = messages[-1]
        
        if isinstance(last_message, HumanMessage):
            user_input = last_message.content
            should_process_input = True
            
            # Get context (the question the user answered)
            if len(messages) > 1 and isinstance(messages[-2], AIMessage):
                last_ai_msg = messages[-2].content

    if should_process_input:
        print(f"[DEBUG] Processing user input: '{user_input}'")
    else:
        print(f"[DEBUG] No new user input (Node transition). Skipping extraction.")


    # --- 2. INTENT CHECK (Only if input is fresh) ---
    is_clarification = False
    
    if should_process_input and user_input:
        intent_prompt = f"""
        Analyze the conversation.
        Bot asked: "{last_ai_msg}"
        User replied: "{user_input}"
        
        Task: Determine if the User is answering the question OR asking for clarification.
        
        Return ONLY one word:
        - "ANSWER" (if user answers or ignores the question)
        - "CLARIFICATION" (if user asks "what do you mean?", "define X", "I don't understand")
        """
        
        try:
            time.sleep(2.5)  # Rate limit protection
            intent_result = llm.invoke(intent_prompt).content.strip().upper()
            print(f"[DEBUG] Intent detected: {intent_result}")
            if "CLARIFICATION" in intent_result:
                is_clarification = True
        except Exception as e:
            print(f"[Intent Error]: {e}")


    # --- 3. HANDLE CLARIFICATION (If needed) ---
    if is_clarification:
        print("[DEBUG] Handling clarification request...")
        time.sleep(2.5)  # Rate limit protection
        
        explain_prompt = f"""
        The user did not understand the previous question.
        Previous Question: "{last_ai_msg}"
        User's Question: "{user_input}"
        
        Task:
        1. Explain the concept clearly and simply.
        2. Re-state the original question in a friendly way.
        
        CRITICAL: Do not give a list of options. Just explain and ask.
        """
        explanation = llm.invoke(explain_prompt).content
        return {"messages": [AIMessage(content=explanation)]}


    # --- 4. EXTRACT DATA (Only if Answer & Input is fresh) ---
    if should_process_input and not is_clarification:
        current_facts = {k: getattr(state, k, None) for k in tool_class.model_fields}
        
        prompt = f"""
        TASK: Update the medical device data.
        
        CONTEXT:
        1. Known Data: {current_facts}
        2. Bot asked: "{last_ai_msg}"
        3. User answered: "{user_input}"
        
        INSTRUCTIONS:
        - specific: Update fields based strictly on the User's answer.
        - context: If User says "Yes"/"No", apply it ONLY to the field relevant to the Bot's last question.
        - strict: Do NOT guess fields unrelated to the answer.
        """

        try:
            time.sleep(2.5)  # Rate limit protection
            result = llm.with_structured_output(tool_class).invoke(prompt)
            extracted_data = result.model_dump(exclude_unset=True, exclude_none=True)
            
            if extracted_data:
                print(f"[DEBUG] Extracted: {extracted_data}")
                updates.update(extracted_data)
            else:
                print(f"[DEBUG] No data extracted.")
        except Exception as e:
            print(f"[Extract Error]: {e}")


    # --- 5. FIND MISSING & ACT (Always runs) ---
    # We check the updated state to see what is still missing.
    
    missing = None
    temp_state = state.model_copy(update=updates)
    
    for name, info in tool_class.model_fields.items():
        if getattr(temp_state, name, None) is None:
            missing = (name, info.description)
            break

    if missing:
        name, desc = missing
        print(f"[DEBUG] Missing field: {name}")
        
        time.sleep(2.5)  # Rate limit protection
        
        q_prompt = f"""
        You are a helpful Medical Device Classification Assistant.
        You need information about: '{name}'
        Description: {desc}
        
        Task: Ask the user a SINGLE, clear question to get this information.
        
        CRITICAL OUTPUT RULES:
        - Return ONLY the question text.
        - Do NOT give options (A, B, C).
        - Do NOT use bullet points.
        - Do NOT add meta-text like "Here is the question".
        """
        q = llm.invoke(q_prompt).content
        q_clean = q.strip().replace('"', '') # Clean up quotes
        
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

def non_invasive_node(state: State) -> dict:
    return run_node(state, NonInvasiveNode, "non_invasive")

def invasive_node(state: State) -> dict:
    return run_node(state, InvasiveNode, "invasive")

def active_node(state: State) -> dict:
    return run_node(state, ActiveNode, "active")

def software_node(state: State) -> dict:
    return run_node(state, SoftwareNode, "software")

def special_rules_node(state: State) -> dict:
    return run_node(state, SpecialRulesNode, "special_rules")

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
    """
    Decides flow:
    - If AI just asked a question -> STOP (END) to wait for user.
    - If AI just gave a status update (✓) -> CONTINUE automatically.
    - Otherwise -> Route to next node logic.
    """
    
    # 1. Check the very last message
    if state.messages and isinstance(state.messages[-1], AIMessage):
        last_msg = state.messages[-1].content
        
        # LOGIC: 
        # If it contains "✓" (Node done) or "📋" (Final Report), we generally want to CONTINUE 
        # to the next logic step or finish.
        # BUT if it does NOT contain those, it's a question. We MUST stop.
        
        if "✓" not in last_msg and "📋" not in last_msg:
             print("[DEBUG] Router: AI asked a question -> STOP (wait for input).")
             return END
        else:
             print(f"[DEBUG] Router: Status update '{last_msg}' -> CONTINUE flow.")

    # 2. Logic Flow
    if not state.triage_complete:
        return "triage"
    
    if state.pending_nodes:
        next_node = state.pending_nodes[0]
        print(f"[DEBUG] Router -> Next pending node: {next_node}")
        return next_node
        
    return "classify"


# ============================================================
# GRAPH CONFIG
# ============================================================

builder = StateGraph(State)

builder.add_node("triage", triage_node)
builder.add_node("non_invasive", non_invasive_node)
builder.add_node("invasive", invasive_node)
builder.add_node("active", active_node)
builder.add_node("software", software_node)
builder.add_node("special_rules", special_rules_node)
builder.add_node("classify", classify_node)

builder.set_entry_point("triage")

ROUTES = {"triage": "triage", "non_invasive": "non_invasive", "invasive": "invasive", "active": "active", "software": "software", "special_rules": "special_rules", "classify": "classify", END: END}

builder.add_conditional_edges("triage", router, ROUTES)
builder.add_conditional_edges("non_invasive", router, ROUTES)
builder.add_conditional_edges("invasive", router, ROUTES)
builder.add_conditional_edges("active", router, ROUTES)
builder.add_conditional_edges("software", router, ROUTES)
builder.add_conditional_edges("special_rules", router, ROUTES)
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