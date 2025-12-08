import requests
import json
import time
from pathlib import Path
from datetime import datetime


def fuzzy_search(page=1, pageSize=300, size=300, iso2Code="en", languageIso2Code="en"):
    """Fetch a single page of device data from EUDAMED API."""
    url = "https://ec.europa.eu/tools/eudamed/api/devices/udiDiData"
    params = {
        "page": page,
        "pageSize": pageSize,
        "size": size,
        "iso2Code": iso2Code,
        "languageIso2Code": languageIso2Code
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def scrape_all_devices(
    output_file="eudamed_devices.json",
    start_page=1,
    end_page=None,
    page_size=300,
    sleep_seconds=3,
    iso2Code="en",
    languageIso2Code="en"
):
    """
    Scrape device data from EUDAMED API with pagination.
    
    Args:
        output_file: Path to the output JSON file
        start_page: First page to fetch (1-indexed)
        end_page: Last page to fetch (None = fetch all pages)
        page_size: Number of devices per page
        sleep_seconds: Seconds to wait between requests
        iso2Code: ISO2 country code
        languageIso2Code: Language ISO2 code
    """
    output_path = Path(output_file)
    all_devices = []
    
    # If file exists, load existing data to append
    if output_path.exists():
        print(f"Loading existing data from {output_file}...")
        with open(output_path, "r", encoding="utf-8") as f:
            all_devices = json.load(f)
        print(f"Loaded {len(all_devices)} existing devices")
    
    current_page = start_page
    total_pages = None
    
    print(f"\nStarting scrape from page {start_page}...")
    print(f"Sleep between requests: {sleep_seconds} seconds")
    print("-" * 50)
    
    while True:
        try:
            print(f"\nFetching page {current_page}...", end=" ")
            
            data = fuzzy_search(
                page=current_page,
                pageSize=page_size,
                size=page_size,
                iso2Code=iso2Code,
                languageIso2Code=languageIso2Code
            )
            
            # Get pagination info from first request
            if total_pages is None:
                total_pages = data.get("totalPages", 1)
                total_elements = data.get("totalElements", 0)
                print(f"\nTotal pages: {total_pages}, Total devices: {total_elements}")
                
                # Adjust end_page if not specified or out of range
                if end_page is None or end_page > total_pages:
                    end_page = total_pages
                print(f"Will fetch pages {start_page} to {end_page}")
                print("-" * 50)
            
            # Extract devices from this page
            page_devices = data.get("content", [])
            num_devices = len(page_devices)
            all_devices.extend(page_devices)
            
            print(f"Got {num_devices} devices. Total collected: {len(all_devices)}")
            
            # Save after each page (safe incremental saving)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_devices, f, ensure_ascii=False, indent=2)
            
            # Check if we're done
            is_last = data.get("last", False)
            if is_last or current_page >= end_page:
                print(f"\n{'=' * 50}")
                print(f"Scraping complete!")
                print(f"Total devices collected: {len(all_devices)}")
                print(f"Data saved to: {output_path.absolute()}")
                break
            
            # Move to next page
            current_page += 1
            
            # Rate limiting sleep
            print(f"Sleeping {sleep_seconds} seconds...")
            time.sleep(sleep_seconds)
            
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching page {current_page}: {e}")
            print("Saving progress and stopping...")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_devices, f, ensure_ascii=False, indent=2)
            print(f"Progress saved. Resume from page {current_page}")
            raise
        
        except KeyboardInterrupt:
            print(f"\n\nInterrupted by user. Saving progress...")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_devices, f, ensure_ascii=False, indent=2)
            print(f"Progress saved to {output_file}")
            print(f"Resume from page {current_page + 1}")
            break
    
    return all_devices


def main():
    """Main entry point with example usage."""
    # Configuration - adjust these as needed
    config = {
        "output_file": "eudamed_devices.json",
        "start_page": 1,
        "end_page": 60,      # None = fetch all pages, or set a specific number
        "page_size": 300,
        "sleep_seconds": 3,    # Be nice to the API
    }
    
    print("EUDAMED Device Scraper")
    print("=" * 50)
    print(f"Output file: {config['output_file']}")
    print(f"Start page: {config['start_page']}")
    print(f"End page: {config['end_page'] or 'all'}")
    print(f"Page size: {config['page_size']}")
    print(f"Sleep between requests: {config['sleep_seconds']}s")
    print("=" * 50)
    
    devices = scrape_all_devices(**config)
    
    print(f"\nDone! Collected {len(devices)} devices total.")


if __name__ == "__main__":
    main()