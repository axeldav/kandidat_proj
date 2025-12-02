# utils.py
from typing import List


def calculate_pending_nodes(state) -> List[str]:
    """Bestäm vilka noder som ska köras."""
    nodes = []
    
    if state.is_invasive:
        nodes.append("invasive")
    
    if state.is_active:
        nodes.append("active")
    
    if state.is_software:
        nodes.append("software")
    
    return nodes