# --- Tool 1: Logic ---
def set_field(state, field_name, field_value):
    """The actual Python logic for the set_field tool."""
    
    if field_name not in State.__annotations__:
        print(f"[TOOL ERROR] Unknown field: {field_name}")
        return {"status": "error", "message": f"Unknown field {field_name}"}

    # Optional: Validate the value against the Literal options
    options = get_field_options(field_name)
    if options and field_value not in options:
        # Handle boolean conversion
        if isinstance(field_value, bool):
             state[field_name] = field_value
             print(f"[TOOL CALL] set_field({field_name}={field_value})")
             return {"status": "success", "field": field_name, "value": field_value}
        
        print(f"[TOOL WARNING] Invalid value '{field_value}' for {field_name}. Valid: {options}")
        # You could return an error, but for now we'll just warn
        # return {"status": "error", "message": f"Invalid value {field_value}"}
    
    # Update state in-place
    print(f"[TOOL CALL] set_field({field_name}={field_value})")
    state[field_name] = field_value
    
    return {"status": "success", "field": field_name, "value": field_value}


# --- Generic Tool Handler ---
def handle_tool_call(resp, chat, state: State) -> str:
    """
    A more abstract tool handler that dispatches to the correct tool logic.
    """
    if not resp.candidates:
        return resp.text.strip()

    parts = resp.candidates[0].content.parts
    if not parts or not hasattr(parts[0], "function_call"):
        return resp.text.strip()

    fc = parts[0].function_call
    args = getattr(fc, "args", {})
    response_data = {}

    # --- Dispatcher ---
    # This is now easy to expand!
    if fc.name == "set_field":
        response_data = set_field(state, args.get("field"), args.get("value"))
    
    # elif fc.name == "another_tool":
    #     response_data = another_tool(state, args.get("param1"))

    else:
        print(f"[IGNORED TOOL] Unknown tool {fc.name}")
        return resp.text.strip()
    # --- End Dispatcher ---

    # Send function_response back to the model
    resp2 = chat.send_message([{
        "function_response": {
            "name": fc.name,
            "response": response_data  # Send back the clean JSON response
        }
    }])

    return resp2.text.strip()