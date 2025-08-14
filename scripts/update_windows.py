import json
import datetime
import requests

# Microsoft TechBench API endpoint
API_URL = "https://www.microsoft.com/en-us/api/controls/contentinclude/html"

# Windows editions to track
WINDOWS_EDITIONS = [
    {"name": "Windows 10", "product_id": "cb96bdee-8629-4be4-80d4-f5568c1c3c4c"},
    {"name": "Windows 11", "product_id": "99b8a1f1-92e3-4b43-b5ee-7481af14c1c2"}
]

def fetch_windows_iso(product_id):
    payload = {
        "pageId": "b6d606b4-9f45-4c7b-8287-1d79da2d6e4f",
        "host": "www.microsoft.com",
        "segments": ["software-download", "windows11"],  # Windows 10 or 11 path changes here
        "query": {"productEditionId": product_id}
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(API_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        return None
    return resp.text

def main():
    output = {
        "last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "windows": []
    }

    for edition in WINDOWS_EDITIONS:
        iso_info = fetch_windows_iso(edition["product_id"])
        if iso_info:
            output["windows"].append({
                "name": edition["name"],
                "source": "Microsoft Official",
                "download_page_html": iso_info  # UI will parse to get actual links
            })

    with open("isos/windows.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
