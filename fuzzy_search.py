"""
This is a file for fuzzy search functionality.
This means taking the result of the general api response and iterating over the 
results based on search criteria to find the best match.
"""
# use python request library to make get requests to this endpoint, parameters req: page, pageSize
#https://openregulatory.github.io/eudamed-api/devices/udiDiData
import requests
import json

# Create the function here to make the simple api get call (ONLY FILL THIS FOR NOW)
def fuzzy_search(page=1, pageSize=10, size=10, iso2Code="en", languageIso2Code="en"):
    url = "https://ec.europa.eu/tools/eudamed/api/devices/udiDiData"
    params = {
        "page": page,
        "pageSize": pageSize,
        "size": size,
        "iso2Code": iso2Code,
        "languageIso2Code": languageIso2Code
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an error for bad status codes
    
    # Parse JSON and pretty print
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    return data



# Add another function for another endpoint here, this one is more for a specific device (ONLY FILL THIS FUNCTION IN FOR NOW)
"""
https://ec.europa.eu/tools/eudamed/api/devices/udiDiData/{deviceId}
== path Parameters ==
-deviceId
required	
string <uuid>
ID of device to return
== query Parameters ==
- languageIso2Code
required	
string
Probably the language of what to return. Commonly en.

"""
def get_specific_device(deviceId='121f9fdc-197a-4a4e-a415-b5d80b54a8fe', languageIso2Code="en"):
    url = f"https://ec.europa.eu/tools/eudamed/api/devices/udiDiData/{deviceId}"
    params = {
        "languageIso2Code": languageIso2Code
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    return data

if __name__ == "__main__":
    fuzzy_search()
    #get_specific_device()
    