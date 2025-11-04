CHECK_LIST = {
    "device_type": {
        "question": "What is the primary characteristic of the device?",
        "options": [
            "NON_INVASIVE",  # "Does not penetrate the body surface."
            "INVASIVE_BODY_ORIFICE", # "Penetrates a body opening (e.g., mouth, nose) but not through surgery."
            "SURGICALLY_INVASIVE", # "Penetrates the body surface through surgery."
            "IMPLANTABLE", # "Intended to be left in the body after a procedure."
            "ACTIVE", # "Relies on an energy source (like electricity) not from the body or gravity."
            "SOFTWARE" # "Is standalone software used for medical purposes."
        ],
        "answer": None,
        "description": "Determines the primary set of rules to apply (Non-Invasive, Invasive, Active, Software)."
    },
    "duration": {
        "question": "What is the intended *continuous* duration of use for the device?",
        "options": [
            "TRANSIENT", # "Less than 60 minutes."
            "SHORT_TERM", # "Between 60 minutes and 30 days."
            "LONG_TERM" # "More than 30 days."
        ],
        "answer": None,
        "description": "Required for most invasive devices (Rules 5, 6, 7, 8)."
    },
    "contact_location": {
        "question": "Where does the device make contact with the body? (Select all that apply)",
        "options": [
            "INTACT_SKIN",
            "INJURED_SKIN",
            "MUCOUS_MEMBRANE",
            "ORAL_PHARYNX",
            "EAR_CANAL",
            "NASAL_CAVITY",
            "TEETH",
            "HEART",
            "CENTRAL_CIRCULATORY",
            "CENTRAL_NERVOUS",
            "NONE" # e.g., for software
        ],
        "answer": None,
        "description": "Critical for invasive rules (5-8) and non-invasive Rule 4."
    },
    "special_rules_check": {
        "question": "Does the device have any of the following specific purposes or characteristics? (Select all that apply)",
        "options": [
            "incorporates_medicinal_substance", # Rule 14
            "contraception_or_std_prevention", # Rule 15
            "disinfects_or_cleans_contact_lenses", # Rule 16
            "disinfects_or_sterilizes_other_medical_devices", # Rule 16
            "manufactured_with_biological_tissues_or_cells", # Rule 18
            "incorporates_nanomaterial", # Rule 19
            "administers_medicine_via_inhalation", # Rule 20
            "is_substance_absorbed_by_body", # Rule 21
            "records_diagnostic_xray_images", # Rule 17
            "NONE"
        ],
        "answer": None,
        "description": "Checks for Special Rules (14-22) which override all other rules."
    },
    "connections": {
        "question": "Is the device intended to be connected to another medical device?",
        "options": [
            "NOT_CONNECTED",
            "CONNECTED_TO_CLASS_I",
            "CONNECTED_TO_CLASS_II_OR_III" # (IIa, IIb, III)
        ],
        "answer": None,
        "description": "Relevant for Non-Invasive Rule 2 and Invasive Rule 5."
    },
    "conditional_active": {
        "question": "IF the device is 'Active', what is its primary function?",
        "options": [
            "therapeutic_energy_exchange", # Rule 9
            "controls_class_IIb_therapeutic_device", # Rule 9
            "diagnostic_or_monitoring", # Rule 10
            "illuminates_body", # Rule 10
            "monitors_vital_parameters_immediate_danger", # Rule 10
            "administers_or_removes_substances", # Rule 12
            "closed_loop_or_aed_system", # Rule 22
            "OTHER_ACTIVE" # Rule 13
        ],
        "answer": None,
        "description": "Follow-up questions for 'ACTIVE' devices (Rules 9-13, 22)."
    },
    "conditional_invasive": {
        "question": "IF the device is 'Invasive' or 'Implantable', does it have any of these characteristics? (Select all that apply)",
        "options": [
            "reusable_surgical_instrument", # Rule 6
            "supplies_ionizing_radiation", # Rule 6, 7
            "has_biological_effect_or_is_absorbed", # Rule 6, 7, 8
            "undergoes_chemical_change_in_body", # Rule 7, 8
            "administers_medicinal_products", # Rule 6, 7, 8
            "is_breast_implant_or_surgical_mesh", # Rule 8
            "is_joint_or_spinal_replacement", # Rule 8
            "NONE"
        ],
        "answer": None,
        "description": "Follow-up questions for 'INVASIVE' or 'IMPLANTABLE' devices (Rules 5-8)."
    },
    "conditional_non_invasive": {
        "question": "IF the device is 'Non-Invasive', what is its primary function?",
        "options": [
            "channels_or_stores_liquids_for_infusion", # Rule 2
            "is_blood_bag", # Rule 2
            "modifies_composition_of_blood_tissues_etc", # Rule 3
            "contacts_injured_skin_or_mucous_membrane", # Rule 4
            "OTHER_NON_INVASIVE" # Rule 1
        ],
        "answer": None,
        "description": "Follow-up questions for 'NON_INVASIVE' devices (Rules 1-4)."
    },
    "conditional_software": {
        "question": "IF the device is 'Software', what is the impact of the information it provides?",
        "options": [
            "impact_death_or_irreversible_deterioration", # Rule 11 (Class III)
            "impact_serious_deterioration_or_surgical_intervention", # Rule 11 (Class IIb)
            "monitors_vital_parameters_immediate_danger", # Rule 11 (Class IIb)
            "provides_info_for_other_decisions", # Rule 11 (Class IIa)
            "monitors_other_physiological_processes", # Rule 11 (Class IIa)
            "OTHER_SOFTWARE" # Rule 11 (Class I)
        ],
        "answer": None,
        "description": "Follow-up questions for 'SOFTWARE' devices (Rule 11)."
    }
}

TOOLS = [{
    "function_declarations": [{
        "name": "record_answers",
        "description": "Records or updates the user's answers about the medical device characteristics for MDR classification.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "device_type": {
                    "type": "STRING",
                    "description": "The primary characteristic of the device (e.g., Active, Invasive).",
                    "enum": [
                        "NON_INVASIVE",
                        "INVASIVE_BODY_ORIFICE",
                        "SURGICALLY_INVASIVE",
                        "IMPLANTABLE",
                        "ACTIVE",
                        "SOFTWARE"
                    ]
                },
                "duration": {
                    "type": "STRING",
                    "description": "The intended continuous duration of use.",
                    "enum": ["TRANSIENT", "SHORT_TERM", "LONG_TERM"]
                },
                "contact_location": {
                    "type": "ARRAY",
                    "description": "Body parts the device contacts (e.g., Heart, Intact Skin).",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "INTACT_SKIN",
                            "INJURED_SKIN",
                            "MUCOUS_MEMBRANE",
                            "ORAL_PHARYNX",
                            "EAR_CANAL",
                            "NASAL_CAVITY",
                            "TEETH",
                            "HEART",
                            "CENTRAL_CIRCULATORY",
                            "CENTRAL_NERVOUS",
                            "NONE"
                        ]
                    }
                },
                "special_rules_check": {
                    "type": "ARRAY",
                    "description": "Specific purposes or characteristics matching special rules (e.g., nanomaterial, contraception).",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "incorporates_medicinal_substance",
                            "contraception_or_std_prevention",
                            "disinfects_or_cleans_contact_lenses",
                            "disinfects_or_sterilizes_other_medical_devices",
                            "manufactured_with_biological_tissues_or_cells",
                            "incorporates_nanomaterial",
                            "administers_medicine_via_inhalation",
                            "is_substance_absorbed_by_body",
                            "records_diagnostic_xray_images",
                            "NONE"
                        ]
                    }
                },
                "connections": {
                    "type": "STRING",
                    "description": "Connection to another medical device.",
                    "enum": [
                        "NOT_CONNECTED",
                        "CONNECTED_TO_CLASS_I",
                        "CONNECTED_TO_CLASS_II_OR_III"
                    ]
                },
                "conditional_active": {
                    "type": "ARRAY",
                    "description": "Primary functions if the device is 'Active'.",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "therapeutic_energy_exchange",
                            "controls_class_IIb_therapeutic_device",
                            "diagnostic_or_monitoring",
                            "illuminates_body",
                            "monitors_vital_parameters_immediate_danger",
                            "administers_or_removes_substances",
                            "closed_loop_or_aed_system",
                            "OTHER_ACTIVE"
                        ]
                    }
                },
                "conditional_invasive": {
                    "type": "ARRAY",
                    "description": "Specific characteristics if the device is 'Invasive' or 'Implantable'.",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "reusable_surgical_instrument",
                            "supplies_ionizing_radiation",
                            "has_biological_effect_or_is_absorbed",
                            "undergoes_chemical_change_in_body",
                            "administers_medicinal_products",
                            "is_breast_implant_or_surgical_mesh",
                            "is_joint_or_spinal_replacement",
                            "NONE"
                        ]
                    }
                },
                "conditional_non_invasive": {
                    "type": "ARRAY",
                    "description": "Primary functions if the device is 'Non-Invasive'.",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "channels_or_stores_liquids_for_infusion",
                            "is_blood_bag",
                            "modifies_composition_of_blood_tissues_etc",
                            "contacts_injured_skin_or_mucous_membrane",
                            "OTHER_NON_INVASIVE"
                        ]
                    }
                },
                "conditional_software": {
                    "type": "ARRAY",
                    "description": "Impact of information if the device is 'Software'.",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "impact_death_or_irreversible_deterioration",
                            "impact_serious_deterioration_or_surgical_intervention",
                            "monitors_vital_parameters_immediate_danger",
                            "provides_info_for_other_decisions",
                            "monitors_other_physiological_processes",
                            "OTHER_SOFTWARE"
                        ]
                    }
                }
            },
            # All parameters are optional, allowing for partial updates
            # as the conversation progresses.
            "required": []
        }
    }]
}]


def is_checklist_complete(cl) -> bool:
    return all(item["answer"] is not None for item in cl.values())


def update_checklist(cl, answers: dict):
    updated = []
    for k, v in answers.items():
        if k in cl and v is not None and cl[k]["answer"] is None:
            
            # Check if v is iterable (like a list) but not a string
            if hasattr(v, '__iter__') and not isinstance(v, str):
                # Convert the 'RepeatedComposite' or other iterable to a standard list
                cl[k]["answer"] = list(v)
            else:
                # Otherwise, just assign the simple value (like a string)
                cl[k]["answer"] = v
            
            updated.append(k)
    return updated


def record_answers(checklist: dict, payload: dict) -> dict:
    """
    Lokala verktyget: uppdatera checklistan och returnera ett enkelt payload.
    """
    updated = update_checklist(checklist, payload)
    return {
        "updated_fields": updated,
        "current_state": {k: v["answer"] for k, v in checklist.items()},
        "is_complete": is_checklist_complete(checklist),
    }