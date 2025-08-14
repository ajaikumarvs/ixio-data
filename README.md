Ixio ISO Auto-Updater

Ixio is a cross-platform ISO fetcher that automatically retrieves the latest download links and SHA256 checksums for popular Linux distributions (and soon Windows releases).
This repo uses Python scripts + GitHub Actions to keep isos/linux.json up-to-date automatically.

---

📦 Features

- Fetches the latest versions of 14 popular Linux distributions:
  - Ubuntu
  - Debian
  - Fedora Workstation
  - Arch Linux
  - Linux Mint Cinnamon
  - Manjaro KDE
  - openSUSE Tumbleweed
  - openSUSE Leap
  - Pop!_OS
  - elementary OS
  - Zorin OS
  - MX Linux
  - Kali Linux
  - CachyOS
- Extracts version, architecture, direct ISO URL, and SHA256 checksum.
- Stores everything in a single JSON file:
  {
    "last_updated": "2025-08-14T12:34:56Z",
    "distros": [
      {
        "name": "Ubuntu",
        "version": "24.04.1",
        "arch": ["x86_64"],
        "download_url": "https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-desktop-amd64.iso",
        "checksum": {
          "sha256": "abc123...",
          "url": "https://releases.ubuntu.com/24.04.1/SHA256SUMS"
        }
      }
    ]
  }
- Fully automated updates via GitHub Actions (runs daily).
- No manual version tracking — all data is scraped live.

---

⚙️ How It Works

1. Python Fetcher (scripts/update_linux.py)
   - Contains fetcher functions for each distro.
   - Uses requests + BeautifulSoup + regex to:
     - Find the latest release folder.
     - Identify the correct ISO filename.
     - Download the checksum file.
     - Extract the SHA256 hash for that ISO.
   - Compiles all distro info into isos/linux.json.

2. JSON Output
   - Saved in isos/linux.json.
   - Always contains the last update time in UTC.
   - Used by Ixio to show the latest ISO download list.

3. GitHub Actions (.github/workflows/update_linux.yml)
   - Runs daily at midnight UTC (or on manual trigger).
   - Installs Python, dependencies, and runs update_linux.py.
   - Commits updated linux.json back to the repo.

---

🚀 Usage

Run Locally
# Clone repo
git clone https://github.com/ajaikumarvs/ixio-data.git
cd ixio-data

# Install dependencies
pip install -r requirements.txt

# Run the updater
python scripts/update_linux.py

Output will be saved in:
isos/linux.json

Requirements
- Python 3.8+
- Dependencies:
  requests
  beautifulsoup4
  Install with:
  pip install -r requirements.txt

---

🤖 Automation

This repo includes:
.github/workflows/update_linux.yml
Which:
1. Runs daily or on-demand.
2. Generates updated isos/linux.json.
3. Commits changes automatically.

---

📌 Future Plans
- Add Windows ISO fetcher.
- Add macOS recovery image links.
- Include multiple architectures (ARM, RISC-V).

---

📝 License
MIT License – You’re free to use and adapt.

---

💡 Example Ixio Integration
Your app can simply:
import json

with open("isos/linux.json") as f:
    data = json.load(f)

for distro in data["distros"]:
    print(f"{distro['name']} {distro['version']} → {distro['download_url']}")

---
