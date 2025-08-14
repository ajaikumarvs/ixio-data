import json, datetime, re, requests
from bs4 import BeautifulSoup

def get_sha256_from_text(text, filename):
    """Extract SHA256 from text given a filename."""
    # Fedora PGP-signed format: SHA256 (filename) = hash
    match = re.search(rf"SHA256\s*\({re.escape(filename)}\)\s*=\s*([a-fA-F0-9]{{64}})", text)
    if match:
        return match.group(1)
    # Simple 'hash filename' format
    for line in text.splitlines():
        if filename in line:
            parts = line.split()
            for part in parts:
                if re.fullmatch(r"[a-fA-F0-9]{64}", part):
                    return part
    return None

# ------------------ Fetchers ------------------ #
def fetch_ubuntu():
    base_url = "https://releases.ubuntu.com/"
    html = requests.get(base_url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    # First non-LTS or LTS release link
    link = next((a['href'] for a in soup.find_all('a', href=True) if re.match(r'\d+\.\d+', a['href'])), None)
    if not link: return None
    version = link.strip("/")
    iso_name = f"ubuntu-{version}-desktop-amd64.iso"
    iso_url = f"{base_url}{version}/{iso_name}"
    checksum_url = f"{base_url}{version}/SHA256SUMS"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    return {"name": "Ubuntu", "version": version, "arch": ["x86_64"], "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_debian():
    base_url = "https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(debian-[0-9.]+-amd64-DVD-1\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "SHA256SUMS"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    version = re.search(r'debian-([0-9.]+)-', iso_name).group(1)
    return {"name": "Debian", "version": version, "arch": ["x86_64"], "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_fedora():
    # Hardcoded current release to avoid scraping complexity
    version = "41"
    iso_name = f"Fedora-Workstation-Live-x86_64-{version}-1.4.iso"
    iso_url = f"https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Workstation/x86_64/iso/{iso_name}"
    checksum_url = f"https://getfedora.org/static/checksums/{version}/Workstation/x86_64/Fedora-Workstation-Live-x86_64-{version}-1.4-CHECKSUM"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    return {"name": "Fedora Workstation", "version": version, "arch": ["x86_64"], "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_arch():
    base_url = "https://mirror.rackspace.com/archlinux/iso/latest/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(archlinux-[0-9.]+-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "sha256sums.txt"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    version = iso_name.split("-")[1]
    return {"name": "Arch Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_cachyos():
    base_url = "https://mirror.cachyos.org/ISO/latest/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(CachyOS-[0-9.]+-[0-9.]+-x86_64\.iso)', html) or \
            re.search(r'(CachyOS-[0-9.]+-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0] if requests.get(checksum_url).status_code == 200 else None
    version = re.search(r'CachyOS-([0-9.]+)-', iso_name).group(1)
    return {"name": "CachyOS", "version": version, "arch": ["x86_64"], "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}}

# TODO: Implement Linux Mint, Manjaro, openSUSE (Tumbleweed & Leap), Pop!_OS, elementary OS, Zorin OS, MX Linux, Kali Linux

def main():
    output = {"last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "distros": []}
    fetchers = [
        fetch_ubuntu,
        fetch_debian,
        fetch_fedora,
        fetch_arch,
        fetch_cachyos
        # More fetchers will be added here
    ]
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
