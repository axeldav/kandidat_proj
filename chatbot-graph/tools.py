from pydantic import BaseModel, Field
from typing import Optional
from state import Duration, WoundUseType


class TriageNode(BaseModel):
    """Initial triage."""
    
    device_name: Optional[str] = Field(None, description="Name of the device")
    is_invasive: Optional[bool] = Field(None, description="Does it penetrate the body?")
    is_active: Optional[bool] = Field(None, description="Does it rely on energy (electricity/battery)?")
    is_software: Optional[bool] = Field(None, description="Is the device STANDALONE software (e.g., mobile app, AI model)? Set to FALSE if it is a physical device that happens to contain embedded software/firmware.")  
    duration: Optional[Duration] = Field(None, description="Duration: TRANSIENT (<60m), SHORT_TERM (<30d), LONG_TERM (>30d)")


class NonInvasiveNode(BaseModel):
    """Logic for non-invasive devices (Rules 2, 3, 4). Rule 1 default = Class I."""
    
    # Rule 2: Channelling/storing for body introduction
    channels_fluids_for_infusion: Optional[bool] = Field(None, 
        description="Does it channel or store blood, body fluids, cells, or tissues for eventual infusion/administration into the body?")
    is_blood_bag: Optional[bool] = Field(None, 
        description="Is it specifically a blood bag?")
    
    # Rule 3: Modifying composition
    modifies_fluids_for_body: Optional[bool] = Field(None, 
        description="Does it modify biological/chemical composition of blood, body fluids, or tissues intended for implantation into the body?")
    is_simple_processing: Optional[bool] = Field(None, 
        description="Is the modification limited to filtration, centrifugation, or gas/heat exchange?")
    
    # Rule 4: Injured skin/mucous membrane contact
    contacts_injured_skin: Optional[bool] = Field(None, 
        description="Does it contact injured skin or mucous membrane?")
    wound_use_type: Optional[WoundUseType] = Field(None, 
        description="BARRIER (compression/absorption), DERMIS_BREACH (deep wounds, secondary healing), MICRO_ENV (manages wound environment), or OTHER")


class InvasiveNode(BaseModel):
    """Logic regarding invasive devices (Rules 5, 6, 7, 8)."""
    
    is_surgically_invasive: Optional[bool] = Field(None, description="Does it penetrate the body through the skin (surgery/injection) vs just a natural orifice?")
    is_implantable: Optional[bool] = Field(None, description="Is it intended to be totally introduced and remain in the body after the procedure?")
    contacts_cns_or_heart: Optional[bool] = Field(None, description="Does it specifically contact the Central Nervous System (brain/spine) OR the Heart/Central Circulatory System?")
    administers_medicines: Optional[bool] = Field(None, description="Is it intended to administer a medicinal product/drug?")
    is_reusable_instrument: Optional[bool] = Field(None, description="Is it a reusable surgical instrument (e.g., scalpel, scissors)?")


class ActiveNode(BaseModel):
    """Logic regarding active devices (Rules 9, 10, 11, 12)."""
    
    emits_radiation: Optional[bool] = Field(None, description="Does it emit ionizing radiation (e.g., X-ray, CT)?")
    administers_energy: Optional[bool] = Field(None, description="Does it administer energy TO the patient (e.g., laser, muscle stimulator)?")
    monitors_vital_functions: Optional[bool] = Field(None, description="Does it monitor vital physiological parameters (e.g., heart rate, respiration, glucose)?")
    controls_other_device: Optional[bool] = Field(None, description="Does it drive or control another active medical device?")


class SoftwareNode(BaseModel):
    """Logic regarding software (Rule 11)."""
    
    influences_treatment_decisions: Optional[bool] = Field(None, description="Does the software provide information used to take diagnostic or therapeutic decisions?")
    failure_risk_death: Optional[bool] = Field(None, description="Could a failure or wrong result lead to death OR a serious deterioration of health?")