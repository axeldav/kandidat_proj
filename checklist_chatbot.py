"""
How the tool calling workflow works:
1. The app sends system instructions + tools to gemini
2. The app sends user prompt to gemini
3. Gemini sends back a response with/without tool calls
4. App executes functions based on tool calls
5. App sends back response from functions to gemini + conversation history
6. Gemini sends back a response based on function result and conversation history

"""

import os
import json
import google.generativeai as genai
from utils import parts_to_text, load_mdr_rules
from tool_calling import (
    is_checklist_complete,
    record_answers,
    CHECK_LIST,
    TOOLS)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def build_system_prompt(checklist):
    questions = "\n".join(f"- {v['question']}" for v in checklist.values())
    return (
        "You are a friendly chatbot collecting two facts from the user.\n"
        "Ask naturally. If the user answers (even indirectly), record via the tool.\n\n"
        "Questions:\n" + questions +
        "\n\nWhen all are answered, thank the user briefly."
    )


def chat_with_llm(model, user_message, checklist, history):
    
    # 2. The app sends user prompt to gemini
    history.append({"role": "user", "parts": [user_message]})
    resp = model.generate_content(history, tools=TOOLS)
    text_out = parts_to_text(resp)

    # 3. Gemini sends back a response with/without tool calls
    # ... If there was a function call...
    if resp.candidates:
        cand = resp.candidates[0]
        for part in cand.content.parts:
            fc = getattr(part, "function_call", None)
            if fc and fc.name == "record_answers":
                args = dict(fc.args) if fc.args else {}
                
                # 4. App executes functions based on tool calls
                result = record_answers(checklist, args)

                # Add that gemini chose to use tool call to history
                history.append({"role": "model", "parts": cand.content.parts})

                # Add result from function to history
                history.append({
                    "role": "tool",
                    "parts": [{
                        "function_response": {
                            "name": "record_answers",
                            "response": result
                        }
                    }]
                })

                # 5. App sends back response from functions to gemini + conversation history
                follow = model.generate_content(history)

                text_out = parts_to_text(follow)
                break

    return text_out


def gather_info():

    #1. The app sends system instructions + tools to gemini
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=build_system_prompt(CHECK_LIST)
    )

    history = []
    llm_response = chat_with_llm(model, "Hello", CHECK_LIST, history)
    print(f"Chatbot: {llm_response} \n")

    while not is_checklist_complete(CHECK_LIST):

        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Chatbot: Bye!")
            return
        
        # 6. Gemini sends back a response based on function result and conversation history
        llm_response = chat_with_llm(model, user_input, CHECK_LIST, history)        
        print(f"Chatbot: {llm_response} \n")

    print("== SUMMARY ==")
    for k, v in CHECK_LIST.items():
        print(f"{v['question']} => {v['answer']}")


def classify():
    classifier_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="""
    You are a medical device classification (MDR) expert.
    Your Task is to classicate a medical device based on its characteristics and the MDR Classification Rules.
    You are allowed to structure data and use the rules to classify.
    """
    )

    classification_result = classifier_model.generate_content(
    f"""
    Device characteristics:
    {json.dumps(CHECK_LIST, indent=2)}
    
    MDR Classification Rules:
    {load_mdr_rules()}
    
    Classify the device based on its characteristics and the MDR Classification Rules.
    """
    )

    print(classification_result)

if __name__ == "__main__":
    gather_info()
    classify()
