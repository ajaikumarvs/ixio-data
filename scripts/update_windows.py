# update_windows.py
import json
import datetime
from pathlib import Path

WINDOWS_ISOS = [
    {
        "name": "Windows 10",
        "version": "22H2",
        "source": "Microsoft Official",
        "download_page": "https://www.microsoft.com/software-download/windows10",
        "direct_links": []
    },
    {
        "name": "Windows 11",
        "version": "24H2",
        "source": "Microsoft Official",
        "download_page": "https://www.microsoft.com/software-download/windows11",
        "direct_links": []
    },
    {
        "name": "Windows Server 2025",
        "version": "RTM",
        "source": "Microsoft Evaluation Center",
        "download_page": "https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2025",
        "direct_links": []
    }
]

def main():
    data = {
        "last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "windows": WINDOWS_ISOS
    }

    # Write atomically to isos/windows.json
    output_path = Path("isos/windows.json")
    temp_path = output_path.with_suffix(".tmp")

    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    temp_path.replace(output_path)
    print(f"✅ Updated {output_path} at {data['last_updated']}")

if __name__ == "__main__":
    main()
