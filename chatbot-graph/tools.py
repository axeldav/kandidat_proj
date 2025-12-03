from pydantic import BaseModel, Field
from typing import Optional
from state import (
    Duration, WoundUseType, OrificeLocation, 
    NanomaterialExposure, SoftwareRiskLevel
)


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
    """Logic for invasive devices (Rules 5, 6, 7, 8)."""
    
    # Basic invasive characteristics
    is_surgically_invasive: Optional[bool] = Field(None, 
        description="Does it penetrate through the body surface (skin/mucosa) via surgery or injection, NOT just entering a natural orifice?")
    is_implantable: Optional[bool] = Field(None, 
        description="Is it intended to be totally introduced and REMAIN in the body after the procedure?")
    contacts_cns_or_heart: Optional[bool] = Field(None, 
        description="Does it contact the Central Nervous System (brain/spine) OR the Heart/Central Circulatory System?")
    administers_medicines: Optional[bool] = Field(None, 
        description="Is it intended to administer medicinal products/drugs?")
    is_reusable_instrument: Optional[bool] = Field(None, 
        description="Is it a reusable surgical instrument (e.g., scalpel, forceps)?")
    
    # New fields for Rules 5-8 specifics
    has_biological_effect: Optional[bool] = Field(None,
        description="Does it have a biological effect OR is it wholly/mainly absorbed by the body?")
    undergoes_chemical_change: Optional[bool] = Field(None,
        description="Is it intended to undergo chemical change in the body (excluding devices placed in teeth)?")
    placed_in_teeth: Optional[bool] = Field(None,
        description="Is it intended to be placed in the teeth?")
    orifice_location: Optional[OrificeLocation] = Field(None,
        description="If it enters a body orifice (non-surgical): ORAL_PHARYNX, EAR_CANAL, NASAL, or OTHER")


class ActiveNode(BaseModel):
    """Logic for active devices (Rules 9, 10, 12, 13)."""
    
    # Basic active characteristics
    emits_radiation: Optional[bool] = Field(None, 
        description="Does it emit ionizing radiation (e.g., X-ray, CT)?")
    administers_energy: Optional[bool] = Field(None, 
        description="Does it administer energy TO the patient (e.g., laser, electrosurgery, muscle stimulator)?")
    monitors_vital_functions: Optional[bool] = Field(None, 
        description="Does it monitor vital physiological parameters (e.g., heart rate, respiration, blood pressure)?")
    controls_other_device: Optional[bool] = Field(None, 
        description="Does it control or monitor the performance of another active medical device?")
    
    # New fields for Rules 9, 10, 12
    energy_is_hazardous: Optional[bool] = Field(None,
        description="If it administers energy: is the energy potentially hazardous considering nature, density, and body site?")
    immediate_danger_monitoring: Optional[bool] = Field(None,
        description="If it monitors vital functions: could variations in those parameters result in IMMEDIATE danger to the patient?")
    controls_active_implantable: Optional[bool] = Field(None,
        description="Does it control, monitor, or directly influence the performance of an ACTIVE IMPLANTABLE device?")
    administers_removes_substances: Optional[bool] = Field(None,
        description="Does it administer and/or remove medicinal products, body liquids, or other substances to/from the body (e.g., infusion pump, dialysis)?")


class SoftwareNode(BaseModel):
    """Logic for standalone software (Rule 11)."""
    
    influences_treatment_decisions: Optional[bool] = Field(None, 
        description="Does the software provide information used to take diagnostic or therapeutic decisions?")
    software_risk_level: Optional[SoftwareRiskLevel] = Field(None,
        description="Risk level: NONE (no clinical decisions), MODERATE (general diagnostic info), SERIOUS (could cause serious deterioration or surgical intervention), DEATH_OR_IRREVERSIBLE (could cause death or irreversible deterioration)")


class SpecialRulesNode(BaseModel):
    """Special rules that can override other classifications (Rules 14-22)."""
    
    # Rule 14: Incorporates medicinal product → Class III
    incorporates_medicinal_product: Optional[bool] = Field(None,
        description="Does it incorporate, as an integral part, a substance that would be considered a medicinal product if used separately?")
    
    # Rule 15: Contraception/STD prevention → IIb or III
    is_contraceptive_or_std_prevention: Optional[bool] = Field(None,
        description="Is it used for contraception or prevention of sexually transmitted diseases?")
    
    # Rule 16: Disinfecting devices → IIa or IIb
    is_disinfecting_device: Optional[bool] = Field(None,
        description="Is it intended for disinfecting, cleaning, rinsing, or sterilizing medical devices or contact lenses?")
    disinfects_invasive_devices: Optional[bool] = Field(None,
        description="If disinfecting: is it specifically for disinfecting INVASIVE devices as end point of processing?")
    
    # Rule 17: X-ray image recording → IIa
    records_xray_images: Optional[bool] = Field(None,
        description="Is it specifically intended for recording diagnostic images generated by X-ray radiation?")
    
    # Rule 18: Human/animal tissue → Class III (usually)
    contains_human_or_animal_tissue: Optional[bool] = Field(None,
        description="Is it manufactured using non-viable tissues or cells of human or animal origin, or their derivatives?")
    tissue_contacts_intact_skin_only: Optional[bool] = Field(None,
        description="If it contains animal tissue: is it intended to contact INTACT SKIN only?")
    
    # Rule 19: Nanomaterials → IIa/IIb/III
    contains_nanomaterial: Optional[bool] = Field(None,
        description="Does it incorporate or consist of nanomaterials?")
    nanomaterial_exposure: Optional[NanomaterialExposure] = Field(None,
        description="If nanomaterials: exposure potential - HIGH/MEDIUM (→III), LOW (→IIb), NEGLIGIBLE (→IIa)")
    
    # Rule 20: Inhalation drug delivery → IIa or IIb
    is_inhalation_drug_delivery: Optional[bool] = Field(None,
        description="Is it an invasive device (body orifice) intended to administer medicinal products by INHALATION?")
    inhalation_essential_impact: Optional[bool] = Field(None,
        description="If inhalation delivery: does its mode of action have ESSENTIAL impact on efficacy/safety, or treat life-threatening conditions?")
    
    # Rule 21: Substances absorbed in body → IIa/IIb/III
    is_substance_absorbed_in_body: Optional[bool] = Field(None,
        description="Is it composed of substances intended to be introduced into the body (orally/on skin) and absorbed or locally dispersed?")
    substance_systemic_absorption: Optional[bool] = Field(None,
        description="If absorbed: is it SYSTEMICALLY absorbed to achieve intended purpose, or absorbed in stomach/GI tract?")
    
    # Rule 22: Closed loop therapeutic → Class III
    is_closed_loop_therapeutic: Optional[bool] = Field(None,
        description="Is it an active therapeutic device with integrated diagnostic function that significantly determines patient management (e.g., closed loop insulin pump, automated defibrillator)?")