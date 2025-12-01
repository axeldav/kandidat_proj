
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

# Enum-klasser för alla valbara värden
class DeviceType(str, Enum):
    NON_INVASIVE = "NON_INVASIVE"
    INVASIVE_BODY_ORIFICE = "INVASIVE_BODY_ORIFICE"
    SURGICALLY_INVASIVE = "SURGICALLY_INVASIVE"
    IMPLANTABLE = "IMPLANTABLE"
    ACTIVE = "ACTIVE"
    SOFTWARE = "SOFTWARE"

class Duration(str, Enum):
    TRANSIENT = "TRANSIENT"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"

class ContactLocation(str, Enum):
    INTACT_SKIN = "INTACT_SKIN"
    INJURED_SKIN = "INJURED_SKIN"
    MUCOUS_MEMBRANE = "MUCOUS_MEMBRANE"
    ORAL_PHARYNX = "ORAL_PHARYNX"
    EAR_CANAL = "EAR_CANAL"
    NASAL_CAVITY = "NASAL_CAVITY"
    TEETH = "TEETH"
    HEART = "HEART"
    CENTRAL_CIRCULATORY = "CENTRAL_CIRCULATORY"
    CENTRAL_NERVOUS = "CENTRAL_NERVOUS"
    NONE = "NONE"

class OrthopaedicImplantType(str, Enum):
    JOINT_REPLACEMENT = "total_or_partial_joint_replacements"
    SPINAL_DISC = "spinal_disc"
    ANCILLARY_COMPONENTS = "ancillary_components"  # screws, wedges, plates
    NONE = "none"

class SpecialRule(str, Enum):
    INCORPORATES_MEDICINAL = "incorporates_medicinal_substance"
    CONTRACEPTION_STD = "contraception_or_std_prevention"
    DISINFECTS_CONTACT_LENSES = "disinfects_or_cleans_contact_lenses"
    DISINFECTS_MEDICAL_DEVICES = "disinfects_or_sterilizes_other_medical_devices"
    BIOLOGICAL_TISSUES = "manufactured_with_biological_tissues_or_cells"
    INCORPORATES_NANOMATERIAL = "incorporates_nanomaterial"
    ADMINISTERS_VIA_INHALATION = "administers_medicine_via_inhalation"
    IS_ABSORBED = "is_substance_absorbed_by_body"
    RECORDS_XRAY = "records_diagnostic_xray_images"
    NONE = "NONE"

class Connection(str, Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTED_TO_CLASS_I = "CONNECTED_TO_CLASS_I"
    CONNECTED_TO_CLASS_II_OR_III = "CONNECTED_TO_CLASS_II_OR_III"

class ConditionalActive(str, Enum):
    THERAPEUTIC_ENERGY = "therapeutic_energy_exchange"
    CONTROLS_CLASS_IIB = "controls_class_IIb_therapeutic_device"
    DIAGNOSTIC_MONITORING = "diagnostic_or_monitoring"
    ILLUMINATES_BODY = "illuminates_body"
    MONITORS_VITAL_DANGER = "monitors_vital_parameters_immediate_danger"
    ADMINISTERS_SUBSTANCES = "administers_or_removes_substances"
    CLOSED_LOOP_AED = "closed_loop_or_aed_system"
    OTHER_ACTIVE = "OTHER_ACTIVE"

class ConditionalInvasive(str, Enum):
    REUSABLE_SURGICAL = "reusable_surgical_instrument"
    IONIZING_RADIATION = "supplies_ionizing_radiation"
    BIOLOGICAL_EFFECT = "has_biological_effect_or_is_absorbed"
    CHEMICAL_CHANGE = "undergoes_chemical_change_in_body"
    ADMINISTERS_MEDICINAL = "administers_medicinal_products"
    BREAST_IMPLANT_MESH = "is_breast_implant_or_surgical_mesh"
    JOINT_SPINAL = "is_joint_or_spinal_replacement"
    NONE = "NONE"

class ConditionalNonInvasive(str, Enum):
    CHANNELS_STORES = "channels_or_stores_liquids_for_infusion"
    BLOOD_BAG = "is_blood_bag"
    MODIFIES_COMPOSITION = "modifies_composition_of_blood_tissues_etc"
    CONTACTS_INJURED = "contacts_injured_skin_or_mucous_membrane"
    OTHER_NON_INVASIVE = "OTHER_NON_INVASIVE"

class ConditionalSoftware(str, Enum):
    IMPACT_DEATH = "impact_death_or_irreversible_deterioration"
    IMPACT_SERIOUS = "impact_serious_deterioration_or_surgical_intervention"
    MONITORS_VITAL_DANGER = "monitors_vital_parameters_immediate_danger"
    PROVIDES_INFO = "provides_info_for_other_decisions"
    MONITORS_PHYSIOLOGICAL = "monitors_other_physiological_processes"
    OTHER_SOFTWARE = "OTHER_SOFTWARE"


class TriageNode(BaseModel):
    device_characteristics: Optional[List[DeviceType]] = Field(
        None, 
        description="List of all applicable categories. E.g., ['ACTIVE', 'IMPLANTABLE']"
    )
    duration: Optional[Duration] = Field(
        None, 
        description="The intended continuous duration of use."
    )
    contact_location: Optional[List[ContactLocation]] = Field(
        None, 
        description="Body parts the device contacts."
    )

class InvasiveNode(BaseModel):
    """Records answers about invasive device characteristics for MDR Rules 5-8."""
    
    # --- COMMON FIELDS (Shared by Rules 5, 6, 7, 8) ---
    central_circulatory_system: Optional[bool] = Field(
        None,
        description="Is the device intended for direct contact with the heart or central circulatory system? (Rules 6,7,8 -> Class III)"
    )
    
    central_nervous_system: Optional[bool] = Field(
        None,
        description="Is the device intended for direct contact with the central nervous system? (Rules 6,7,8 -> Class III)"
    )
    
    teeth_placement: Optional[bool] = Field(
        None,
        description="Is the device placed in the teeth? Exception: Often Class IIa instead of IIb/III for dental devices"
    )
    
    biological_effect_or_absorbed: Optional[bool] = Field(
        None,
        description="Is the device wholly/mainly absorbed or does it have biological effect? (Rule 6 -> IIb, Rules 7/8 -> III)"
    )
    
    administers_medicines: Optional[bool] = Field(
        None,
        description="Does the device administer medicinal products?"
    )
    
    chemical_change: Optional[bool] = Field(
        None,
        description="Is the device intended to undergo chemical change in the body? (Rules 7,8 -> IIb/III)"
    )
    
    # --- RULE 5 SPECIFIC (Body Orifice - Not Surgically Invasive) ---
    r5_connected_to_active_class_IIa_or_higher: Optional[bool] = Field(
        None,
        description="Is it intended for connection to a Class IIa or higher active device? -> Class IIa"
    )
    
    r5_oral_nasal_ear_specific: Optional[bool] = Field(
        None,
        description="Is it used in oral cavity, ear canal, or nasal cavity? Exception: -> Class I if transient"
    )
    
    r5_absorbed_by_mucous_membrane: Optional[bool] = Field(
        None,
        description="Is the device liable to be absorbed by the mucous membrane? (Long term exception logic)"
    )
    
    # --- RULE 6 SPECIFIC (Surgically Invasive & Transient) ---
    r6_reusable_surgical_instrument: Optional[bool] = Field(
        None,
        description="Is this a reusable surgical instrument? -> Class I"
    )
    
    r6_supplies_ionizing_radiation: Optional[bool] = Field(
        None,
        description="Does it supply energy as ionizing radiation? -> Class IIb"
    )
    
    r6_medicinal_delivery_hazardous: Optional[bool] = Field(
        None,
        description="If administering medicines, is the method potentially hazardous? (Rule 6 specific)"
    )
    
    # --- RULE 7 (Surgically Invasive & Short Term) ---
    # Mostly covered by common fields + duration
    
    # --- RULE 8 SPECIFIC (Surgically Invasive & Long Term / Implantable) ---
    r8_orthopaedic_implant_type: Optional[OrthopaedicImplantType] = Field(
        None,
        description="Type of orthopaedic implant: joint/spinal -> Class III, ancillary -> Class IIb"
    )
    
    r8_breast_implant_or_mesh: Optional[bool] = Field(
        None,
        description="Is it a breast implant or surgical mesh? -> Class III"
    )
    
    r8_active_implantable: Optional[bool] = Field(
        None,
        description="Is this an active implantable device? -> Class III"
    )

class NonInvasiveNode(BaseModel):
    non_invasive_type: Optional[ConditionalNonInvasive] = Field(
        None,
        description="The primary characteristic of the device (e.g., Active, Invasive)."
    )

class SoftwareNode(BaseModel):
    software_type: Optional[ConditionalSoftware] = Field(
        None,
        description="The primary characteristic of the device (e.g., Active, Invasive)."
    )

class ActiveNode(BaseModel):
    active_type: Optional[ConditionalActive] = Field(
        None,
        description="The primary characteristic of the device (e.g., Active, Invasive)."
    )

class SpecialRulesNode(BaseModel):
    special_rules: Optional[List[SpecialRule]] = Field(
        None,
        description="Specific purposes or characteristics matching special rules (e.g., nanomaterial, contraception)."
    )
