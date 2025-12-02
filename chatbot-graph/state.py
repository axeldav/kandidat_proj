# state.py
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
import operator
from enum import Enum


class Duration(str, Enum):
    TRANSIENT = "TRANSIENT"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"


class WoundUseType(str, Enum):
    BARRIER = "BARRIER"           # mechanical barrier, compression, absorption → Class I
    DERMIS_BREACH = "DERMIS_BREACH"  # deep wounds, secondary healing → Class IIb
    MICRO_ENV = "MICRO_ENV"       # manages wound micro-environment → Class IIa
    OTHER = "OTHER"               # all other cases → Class IIa


class State(BaseModel):
    # --- System ---
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    pending_nodes: List[str] = Field(default_factory=list)
    triage_complete: bool = False

    # --- Triage ---
    device_name: Optional[str] = None
    is_invasive: Optional[bool] = None
    is_active: Optional[bool] = None
    is_software: Optional[bool] = None
    duration: Optional[Duration] = None

    # --- Non-Invasive (Rules 2, 3, 4) ---
    channels_fluids_for_infusion: Optional[bool] = None
    is_blood_bag: Optional[bool] = None
    modifies_fluids_for_body: Optional[bool] = None
    is_simple_processing: Optional[bool] = None
    contacts_injured_skin: Optional[bool] = None
    wound_use_type: Optional[WoundUseType] = None

    # --- Invasive ---
    is_surgically_invasive: Optional[bool] = None
    is_implantable: Optional[bool] = None
    contacts_cns_or_heart: Optional[bool] = None
    administers_medicines: Optional[bool] = None
    is_reusable_instrument: Optional[bool] = None

    # --- Active ---
    emits_radiation: Optional[bool] = None
    administers_energy: Optional[bool] = None
    monitors_vital_functions: Optional[bool] = None
    controls_other_device: Optional[bool] = None

    # --- Software ---
    influences_treatment_decisions: Optional[bool] = None
    failure_risk_death: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True