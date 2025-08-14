import json
import datetime
import requests
from bs4 import BeautifulSoup

# Static distros with their update logic
DISTROS = [
    {
        "name": "Ubuntu",
        "arch": ["x86_64"],
        "version_url": "https://releases.ubuntu.com/",
        "parser": "ubuntu"
    },
    {
        "name": "Debian",
        "arch": ["x86_64"],
        "version_url": "https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/",
        "parser": "debian"
    },
    {
        "name": "Fedora Workstation",
        "arch": ["x86_64"],
        "version_url": "https://getfedora.org/en/workstation/download/",
        "parser": "fedora"
    },
    {
        "name": "Arch Linux",
        "arch": ["x86_64"],
        "version_url": "https://archlinux.org/download/",
        "parser": "arch"
    },
    {
        "name": "Linux Mint Cinnamon",
        "arch": ["x86_64"],
        "version_url": "https://linuxmint.com/download.php",
        "parser": "mint"
    },
    {
        "name": "Manjaro KDE",
        "arch": ["x86_64"],
        "version_url": "https://manjaro.org/download/",
        "parser": "manjaro"
    }
]

def get_ubuntu():
    r = requests.get("https://releases.ubuntu.com/")
    soup = BeautifulSoup(r.text, "html.parser")
    link = soup.find("a", href=lambda href: href and "ubuntu-" in href and href.endswith("-desktop-amd64.iso"))
    if not link:
        return None
    href = link["href"]
    version = href.split("-")[1]
    base = "https://releases.ubuntu.com/"
    checksum_url = base + version + "/SHA256SUMS"
    return {
        "version": version,
        "download_url": base + version + "/" + href,
        "checksum_url": checksum_url
    }

# NOTE: For brevity, other distro-specific parsers would be implemented similarly.

def main():
    output = {
        "last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "distros": []
    }

    for distro in DISTROS:
        if distro["parser"] == "ubuntu":
            data = get_ubuntu()
        else:
            # TODO: Implement other parsers
            data = None

        if data:
            output["distros"].append({
                "name": distro["name"],
                "version": data["version"],
                "arch": distro["arch"],
                "download_url": data["download_url"],
                "checksum_url": data["checksum_url"]
            })

    with open("isos/linux.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
