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
    BARRIER = "BARRIER"
    DERMIS_BREACH = "DERMIS_BREACH"
    MICRO_ENV = "MICRO_ENV"
    OTHER = "OTHER"


class OrificeLocation(str, Enum):
    ORAL_PHARYNX = "ORAL_PHARYNX"       # oral cavity as far as pharynx
    EAR_CANAL = "EAR_CANAL"             # ear canal up to ear drum
    NASAL = "NASAL"                      # nasal cavity
    OTHER = "OTHER"                      # other orifices (e.g., rectal, vaginal)


class NanomaterialExposure(str, Enum):
    HIGH = "HIGH"           # → Class III
    MEDIUM = "MEDIUM"       # → Class III
    LOW = "LOW"             # → Class IIb
    NEGLIGIBLE = "NEGLIGIBLE"  # → Class IIa


class SoftwareRiskLevel(str, Enum):
    NONE = "NONE"                           # No diagnostic/therapeutic decisions → Class I
    MODERATE = "MODERATE"                   # General diagnostic/therapeutic info → Class IIa
    SERIOUS = "SERIOUS"                     # Serious deterioration or surgical intervention → Class IIb
    DEATH_OR_IRREVERSIBLE = "DEATH_OR_IRREVERSIBLE"  # Death or irreversible deterioration → Class III


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

    # --- Invasive (Rules 5, 6, 7, 8) ---
    is_surgically_invasive: Optional[bool] = None
    is_implantable: Optional[bool] = None
    contacts_cns_or_heart: Optional[bool] = None
    administers_medicines: Optional[bool] = None
    is_reusable_instrument: Optional[bool] = None
    # New fields:
    has_biological_effect: Optional[bool] = None
    undergoes_chemical_change: Optional[bool] = None
    placed_in_teeth: Optional[bool] = None
    orifice_location: Optional[OrificeLocation] = None

    # --- Active (Rules 9, 10, 11, 12, 13) ---
    emits_radiation: Optional[bool] = None
    administers_energy: Optional[bool] = None
    monitors_vital_functions: Optional[bool] = None
    controls_other_device: Optional[bool] = None
    # New fields:
    energy_is_hazardous: Optional[bool] = None
    immediate_danger_monitoring: Optional[bool] = None
    controls_active_implantable: Optional[bool] = None
    administers_removes_substances: Optional[bool] = None

    # --- Software (Rule 11) ---
    influences_treatment_decisions: Optional[bool] = None
    failure_risk_death: Optional[bool] = None  # Keep for backwards compat
    # New field:
    software_risk_level: Optional[SoftwareRiskLevel] = None

    # --- Special Rules (Rules 14-22) ---
    incorporates_medicinal_product: Optional[bool] = None      # Rule 14 → III
    is_contraceptive_or_std_prevention: Optional[bool] = None  # Rule 15 → IIb/III
    is_disinfecting_device: Optional[bool] = None              # Rule 16 → IIa/IIb
    disinfects_invasive_devices: Optional[bool] = None         # Rule 16 detail
    records_xray_images: Optional[bool] = None                 # Rule 17 → IIa
    contains_human_or_animal_tissue: Optional[bool] = None     # Rule 18 → III
    tissue_contacts_intact_skin_only: Optional[bool] = None    # Rule 18 exception
    contains_nanomaterial: Optional[bool] = None               # Rule 19
    nanomaterial_exposure: Optional[NanomaterialExposure] = None  # Rule 19 detail
    is_inhalation_drug_delivery: Optional[bool] = None         # Rule 20 → IIa/IIb
    inhalation_essential_impact: Optional[bool] = None         # Rule 20 detail
    is_substance_absorbed_in_body: Optional[bool] = None       # Rule 21
    substance_systemic_absorption: Optional[bool] = None       # Rule 21 detail
    is_closed_loop_therapeutic: Optional[bool] = None          # Rule 22 → III

    class Config:
        arbitrary_types_allowed = True