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

# --- CONFIG ---
CALL_DELAY = 4  # Seconds between API calls

# --- LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0 
)

# --- RATE-LIMITED WRAPPER ---
def call_llm(prompt: str, structured_schema: type[BaseModel] | None = None) -> str | BaseModel:
    """Single wrapper for all LLM calls with rate limiting."""
    time.sleep(CALL_DELAY)
    
    if structured_schema:
        return llm.with_structured_output(structured_schema).invoke(prompt)
    return llm.invoke(prompt).content


# --- CONDITIONAL FIELD LOGIC ---
CONDITIONAL_FIELDS = {
    # SpecialRulesNode
    "disinfects_invasive_devices": ("is_disinfecting_device", True),
    "tissue_contacts_intact_skin_only": ("contains_human_or_animal_tissue", True),
    "nanomaterial_exposure": ("contains_nanomaterial", True),
    "inhalation_essential_impact": ("is_inhalation_drug_delivery", True),
    "substance_systemic_absorption": ("is_substance_absorbed_in_body", True),
    # InvasiveNode
    "orifice_location": ("is_surgically_invasive", False),
    "placed_in_teeth": ("undergoes_chemical_change", True),
    # ActiveNode
    "energy_is_hazardous": ("administers_energy", True),
    "immediate_danger_monitoring": ("monitors_vital_functions", True),
    "controls_active_implantable": ("controls_other_device", True),
    # NonInvasiveNode
    "is_blood_bag": ("channels_fluids_for_infusion", True),
    "is_simple_processing": ("modifies_fluids_for_body", True),
    "wound_use_type": ("contacts_injured_skin", True),
}


# ============================================================
# NODE ENGINE
# ============================================================

def run_node(state: State, tool_class: type[BaseModel], node_name: str, is_triage: bool = False) -> dict:
    print(f"\n[DEBUG] Running Node: {node_name.upper()}") 
    
    if is_triage and state.triage_complete:
        print(f"[DEBUG] Triage complete, passing to router...")
        return {}
    
    messages = state.messages
    updates = {}
    
    # --- 1. CHECK FOR NEW USER INPUT ---
    user_input = ""
    last_ai_msg = "None"
    should_process = False

    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        should_process = True
        if len(messages) > 1 and isinstance(messages[-2], AIMessage):
            last_ai_msg = messages[-2].content

    if should_process:
        print(f"[DEBUG] Processing: '{user_input}'")
    else:
        print(f"[DEBUG] No new input, skipping to missing field check.")

    # --- 2. INTENT CHECK ---
    is_clarification = False
    
    if should_process and user_input:
        intent_prompt = f"""Bot asked: "{last_ai_msg}"
User replied: "{user_input}"

Is the user ANSWERING or asking for CLARIFICATION?
Reply ONLY: ANSWER or CLARIFICATION"""
        
        try:
            result = call_llm(intent_prompt)
            is_clarification = "CLARIFICATION" in result.upper()
            print(f"[DEBUG] Intent: {'CLARIFICATION' if is_clarification else 'ANSWER'}")
        except Exception as e:
            print(f"[Intent Error]: {e}")

    # --- 3. HANDLE CLARIFICATION ---
    if is_clarification:
        explain_prompt = f"""User didn't understand: "{last_ai_msg}"
They asked: "{user_input}"

Explain simply, then re-ask the original question."""
        
        return {"messages": [AIMessage(content=call_llm(explain_prompt))]}

    # --- 4. EXTRACT DATA ---
    if should_process and not is_clarification:
        current_facts = {k: getattr(state, k, None) for k in tool_class.model_fields}
        
        extract_prompt = f"""Update medical device data based on user's answer.

Known data: {current_facts}
Bot asked: "{last_ai_msg}"
User answered: "{user_input}"

Rules:
- Update fields based on what the user explicitly stated
- If user says Yes/No, apply it to the field from the bot's question
- Do not guess unrelated fields"""

        try:
            result = call_llm(extract_prompt, structured_schema=tool_class)
            # Changed: removed exclude_unset to capture all values
            extracted = result.model_dump(exclude_none=True)
            if extracted:
                print(f"[DEBUG] Extracted: {extracted}")
                updates.update(extracted)
        except Exception as e:
            print(f"[Extract Error]: {e}")

    # --- 5. FIND NEXT MISSING FIELD ---
    # Merge updates with current state
    merged_data = state.model_dump()
    merged_data.update(updates)
    temp_state = State(**{k: v for k, v in merged_data.items() if k in State.model_fields})
    
    missing = None
    
    for name, info in tool_class.model_fields.items():
        current_value = getattr(temp_state, name, None)
        
        # Skip if already filled
        if current_value is not None:
            continue
            
        # Check if this is a conditional field
        if name in CONDITIONAL_FIELDS:
            parent_field, required_value = CONDITIONAL_FIELDS[name]
            parent_value = getattr(temp_state, parent_field, None)
            
            print(f"[DEBUG] Checking conditional: {name} (parent {parent_field}={parent_value}, required={required_value})")
            
            # Skip if parent hasn't been answered yet
            if parent_value is None:
                print(f"[DEBUG] Skipping {name}: parent not answered yet")
                continue
            
            # Skip if parent doesn't match required value
            if parent_value != required_value:
                print(f"[DEBUG] Skipping {name}: parent={parent_value}, needed={required_value}")
                continue
        
        missing = (name, info.description)
        break

    if missing:
        name, desc = missing
        print(f"[DEBUG] Missing: {name}")
        
        device_name = temp_state.device_name or "the device"
        
        q_prompt = f"""You are a medical device classification assistant helping classify "{device_name}".

You need to find out: {desc}

Ask ONE simple question about the {device_name} to determine this.
- Use plain language a manufacturer would understand
- Ask specifically about what the description says
- Do NOT ask generic questions like "is it used inside the body"

Return only the question, nothing else."""
        
        question = call_llm(q_prompt).strip().replace('"', '')
        updates["messages"] = [AIMessage(content=question)]
    
    elif is_triage:
        print("[DEBUG] Triage complete.")
        merged = State(**{k: v for k, v in {**state.model_dump(), **updates}.items() if k in State.model_fields})
        updates["pending_nodes"] = calculate_pending_nodes(merged)
        updates["triage_complete"] = True
        updates["messages"] = [AIMessage(content="✓ Triage complete. Moving to specifics...")]
    
    else:
        print(f"[DEBUG] {node_name} complete.")
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
    
    prompt = f"""Classify this medical device per MDR (EU) 2017/745 Annex VIII.

Facts: {facts}

Format:
- **Class**: (I, IIa, IIb, or III)
- **Rule**: (Rule numbers)
- **Reasoning**: Brief explanation."""

    return {"messages": [AIMessage(content=f"📋 CLASSIFICATION REPORT:\n\n{call_llm(prompt)}")]}


# ============================================================
# ROUTER
# ============================================================

def router(state: State) -> str:
    """Route based on last message type."""
    if state.messages and isinstance(state.messages[-1], AIMessage):
        last_msg = state.messages[-1].content
        
        if "✓" not in last_msg and "📋" not in last_msg:
            print("[DEBUG] Router: Question -> END")
            return END
        
        print("[DEBUG] Router: Status update -> CONTINUE")

    if not state.triage_complete:
        return "triage"
    
    if state.pending_nodes:
        next_node = state.pending_nodes[0]
        print(f"[DEBUG] Router -> {next_node}")
        return next_node
        
    return "classify"


# ============================================================
# GRAPH
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

ROUTES = {
    "triage": "triage",
    "non_invasive": "non_invasive", 
    "invasive": "invasive",
    "active": "active",
    "software": "software",
    "special_rules": "special_rules",
    "classify": "classify",
    END: END
}

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
    print("🏥 MDR Bot | 'exit' = quit | 'state' = show\n")
    
    current_state = State()
    print("Bot: Please describe the medical device you want to classify.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "state":
                print("\n--- STATE ---")
                for k, v in current_state.model_dump().items():
                    if v not in (None, [], False) and k != "messages":
                        print(f"{k}: {v}")
                print("-------------\n")
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