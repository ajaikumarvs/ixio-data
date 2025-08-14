import json, datetime, re, requests
from bs4 import BeautifulSoup

def fetch_ubuntu():
    base_url = "https://releases.ubuntu.com/"
    html = requests.get(base_url).text
    match = re.search(r'>(\d+\.\d+(?:\.\d+)?)</a>', html)
    if not match: return None
    version = match.group(1)
    iso_url = f"{base_url}{version}/ubuntu-{version}-desktop-amd64.iso"
    checksum_url = f"{base_url}{version}/SHA256SUMS"
    sha256 = None
    try:
        for line in requests.get(checksum_url).text.splitlines():
            if iso_url.split("/")[-1] in line:
                sha256 = line.split()[0]; break
    except: pass
    return {"name": "Ubuntu", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_debian():
    base_url = "https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/"
    html = requests.get(base_url).text
    match = re.search(r'href="(debian-[0-9.]+-amd64-DVD-1.iso)"', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "SHA256SUMS"
    sha256 = None
    try:
        for line in requests.get(checksum_url).text.splitlines():
            if iso_name in line:
                sha256 = line.split()[0]; break
    except: pass
    version = re.search(r'debian-([0-9.]+)-', iso_name).group(1)
    return {"name": "Debian", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_fedora():
    iso_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/41/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-41-1.4.iso"
    checksum_url = "https://getfedora.org/static/checksums/41/Workstation/x86_64/Fedora-Workstation-Live-x86_64-41-1.4-CHECKSUM"
    sha256 = None
    try:
        for line in requests.get(checksum_url).text.splitlines():
            if ".iso" in line:
                sha256 = line.split()[0]; break
    except: pass
    return {"name": "Fedora Workstation", "version": "41", "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_arch():
    base_url = "https://mirror.rackspace.com/archlinux/iso/latest/"
    html = requests.get(base_url).text
    match = re.search(r'(archlinux-[0-9.]+-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "sha256sums.txt"
    sha256 = None
    try:
        for line in requests.get(checksum_url).text.splitlines():
            if iso_name in line:
                sha256 = line.split()[0]; break
    except: pass
    version = iso_name.split("-")[1]
    return {"name": "Arch Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_cachyos():
    base_url = "https://mirror.cachyos.org/ISO/latest/"
    html = requests.get(base_url).text
    match = re.search(r'(CachyOS-[0-9.]+-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = None
    try:
        sha256 = requests.get(checksum_url).text.split()[0]
    except: pass
    version = re.search(r'CachyOS-([0-9.]+)-', iso_name).group(1)
    return {"name": "CachyOS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

# TODO: Add Mint, Manjaro, openSUSE, Pop!_OS, elementary, Zorin, MX, Kali (similar approach)

def main():
    output = {"last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "distros": []}
    fetchers = [fetch_ubuntu, fetch_debian, fetch_fedora, fetch_arch, fetch_cachyos]
    for f in fetchers:
        try:
            data = f()
            if data: output["distros"].append(data)
        except Exception as e:
            print(f"Error fetching {f.__name__}: {e}")
    with open("isos/linux.json", "w") as fp:
        json.dump(output, fp, indent=2)

if __name__ == "__main__":
    main()
