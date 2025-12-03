import json
import time
import requests
from pathlib import Path


def fetch_device_details(basic_udi_di_id, iso2Code="en", languageIso2Code="en"):
    """Fetch detailed device information from EUDAMED API."""
    url = f"https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/{basic_udi_di_id}"
    params = {
        "iso2Code": iso2Code,
        "languageIso2Code": languageIso2Code
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def filter_devices(
    input_file="eudamed_devices.json",
    output_file=None,
    risk_class=None,
    limit=None,
    fetch_details=True,
    sleep_seconds=2
):
    """
    Filter devices from the scraped EUDAMED data and fetch full details.
    
    Args:
        input_file: Path to the scraped JSON file
        output_file: Optional path to save filtered results (None = don't save)
        risk_class: Filter by risk class ('i', 'iia', 'iib', 'iii', etc.)
        limit: Maximum number of devices to return
        fetch_details: If True, fetch full details from /devices/basicUdiData/{id}
        sleep_seconds: Seconds to wait between API requests
    
    Returns:
        List of filtered devices (one per unique basicUdi) with full details
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    print(f"Loading devices from {input_file}...")
    with open(input_path, "r", encoding="utf-8") as f:
        all_devices = json.load(f)
    
    print(f"Loaded {len(all_devices)} total devices")
    
    # Build the risk class code if specified
    risk_class_code = None
    if risk_class:
        risk_class_code = f"refdata.risk-class.class-{risk_class.lower()}"
        print(f"Filtering by risk class: {risk_class_code}")
    
    # Filter and deduplicate
    seen_basic_udis = set()
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
        
        seen_basic_udis.add(basic_udi)
        filtered_devices.append(device)
        
        # Check limit
        if limit and len(filtered_devices) >= limit:
            break
    
    print(f"Found {len(filtered_devices)} unique devices (by basicUdi)")
    
    # Fetch full details for each device
    if fetch_details and filtered_devices:
        print(f"\nFetching detailed info for {len(filtered_devices)} devices...")
        print(f"Sleep between requests: {sleep_seconds} seconds")
        print("-" * 50)
        
        detailed_devices = []
        for i, device in enumerate(filtered_devices):
            # Get the ID needed for the API call (uuid field matches the API's expected format)
            basic_udi_di_id = device.get("uuid")
            
            if not basic_udi_di_id:
                print(f"[{i+1}/{len(filtered_devices)}] No ID found, skipping...")
                detailed_devices.append(device)  # Keep original if no ID
                continue
            
            try:
                print(f"[{i+1}/{len(filtered_devices)}] Fetching {device.get('basicUdi', 'unknown')}...", end=" ")
                details = fetch_device_details(basic_udi_di_id)
                detailed_devices.append(details)
                print("OK")
                
                # Rate limiting (skip sleep on last item)
                if i < len(filtered_devices) - 1:
                    time.sleep(sleep_seconds)
                    
            except requests.exceptions.RequestException as e:
                print(f"ERROR: {e}")
                detailed_devices.append(device)  # Keep original on error
        
        filtered_devices = detailed_devices
        print("-" * 50)
        print(f"Fetched details for {len(filtered_devices)} devices")
    
    # Save if output file specified
    if output_file:
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(filtered_devices, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_path.absolute()}")
    
    return filtered_devices


def print_device_summary(devices, max_display=10):
    """Print full information for each filtered device."""
    print(f"\n{'=' * 60}")
    print(f"Showing first {min(len(devices), max_display)} devices:")
    print('=' * 60)
    
    for i, device in enumerate(devices[:max_display]):
        print(f"\n[Device {i+1}]")
        print(json.dumps(device, indent=2, ensure_ascii=False))
        print("-" * 60)


def main():
    """Example usage."""
    # Example: Get 50 unique IIa devices with full details
    devices = filter_devices(
        input_file="eudamed_devices.json",
        output_file="test_detailed.json",
        risk_class="iia",
        limit=2,
        fetch_details=True,
        sleep_seconds=2
    )
    
    print_device_summary(devices)
    
    return devices


if __name__ == "__main__":
    main()