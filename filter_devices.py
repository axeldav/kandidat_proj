#!/usr/bin/env python3
"""
EUDAMED Device Enrichment Script

Filters devices by risk class from a scraped JSON file and fetches
detailed information using the /devices/udiDiData/{uuid} endpoint.

Note: The /devices/basicUdiData/{id} endpoint returns 404 for all IDs
available in the search results. The udiDiData endpoint works with uuid.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime


def fetch_device_details(uuid: str, languageIso2Code: str = "en") -> dict:
    """
    Fetch detailed device information from EUDAMED API.
    
    Uses /devices/udiDiData/{uuid} which is confirmed to work.
    """
    url = f"https://ec.europa.eu/tools/eudamed/api/devices/udiDiData/{uuid}"
    params = {"languageIso2Code": languageIso2Code}
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def load_devices(input_file: str) -> list:
    """Load devices from JSON file, handling both array and {content: [...]} formats."""
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both formats: direct array or {content: [...]}
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "content" in data:
        return data["content"]
    else:
        raise ValueError("Unexpected JSON format. Expected array or {content: [...]}}")


def filter_devices(
    input_file: str = "eudamed_devices.json",
    risk_class: str = None,
    limit: int = None,
    fetch_details: bool = True,
    sleep_seconds: float = 1.0
) -> list:
    """
    Filter devices from scraped EUDAMED data and fetch full details.
    
    Args:
        input_file: Path to the scraped JSON file
        risk_class: Filter by risk class ('i', 'iia', 'iib', 'iii', 'a', 'b', 'c', 'd')
        limit: Maximum number of devices to process
        fetch_details: If True, fetch full details from /devices/udiDiData/{uuid}
        sleep_seconds: Seconds to wait between API requests
    
    Returns:
        List of devices with enriched details
    """
    print(f"Loading devices from {input_file}...")
    all_devices = load_devices(input_file)
    print(f"Loaded {len(all_devices)} total device entries")
    
    # Build the risk class code if specified
    risk_class_code = None
    if risk_class:
        risk_class_code = f"refdata.risk-class.class-{risk_class.lower()}"
        print(f"Filtering by risk class: {risk_class_code}")
    
    # Filter and deduplicate by basicUdi AND tradeName
    seen_basic_udis = set()
    seen_trade_names = set()
    filtered_devices = []
    
    for device in all_devices:
        # Filter by risk class if specified
        if risk_class_code:
            device_risk = device.get("riskClass", {})
            if isinstance(device_risk, dict):
                device_risk_code = device_risk.get("code", "")
            else:
                device_risk_code = ""
            
            if device_risk_code != risk_class_code:
                continue
        
        # Deduplicate by basicUdi
        basic_udi = device.get("basicUdi")
        if basic_udi in seen_basic_udis:
            continue
        
        # Deduplicate by tradeName (extract text value)
        trade_name_raw = device.get("tradeName")
        if isinstance(trade_name_raw, str):
            trade_name = trade_name_raw.strip().lower()
        elif isinstance(trade_name_raw, dict) and "texts" in trade_name_raw:
            texts = trade_name_raw.get("texts", [])
            trade_name = texts[0].get("text", "").strip().lower() if texts else ""
        else:
            trade_name = str(trade_name_raw).strip().lower() if trade_name_raw else ""
        
        if trade_name and trade_name in seen_trade_names:
            continue
        
        seen_basic_udis.add(basic_udi)
        if trade_name:
            seen_trade_names.add(trade_name)
        filtered_devices.append(device)
        
        # Check limit
        if limit and len(filtered_devices) >= limit:
            break
    
    print(f"Found {len(filtered_devices)} unique devices (by basicUdi and tradeName)")
    
    # Fetch full details for each device
    if fetch_details and filtered_devices:
        print(f"\nFetching detailed info for {len(filtered_devices)} devices...")
        print(f"Using endpoint: /devices/udiDiData/{{uuid}}")
        print(f"Sleep between requests: {sleep_seconds}s")
        print("-" * 50)
        
        detailed_devices = []
        success_count = 0
        error_count = 0
        
        for i, device in enumerate(filtered_devices):
            uuid = device.get("uuid")
            basic_udi = device.get("basicUdi", "unknown")
            
            if not uuid:
                print(f"[{i+1}/{len(filtered_devices)}] No UUID for {basic_udi}, keeping original")
                detailed_devices.append(device)
                continue
            
            try:
                print(f"[{i+1}/{len(filtered_devices)}] {basic_udi}...", end=" ", flush=True)
                details = fetch_device_details(uuid)
                detailed_devices.append(details)
                success_count += 1
                print("✓")
                
                # Rate limiting (skip sleep on last item)
                if i < len(filtered_devices) - 1:
                    time.sleep(sleep_seconds)
                    
            except requests.exceptions.HTTPError as e:
                print(f"✗ HTTP {e.response.status_code}")
                detailed_devices.append(device)
                error_count += 1
            except requests.exceptions.RequestException as e:
                print(f"✗ {type(e).__name__}")
                detailed_devices.append(device)
                error_count += 1
        
        print("-" * 50)
        print(f"Success: {success_count}, Errors: {error_count}")
        
        filtered_devices = detailed_devices
    
    return filtered_devices


def generate_output_filename(risk_class: str, amount: int) -> str:
    """Generate output filename with risk class and amount."""
    risk_part = risk_class.lower() if risk_class else "all"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"eudamed_class{risk_part}_{amount}devices_{timestamp}.json"


def save_results(devices: list, output_file: str):
    """Save devices to JSON file."""
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(devices)} devices to: {output_path.absolute()}")


def get_text_value(field) -> str:
    """Extract text value from EUDAMED's multilingual text structure."""
    if field is None:
        return "N/A"
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        if "texts" in field:
            texts = field.get("texts", [])
            if texts and len(texts) > 0:
                return texts[0].get("text", "N/A")
        if "code" in field:
            # Extract readable part from codes like "refdata.risk-class.class-iia"
            code = field.get("code", "")
            return code.split(".")[-1] if "." in code else code
        if "text" in field:
            return field.get("text", "N/A")
    return str(field) if field else "N/A"


def format_bool(value) -> str:
    """Format boolean for display."""
    if value is True:
        return "✓ Yes"
    elif value is False:
        return "✗ No"
    return "—"


def print_summary(devices: list, max_display: int = None):
    """Print detailed information for each device with MDR classification-relevant fields."""
    if max_display is None:
        max_display = len(devices)
    
    print(f"\n{'=' * 70}")
    print(f"DETAILED DEVICE INFORMATION ({len(devices)} devices)")
    print('=' * 70)
    
    for i, device in enumerate(devices[:max_display]):
        print(f"\n{'─' * 70}")
        print(f"DEVICE {i+1} of {len(devices)}")
        print('─' * 70)
        
        # === BASIC IDENTIFICATION ===
        print("\n📋 IDENTIFICATION")
        
        # Trade name (can be nested structure or string)
        trade_name = device.get("tradeName")
        print(f"   Trade Name:    {get_text_value(trade_name)}")
        
        # Primary DI
        primary_di = device.get("primaryDi")
        if isinstance(primary_di, dict):
            print(f"   Primary DI:    {primary_di.get('code', 'N/A')}")
        else:
            print(f"   Primary DI:    {primary_di or 'N/A'}")
        
        # Reference
        print(f"   Reference:     {device.get('reference', 'N/A')}")
        
        # === CLASSIFICATION ===
        print("\n🏷️  CLASSIFICATION (MDR)")
        
        # Risk class
        risk_class = device.get("riskClass", {})
        print(f"   Risk Class:    {get_text_value(risk_class)}")
        
        # Legislation
        legislation = device.get("legislation", {})
        print(f"   Legislation:   {get_text_value(legislation)}")
        
        # Device status
        device_status = device.get("deviceStatus", {})
        if isinstance(device_status, dict):
            status_type = device_status.get("type", {})
            print(f"   Status:        {get_text_value(status_type)}")
        
        # === MDR CLASSIFICATION CRITERIA ===
        print("\n⚙️  MDR CLASSIFICATION CRITERIA")
        
        # Active device (Rule 9-13, 22)
        print(f"   Active:                    {format_bool(device.get('active'))}")
        
        # Implantable (Rule 8)
        print(f"   Implantable:               {format_bool(device.get('implantable'))}")
        
        # Invasive characteristics
        # Note: "invasive" might be in different structures, checking common ones
        surgically_invasive = device.get("surgicallyInvasive")
        print(f"   Surgically Invasive:       {format_bool(surgically_invasive)}")
        
        # Reusable surgical instrument (Rule 6)
        reusable = device.get("reusable")
        print(f"   Reusable:                  {format_bool(reusable)}")
        
        # Single use
        single_use = device.get("singleUse")
        print(f"   Single Use:                {format_bool(single_use)}")
        
        # Sterile (relevant for various rules)
        sterile = device.get("sterile")
        print(f"   Sterile:                   {format_bool(sterile)}")
        
        # Sterilization required
        sterilization = device.get("sterilization")
        print(f"   Sterilization Required:    {format_bool(sterilization)}")
        
        # === SUBSTANCE-RELATED (Rules 14, 18, 19, 21) ===
        print("\n🧪 SUBSTANCES & MATERIALS")
        
        # Medicinal product (Rule 14)
        medicinal = device.get("medicinalProduct")
        print(f"   Medicinal Product:         {format_bool(medicinal)}")
        
        # Human tissues/cells (Rule 18)
        human_tissues = device.get("humanTissues")
        print(f"   Human Tissues:             {format_bool(human_tissues)}")
        
        # Human product (blood derivatives, etc.)
        human_product = device.get("humanProduct")
        print(f"   Human Product:             {format_bool(human_product)}")
        
        # Animal tissues (Rule 18)
        animal_tissues = device.get("animalTissues")
        print(f"   Animal Tissues:            {format_bool(animal_tissues)}")
        
        # CMR substances (carcinogenic, mutagenic, toxic to reproduction)
        cmr = device.get("cmrSubstance")
        print(f"   CMR Substance:             {format_bool(cmr)}")
        
        # Endocrine disruptor
        endocrine = device.get("endocrineDisruptor")
        print(f"   Endocrine Disruptor:       {format_bool(endocrine)}")
        
        # Microbial substances
        microbial = device.get("microbialSubstances")
        print(f"   Microbial Substances:      {format_bool(microbial)}")
        
        # === FUNCTIONAL CHARACTERISTICS ===
        print("\n🔧 FUNCTIONAL CHARACTERISTICS")
        
        # Measuring function (Rule 10)
        measuring = device.get("measuringFunction")
        print(f"   Measuring Function:        {format_bool(measuring)}")
        
        # Administering medicine (Rules 6, 7, 8, 12)
        admin_medicine = device.get("administeringMedicine")
        print(f"   Administering Medicine:    {format_bool(admin_medicine)}")
        
        # Near patient testing (IVD related)
        near_patient = device.get("nearPatientTesting")
        print(f"   Near Patient Testing:      {format_bool(near_patient)}")
        
        # Self testing (IVD related)
        self_testing = device.get("selfTesting")
        print(f"   Self Testing:              {format_bool(self_testing)}")
        
        # === SPECIAL DEVICE CHARACTERISTICS ===
        print("\n🔬 SPECIAL CHARACTERISTICS")
        
        # Special device type
        special_type = device.get("specialDeviceType", {})
        if special_type:
            print(f"   Special Device Type:       {get_text_value(special_type)}")
        else:
            print(f"   Special Device Type:       —")
        
        # Companion diagnostics
        companion_diag = device.get("companionDiagnostics")
        print(f"   Companion Diagnostics:     {format_bool(companion_diag)}")
        
        # Multi-component
        multi_component = device.get("multiComponent")
        print(f"   Multi-Component:           {format_bool(multi_component)}")
        
        # Latex (relevant for labeling)
        latex = device.get("latex")
        print(f"   Contains Latex:            {format_bool(latex)}")
        
        # EMR (electronic medical record integration)
        emr = device.get("emr")
        print(f"   EMR Integration:           {format_bool(emr)}")
        
        # === VERSION INFO ===
        print("\n📌 VERSION")
        print(f"   Version Number:  {device.get('versionNumber', 'N/A')}")
        print(f"   Latest Version:  {format_bool(device.get('latestVersion'))}")
    
    if len(devices) > max_display:
        print(f"\n... and {len(devices) - max_display} more devices (not shown)")
    
    print(f"\n{'=' * 70}")


def main():
    """Main function with configurable parameters."""
    # ============================================================
    # CONFIGURATION - Modify these values as needed
    # ============================================================
    INPUT_FILE = "eudamed_devices.json"
    RISK_CLASS = "iii"  # Options: 'i', 'iia', 'iib', 'iii', 'a', 'b', 'c', 'd', or None for all
    AMOUNT = 5          # Number of devices to fetch
    SLEEP_SECONDS = 1.0 # Delay between API calls (be nice to the server)
    # ============================================================
    
    print("=" * 60)
    print("EUDAMED Device Enrichment")
    print("=" * 60)
    print(f"Input file: {INPUT_FILE}")
    print(f"Risk class filter: {RISK_CLASS or 'None (all classes)'}")
    print(f"Amount to fetch: {AMOUNT}")
    print("=" * 60)
    
    # Filter and fetch
    devices = filter_devices(
        input_file=INPUT_FILE,
        risk_class=RISK_CLASS,
        limit=AMOUNT,
        fetch_details=True,
        sleep_seconds=SLEEP_SECONDS
    )
    
    # Generate output filename and save
    output_file = generate_output_filename(RISK_CLASS, len(devices))
    save_results(devices, output_file)
    
    # Print summary - show ALL devices
    print_summary(devices)
    
    return devices


if __name__ == "__main__":
    main()