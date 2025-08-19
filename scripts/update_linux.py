import json, datetime, re, requests
from bs4 import BeautifulSoup

def get_sha256_from_text(text, filename):
    match = re.search(rf"SHA256\s*\({re.escape(filename)}\)\s*=\s*([a-fA-F0-9]{{64}})", text)
    if match:
        return match.group(1)
    for line in text.splitlines():
        if filename in line:
            parts = line.split()
            for part in parts:
                if re.fullmatch(r"[a-fA-F0-9]{64}", part):
                    return part
    return None

# ------------------ Fetchers ------------------ #
def _parse_ubuntu_versions(index_html):
    soup = BeautifulSoup(index_html, "html.parser")
    versions = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # versions like 24.04.1/, 22.04.5/
        if re.fullmatch(r"\d+\.\d+(?:\.\d+)?/", href):
            versions.append(href.strip('/'))
    # sort versions numerically by parts
    def key(v):
        return tuple(int(p) for p in v.split('.'))
    versions = sorted(set(versions), key=key)
    return versions

def fetch_ubuntu(max_versions: int = 3):
    """Return up to max_versions latest Ubuntu desktop x86_64 ISOs (latest first)."""
    base_url = "https://releases.ubuntu.com/"
    html = requests.get(base_url, timeout=15).text
    versions = _parse_ubuntu_versions(html)
    if not versions:
        return None
    selected = list(reversed(versions))[:max_versions]
    out = []
    for version in selected:
        iso_name = f"ubuntu-{version}-desktop-amd64.iso"
        iso_url = f"{base_url}{version}/{iso_name}"
        checksum_url = f"{base_url}{version}/SHA256SUMS"
        try:
            sha_text = requests.get(checksum_url, timeout=15).text
            sha256 = get_sha256_from_text(sha_text, iso_name)
        except Exception:
            sha256 = None
        out.append({
            "name": "Ubuntu",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out

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
    return {"name": "Debian", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_fedora():
    version = "41"
    iso_name = f"Fedora-Workstation-Live-x86_64-{version}-1.4.iso"
    iso_url = f"https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Workstation/x86_64/iso/{iso_name}"
    checksum_url = f"https://getfedora.org/static/checksums/{version}/Workstation/x86_64/Fedora-Workstation-Live-x86_64-{version}-1.4-CHECKSUM"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    return {"name": "Fedora Workstation", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

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
    return {"name": "Arch Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_linuxmint():
    base_url = "https://mirrors.edge.kernel.org/linuxmint/stable/"
    html = requests.get(base_url, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions: return None
    version = sorted(versions, key=lambda v: list(map(int, v.split('.'))))[-1]
    folder = f"{base_url}{version}/"
    html = requests.get(folder).text
    match = re.search(r'(linuxmint-\d+-cinnamon-64bit\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = folder + iso_name
    checksum_url = folder + "sha256sum.txt"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    return {"name": "Linux Mint Cinnamon", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_manjaro():
    base_url = "https://download.manjaro.org/kde/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(manjaro-kde-[0-9.]+-minimal-.*-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0]
    version = re.search(r'manjaro-kde-([0-9.]+)-', iso_name).group(1)
    return {"name": "Manjaro KDE", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_opensuse_tumbleweed():
    base_url = "https://download.opensuse.org/tumbleweed/iso/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(openSUSE-Tumbleweed-DVD-x86_64-[0-9]+\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0]
    version = re.search(r'([0-9]+)\.iso', iso_name).group(1)
    return {"name": "openSUSE Tumbleweed", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_opensuse_leap():
    base_url = "https://download.opensuse.org/distribution/leap/"
    html = requests.get(base_url, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions: return None
    version = sorted(versions, key=lambda v: list(map(int, v.split('.'))))[-1]
    folder = f"{base_url}{version}/iso/"
    html = requests.get(folder).text
    match = re.search(r'(openSUSE-Leap-[0-9.]+-DVD-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = folder + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0]
    return {"name": "openSUSE Leap", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_popos():
    base_url = "https://pop-iso.sfo2.cdn.digitaloceanspaces.com/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(pop-os_[0-9.]+_amd64_intel_.*\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.strip()
    version = re.search(r'pop-os_([0-9.]+)_', iso_name).group(1)
    return {"name": "Pop!_OS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_elementary():
    base_url = "https://mirror.elementary.io/iso/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(elementaryos-[0-9.]+-stable\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "SHA256SUMS"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    version = re.search(r'elementaryos-([0-9.]+)-', iso_name).group(1)
    return {"name": "elementary OS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_zorin():
    base_url = "https://mirrors.edge.kernel.org/zorinos-isos/stable/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(Zorin-OS-[0-9.]+-Core-64-bit\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "SHA256SUMS"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    version = re.search(r'Zorin-OS-([0-9.]+)-', iso_name).group(1)
    return {"name": "Zorin OS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_mxlinux():
    base_url = "https://mxlinux.org/iso/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(MX-[0-9.]+_x64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0]
    version = re.search(r'MX-([0-9.]+)_', iso_name).group(1)
    return {"name": "MX Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_kali():
    base_url = "https://cdimage.kali.org/kali-rolling/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(kali-linux-[0-9.]+-live-amd64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = base_url + "SHA256SUMS"
    sha256 = get_sha256_from_text(requests.get(checksum_url).text, iso_name)
    version = re.search(r'kali-linux-([0-9.]+)-', iso_name).group(1)
    return {"name": "Kali Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_cachyos():
    base_url = "https://mirror.cachyos.org/ISO/latest/"
    html = requests.get(base_url, timeout=15).text
    match = re.search(r'(CachyOS-[0-9.]+-[0-9.]+-x86_64\.iso)', html) or re.search(r'(CachyOS-[0-9.]+-x86_64\.iso)', html)
    if not match: return None
    iso_name = match.group(1)
    iso_url = base_url + iso_name
    checksum_url = iso_url + ".sha256"
    sha256 = requests.get(checksum_url).text.split()[0] if requests.get(checksum_url).status_code == 200 else None
    version = re.search(r'CachyOS-([0-9.]+)-', iso_name).group(1)
    return {"name": "CachyOS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

# ------------------ Main ------------------ #
def main():
    output = {"last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "distros": []}
    fetchers = [
        fetch_ubuntu, fetch_debian, fetch_fedora, fetch_arch, fetch_linuxmint, fetch_manjaro,
        fetch_opensuse_tumbleweed, fetch_opensuse_leap, fetch_popos, fetch_elementary,
        fetch_zorin, fetch_mxlinux, fetch_kali, fetch_cachyos
    ]
    for f in fetchers:
        try:
            data = f()
            if not data:
                continue
            if isinstance(data, list):
                output["distros"].extend(data)
            else:
                output["distros"].append(data)
        except Exception as e:
            print(f"Error fetching {f.__name__}: {e}")
    with open("isos/linux.json", "w") as fp:
        json.dump(output, fp, indent=2)

if __name__ == "__main__":
    main()
