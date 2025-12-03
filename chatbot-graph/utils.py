# utils.py
from typing import List


def calculate_pending_nodes(state) -> List[str]:
    """Bestäm vilka noder som ska köras."""
    nodes = []
    
    if state.is_invasive:
        nodes.append("invasive")
    elif state.is_invasive is False:
        nodes.append("non_invasive")
    
    if state.is_active:
        nodes.append("active")
    
    if state.is_software:
        nodes.append("software")

    nodes.append("special_rules")
    
    return nodes