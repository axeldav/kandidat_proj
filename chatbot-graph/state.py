from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field
import operator

# (Samma Enums som tidigare: DeviceClass, Duration, InvasiveType, etc.)
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DeviceClass(str, Enum):
    CLASS_I = "Class I"
    CLASS_IIa = "Class IIa"
    CLASS_IIb = "Class IIb"
    CLASS_III = "Class III"

class Duration(str, Enum):
    TRANSIENT = "Transient (<60 min)"
    SHORT_TERM = "Short term (<30 days)"
    LONG_TERM = "Long term (>30 days)"

class InvasiveType(str, Enum):
    NON_INVASIVE = "Non-invasive"
    BODY_ORIFICE = "Invasive via body orifice"
    SURGICALLY_INVASIVE = "Surgically invasive"
    IMPLANTABLE = "Implantable"

class NanoExposure(str, Enum):
    NEGLIGIBLE = "Negligible"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

from typing import Annotated, List, Optional, Literal
from pydantic import BaseModel, Field
import operator

from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
import operator

class State(BaseModel):
    ####### --- CHAT CONTEXT ---  #######
    # ... Lagrar historiken så LLM:en minns vad som sagts
    messages: Annotated[List[str], operator.add] = Field(default_factory=list)
    pending_nodes: List[str]
    triage_complete: bool

    ####### --- TRIAGE (Vägval) --- #######
    # ... Dessa två avgör hela flödet i grafen
    is_active_device: Optional[bool] = None       # True = Gå till Active Questions
    invasive_type: Optional[InvasiveType] = None  # Bestämmer Non-invasive vs Invasive Questions
    is_software: Optional[bool] = None

    ####### --- COMMON FIELDS --- #######
    # ... Duration krävs för nästan alla invasiva regler (5-8)
    duration: Optional[Duration] = None

    ####### --- NON-INVASIVE SPECIFICS (Rules 1-4) --- ####### 
    # ... Fylls i om invasive_type == NON_INVASIVE

    # Rule 1:
    # ... All non-invasive devices are classified as class I, unless one of the rules in rule 2 to rule 4 applies ....(Inga extra frågor behövs för Regel 1)

    # Rule 2: Channeling/Storing (Förenklad enligt din instruktion)
    r2_channeling_storing: Optional[bool] = None      # "Gatekeeper" för Regel 2
    r2_is_blood_bag: Optional[bool] = None            # Enda separata gruppen för IIb
    r2_includes_blood_body_liquids: Optional[bool] = None # Inkluderar organ/vävnad/blod -> IIa
    r2_connected_active: Optional[bool] = None        # Kopplas till aktiv enhet -> IIa

    # Rule 3: Modifying composition
    r3_modifies_composition: Optional[bool] = None # All non-invasive devices intended for modifying the biological or chemical composition of human tissues or cells, blood, other body liquids or other liquids intended for implantation or administration into the body are classified as class IIb
    r3_filtration_centrifugation: Optional[bool] = None # unless the treatment for which the device is used consists of filtration, centrifugation or exchanges of gas, heat, in which case they are classified as class IIa.
    r3_in_vitro_cells: Optional[bool] = None          # All non-invasive devices consisting of a substance or a mixture of substances intended to be used in vitro in direct contact with human cells, tissues or organs taken from the human body or used in vitro with human embryos before their implantation or administration into the body are classified as class III.

    # Rule 4: Injured Skin & Mucous Membrane
    
    # ... If this is false, skip all Rule 4 questions   
    r4_contact_injured_skin_mucosa_check: Optional[bool] = None  # "All non-invasive devices which come into contact with injured skin or mucous membrane..."
    
    r4_mechanical_barrier_compression_absorption: Optional[bool] = None # " class I if they are intended to be used as a mechanical barrier, for compression or for absorption of exudates;"
    r4_breached_dermis_secondary_healing: Optional[bool] = None # "class IIb if they are intended to be used principally for injuries to skin which have breached the dermis or mucous membrane and can only heal by secondary intent;"
    r4_manages_micro_environment: Optional[bool] = None # "class IIa if they are principally intended to manage the micro-environment of injured skin or mucous membrane;"

    ######## --- 5. INVASIVE SPECIFICS (Rules 5-8) --- ########
    # Fylls i om invasive_type != NON_INVASIVE

    # ... COMMON FIELDS (Shared by Rules 5, 6, 7, 8)
    central_circulatory_system: Optional[bool] = None  # Rule 6, 7, 8: "intended specifically for use in direct contact with the heart or central circulatory system -> Class III"
    central_nervous_system: Optional[bool] = None  # Rule 6, 7, 8: "...or the central nervous system -> Class III"
    teeth_placement: Optional[bool] = None  # Rule 5, 7, 8: Undantag. Ofta Class IIa (Dental) istället för IIb/III.
    biological_effect_or_absorbed: Optional[bool] = None  # Rule 6, 7, 8: Om enheten absorberas eller har biologisk effekt. (Rule 6 -> Class IIb. Rule 7/8 -> Class III).
    administers_medicines: Optional[bool] = None  # Rule 6, 7, 8: Administrering av läkemedel. (Rule 6 kräver att det är "hazardous" för att klassas upp, Rule 7/8 klassar upp direkt).
    chemical_change: Optional[bool] = None  # Rule 7, 8: "intended to undergo chemical change in the body" -> Class IIb/III.

    # Rule 5 (Body Orifice - Not Surgically Invasive)
    # ... Gäller om invasive_type == InvasiveType.BODY_ORIFICE

    r5_connected_to_active_class_IIa_or_higher: Optional[bool] = None  # "intended for connection to a class IIa... active device -> Class IIa"
    r5_oral_nasal_ear_specific: Optional[bool] = None  # Exception: "...used in the oral cavity... ear canal... nasal cavity -> Class I (if transient)"
    r5_absorbed_by_mucous_membrane: Optional[bool] = None  # Exception logic for Long Term: "...and are not liable to be absorbed by the mucous membrane"

    # Rule 6 (Surgically Invasive & Transient)
    # ... Gäller om invasive_type == SURGICALLY_INVASIVE och duration == TRANSIENT
    
    r6_reusable_surgical_instrument: Optional[bool] = None  # "...are reusable surgical instruments, in which case they are classified as class I".
    r6_supplies_ionizing_radiation: Optional[bool] = None  # "...intended to supply energy in the form of ionising radiation -> Class IIb"
    r6_medicinal_delivery_hazardous: Optional[bool] = None  # Specifik nyans för Rule 6: Är administreringen POTENTIELLT FARLIG?  (Om 'administers_medicines' är True, kollar vi detta för Rule 6).

    # Rule 7 (Surgically Invasive & Short Term)
    # ... (Mest täckt av Common fields, men här kan finnas unika variabler om nödvändigt) ... Just nu täcks allt av Common + Duration.

    # Rule 8 (Surgically Invasive & Long Term / Implantable) ---
    # ...Gäller om invasive_type == IMPLANTABLE eller Duration == LONG_TERM
    
    r8_orthopaedic_implant_type: Optional[str] = None  # "total or partial joint replacements -> Class III", "spinal disc -> Class III" , "ancillary components such as screws, wedges, plates -> Class IIb"
    r8_breast_implant_or_mesh: Optional[bool] = None  # "breast implants or surgical meshes -> Class III"
    r8_active_implantable: Optional[bool] = None  # "active implantable devices -> Class III"

    ######## --- 6. ACTIVE SPECIFICS (Rules 9-12) --- ########
    # Fylls i om is_active_device == True

    # COMMON FIELDS (Shared by Rules 9 & 10) ---
    
    emits_ionizing_radiation: Optional[bool] = None # Rule 9 & 10: "intended to emit ionizing radiation..." -> Class IIb (Both Therapeutic and Diagnostic) .... (T.ex. Röntgen, CT, strålkanoner. Notera: Gäller ej synligt ljus).

    # Rule 9: Active Therapeutic Devices (Energy & Control)
    # ... Gäller enheter som tillför energi eller styr andra enheter.

    r9_administers_exchange_energy: Optional[bool] = None # "intended to administer or exchange energy... classified as class IIa"... (T.ex. muskelstimulatorer, TENS, hörapparater, värmelampor).
    r9_hazardous_energy_delivery: Optional[bool] = None # Exception: "...administer energy... in a potentially hazardous way -> Class IIb"... (T.ex. kirurgisk laser, lungventilatorer, litotripsi).
    r9_controls_active_class_iib: Optional[bool] = None # "intended to control or monitor... active therapeutic class IIb devices -> Class IIb" ... (T.ex. en kontrollenhet för en strålningsmaskin).
    r9_controls_active_implantable: Optional[bool] = None # "intended for controlling, monitoring... active implantable devices -> Class III" ... (T.ex. en programmerare för en pacemaker eller ICD. Mycket viktig regel!).

    # Rule 10: Active Diagnostic Devices
    #... Gäller enheter för diagnos och övervakning.
    
    r10_monitors_vital_processes: Optional[bool] = None  # "allow direct diagnosis or monitoring of vital physiological processes -> Class IIa"
    r10_immediate_danger_alert: Optional[bool] = None  # Exception: "...variations... could result in immediate danger to the patient -> Class IIb" ... (T.ex. larm på en intensivvårdsmonitor).
    r10_illuminates_body: Optional[bool] = None  # "intended to illuminate the patient's body, in the visible spectrum -> Class I" ... (T.ex. undersökningslampor, pannlampor).

    # Rule 11: Software (Decision Making)
    #... Gäller fristående mjukvara eller mjukvara som driver en enhet.
    
    r11_software_decision_impact: Optional[str] = None # "Death or irreversible deterioration" -> III, "Serious deterioration/Surgical intervention" -> IIb, "Provide info" -> IIa.
    
    # Rule 12: Active Administration of Substances
    # ... Gäller pumpar och liknande som flyttar medicin eller substanser.
    
    r12_active_drug_delivery: Optional[bool] = None # "administer and/or remove medicinal products... -> Class IIa"
    r12_active_drug_delivery_hazardous: Optional[bool] = None # Exception: "...in a manner that is potentially hazardous -> Class IIb" ... (T.ex. insulinpumpar, infusionspumpar för smärtlindring).
    
    # Rule 13: All Other Active Devices is Class I
    # ... If is_active_device == True,  but all previous fields (r9-r12) are False/None, then Class I by default.


    ######## --- 7. SPECIAL RULES (Rules 14-22) --- ########
    # ... Dessa "checkas" alltid i slutet då de gäller oavsett typ.

    # --- Rule 14: Medicinal Products ---
    # ... Gäller produkter som innehåller läkemedel som en integrerad del.

    r14_contains_medicinal_product: Optional[bool] = None # "incorporating... a medicinal product... ancillary action -> Class III" ... (Gäller även derivat från humant blod/plasma. Om läkemedlet är huvudsyftet regleras det inte av MDR utan av läkemedelsdirektivet).

    # --- Rule 15: Contraception & STD Prevention ---
    
    r15_contraception_std_prevention: Optional[bool] = None # "contraception or prevention of transmission of STDs -> Class IIb" ... (Notera: Om enheten OCKSÅ är Implantable eller Long Term Invasive (via globala fält) -> Class III).

    # --- Rule 16: Disinfection & Sterilization ---
    # ... Gäller produkter som rengör eller desinficerar *andra* produkter.

    r16_contact_lens_care: Optional[bool] = None # "disinfecting, cleaning, rinsing... contact lenses -> Class IIb" ... (Specifikt för kontaktlinser. Gäller även vätskor för förvaring/hydrering).
    r16_disinfects_medical_devices: Optional[bool] = None # "disinfecting or sterilising medical devices -> Class IIa"... (Gäller t.ex. autoklaver, sterilisatorer).

    r16_disinfects_invasive_endpoint: Optional[bool] = None # Exception: "...disinfecting invasive devices, as the end point of processing -> Class IIb" ... (Gäller desinfektionslösningar eller diskdesinfektorer avsedda specifikt för invasiva instrument). ... (OBS: Regel 16 gäller INTE om rengöring sker enbart med fysisk verkan, t.ex. en borste).
    
    # Rule 19 (Nano)
    r19_nanomaterial: Optional[bool] = None
    r19_nanomaterial_exposure: Optional[NanoExposure] = None # Endast om nanomaterial = True
    
    r20_inhalation_drug_delivery: Optional[bool] = None  # Rule 20
    r20_impact_on_drug_or_treat_life_threatening: Optional[bool] = None  # Rule 20 unless their mode of action has an essential impact on the efficacy and safety of the administered medicinal product or they are intended to treat life- threatening conditions, in which case they are classified as class IIb.
    r21_substance_absorbed_locally: Optional[bool] = None  # Rule 21 (Substances introduced to body)
    r22_closed_loop_system: Optional[bool] = None  # Rule 22 (Artificial Pancreas etc.)

    # --- 8. OUTPUT ---
    potential_classes: List[str] = Field(default_factory=list) # Lista med träffar, t.ex. ["Rule 1: Class I", "Rule 10: Class IIa"]
    final_classification: Optional[str] = None        # Resultatet, t.ex. "Class IIa"
    rationale: Optional[str] = None                   # Förklaringen

def get_field_options(field_name: str) -> List[str]: 
    """Helper function to get the Literal options for a field."""
    field_type = State.__annotations__.get(field_name)
    if field_type:
        # This will extract options from Optional[Literal[...]]
        args = get_args(field_type)
        if args:
            literal_args = get_args(args[0])
            if literal_args:
                return list(literal_args)
    return []