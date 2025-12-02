from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Duration(str, Enum):
    TRANSIENT = "TRANSIENT"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"


class TriageNode(BaseModel):
    """Initial triage."""
    
    device_name: Optional[str] = Field(None, description="Name of the device")
    is_invasive: Optional[bool] = Field(None, description="Does it penetrate the body?")
    is_active: Optional[bool] = Field(None, description="Does it rely on energy (electricity/battery)?")
    is_software: Optional[bool] = Field(None, description="Is the device STANDALONE software (e.g., mobile app, AI model)? Set to FALSE if it is a physical device that happens to contain embedded software/firmware.")  
    duration: Optional[Duration] = Field(None, description="Duration: TRANSIENT (<60m), SHORT_TERM (<30d), LONG_TERM (>30d)")


class InvasiveNode(BaseModel):
    """Logic regarding invasive devices (Rules 5, 6, 7, 8)."""
    
    # Här måste vi använda dina exakta fält från state.py
    is_surgically_invasive: Optional[bool] = Field(None, description="Does it penetrate the body through the skin (surgery/injection) vs just a natural orifice?")
    is_implantable: Optional[bool] = Field(None, description="Is it intended to be totally introduced and remain in the body after the procedure?")
    
    # Kombinerat fält i ditt state - vi tydliggör i beskrivningen
    contacts_cns_or_heart: Optional[bool] = Field(None, description="Does it specifically contact the Central Nervous System (brain/spine) OR the Heart/Central Circulatory System?")
    
    administers_medicines: Optional[bool] = Field(None, description="Is it intended to administer a medicinal product/drug?")
    is_reusable_instrument: Optional[bool] = Field(None, description="Is it a reusable surgical instrument (e.g., scalpel, scissors)?")


class ActiveNode(BaseModel):
    """Logic regarding active devices (Rules 9, 10, 11, 12)."""
    
    emits_radiation: Optional[bool] = Field(None, description="Does it emit ionizing radiation (e.g., X-ray, CT)?")
    administers_energy: Optional[bool] = Field(None, description="Does it administer energy TO the patient (e.g., laser, muscle stimulator)?")
    
    # Kritisk för Regel 10
    monitors_vital_functions: Optional[bool] = Field(None, description="Does it monitor vital physiological parameters (e.g., heart rate, respiration, glucose)?")
    
    controls_other_device: Optional[bool] = Field(None, description="Does it drive or control another active medical device?")


class SoftwareNode(BaseModel):
    """Logic regarding software (Rule 11)."""
    
    influences_treatment_decisions: Optional[bool] = Field(None, description="Does the software provide information used to take diagnostic or therapeutic decisions?")
    
    # Det här fältet i ditt state är lite binärt för Regel 11 (som har tre nivåer), 
    # men vi beskriver det så att det fångar de allvarligaste fallen (Klass III/IIb).
    failure_risk_death: Optional[bool] = Field(None, description="Could a failure or wrong result lead to death OR a serious deterioration of health?")