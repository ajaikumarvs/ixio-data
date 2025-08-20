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

def fetch_linuxmint(max_versions: int = 2):
    base_url = "https://mirrors.edge.kernel.org/linuxmint/stable/"
    html = requests.get(base_url, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        return None
    ordered = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for version in selected:
        folder = f"{base_url}{version}/"
        listing = requests.get(folder, timeout=15).text
        m = re.search(r'(linuxmint-\d+-cinnamon-64bit\.iso)', listing)
        if not m:
            continue
        iso_name = m.group(1)
        iso_url = folder + iso_name
        checksum_url = folder + "sha256sum.txt"
        try:
            sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
        except Exception:
            sha256 = None
        out.append({
            "name": "Linux Mint Cinnamon",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

def fetch_manjaro(max_versions: int = 2):
    base_url = "https://download.manjaro.org/kde/"
    html = requests.get(base_url, timeout=15).text
    # collect multiple matches
    matches = re.findall(r"(manjaro-kde-([0-9.]+)-[^\s\"']*-x86_64\.iso)", html)
    if not matches:
        return None
    # unique by version
    by_ver = {}
    for full, ver in matches:
        by_ver[ver] = full
    def key(v):
        return tuple(int(p) for p in v.split('.'))
    ordered = sorted(by_ver.keys(), key=key)
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for ver in selected:
        iso_name = by_ver[ver]
        iso_url = base_url + iso_name
        checksum_url = iso_url + ".sha256"
        try:
            sha256 = requests.get(checksum_url, timeout=15).text.split()[0]
        except Exception:
            sha256 = None
        out.append({
            "name": "Manjaro KDE",
            "version": ver,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

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

def fetch_opensuse_leap(max_versions: int = 2):
    base_url = "https://download.opensuse.org/distribution/leap/"
    html = requests.get(base_url, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        return None
    ordered = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for version in selected:
        folder = f"{base_url}{version}/iso/"
        listing = requests.get(folder, timeout=15).text
        m = re.search(r'(openSUSE-Leap-[0-9.]+-DVD-x86_64\.iso)', listing)
        if not m:
            continue
        iso_name = m.group(1)
        iso_url = folder + iso_name
        checksum_url = iso_url + ".sha256"
        try:
            sha256 = requests.get(checksum_url, timeout=15).text.split()[0]
        except Exception:
            sha256 = None
        out.append({
            "name": "openSUSE Leap",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

def fetch_popos(max_versions: int = 2):
    base_url = "https://pop-iso.sfo2.cdn.digitaloceanspaces.com/"
    html = requests.get(base_url, timeout=15).text
    matches = re.findall(r"(pop-os_([0-9.]+)_amd64_intel_[^\s\"']*\.iso)", html)
    if not matches:
        return None
    # prefer unique versions
    by_ver = {}
    for full, ver in matches:
        by_ver[ver] = full
    def key(v):
        return tuple(int(p) for p in v.split('.'))
    ordered = sorted(by_ver.keys(), key=key)
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for ver in selected:
        iso_name = by_ver[ver]
        iso_url = base_url + iso_name
        checksum_url = iso_url + ".sha256"
        try:
            sha256 = requests.get(checksum_url, timeout=15).text.strip().split()[0]
        except Exception:
            sha256 = None
        out.append({
            "name": "Pop!_OS",
            "version": ver,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

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

def fetch_zorin(max_versions: int = 2):
    base_url = "https://mirrors.edge.kernel.org/zorinos-isos/stable/"
    html = requests.get(base_url, timeout=15).text
    matches = re.findall(r'(Zorin-OS-([0-9.]+)-Core-64-bit\.iso)', html)
    if not matches:
        return None
    by_ver = {}
    for full, ver in matches:
        by_ver[ver] = full
    def key(v):
        return tuple(int(p) for p in v.split('.'))
    ordered = sorted(by_ver.keys(), key=key)
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for ver in selected:
        iso_name = by_ver[ver]
        iso_url = base_url + iso_name
        checksum_url = base_url + "SHA256SUMS"
        try:
            sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
        except Exception:
            sha256 = None
        out.append({
            "name": "Zorin OS",
            "version": ver,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

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

# --- Additional requested distros --- #
def fetch_endeavouros():
    # Use GitHub releases latest page to find ISO and sums
    url = "https://github.com/endeavouros-team/ISO/releases/latest"
    html = requests.get(url, timeout=15, headers={"User-Agent": "ixio-bot"}).text
    iso_match = re.search(r'href="([^"]+\.iso)"', html)
    if not iso_match:
        return None
    href = iso_match.group(1)
    if href.startswith("/"):
        iso_url = "https://github.com" + href
    else:
        iso_url = href
    # Try to extract version from filename
    iso_name = iso_url.split("/")[-1]
    ver_match = re.search(r"(\d{4}\.\d{2}|\d+\.\d+)", iso_name)
    version = ver_match.group(1) if ver_match else "latest"
    checksum_url = url
    return {"name": "EndeavourOS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": None, "url": checksum_url}}

def fetch_parrot():
    base = "https://mirror.parrot.sh/parrot/iso/rolling/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'(Parrot-home-rolling-.*?_amd64\.iso)', html)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = base + iso_name
    # common sums file name
    checksum_url = base + "SHA256SUMS"
    try:
        sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
    except Exception:
        sha256 = None
    ver = re.search(r'Parrot-home-rolling-([0-9.]+)-', iso_name)
    version = ver.group(1) if ver else "rolling"
    return {"name": "Parrot Security OS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_tails(max_versions: int = 2):
    base = "https://mirrors.edge.kernel.org/tails/stable/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="([0-9.]+)/"', html)
    if not versions:
        return None
    def key(v):
        return tuple(int(p) for p in v.split('.'))
    ordered = sorted(set(versions), key=key)
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for version in selected:
        folder = f"{base}{version}/"
        listing = requests.get(folder, timeout=15).text
        m = re.search(r"(tails-amd64-[^\s\"']*?\.iso)", listing)
        if not m:
            continue
        iso_name = m.group(1)
        iso_url = folder + iso_name
        checksum_url = iso_url + ".sha256sum"
        try:
            sha_text = requests.get(checksum_url, timeout=15).text
            sha256 = sha_text.split()[0] if sha_text else None
        except Exception:
            sha256 = None
        out.append({
            "name": "Tails",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        })
    return out or None

def fetch_qubes():
    base = "https://ftp.qubes-os.org/iso/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'(Qubes-R[0-9.]+-x86_64\.iso)', html)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = base + iso_name
    checksum_url = base + "SHA256SUMS"
    try:
        sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
    except Exception:
        sha256 = None
    ver = re.search(r'Qubes-R([0-9.]+)-', iso_name)
    version = ver.group(1) if ver else "R"
    return {"name": "Qubes OS", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_puppy():
    base = "https://distro.ibiblio.org/puppylinux/puppy64/"
    html = requests.get(base, timeout=15).text
    dirs = re.findall(r'href="([^\"]+/)"', html)
    dirs = [d for d in dirs if d not in ("../",) and not d.startswith("?")]
    if not dirs:
        return None
    # choose last dir alphabetically as heuristic
    folder = base + sorted(dirs)[-1]
    listing = requests.get(folder, timeout=15).text
    m = re.search(r'([A-Za-z0-9_.-]*puppy.*64.*?\.iso)', listing)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = folder + iso_name
    version = re.search(r'([0-9.]+)', iso_name)
    ver = version.group(1) if version else "latest"
    return {"name": "Puppy Linux", "version": ver, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": None, "url": folder}}

def fetch_garuda():
    # Try common latest path on Chaotic mirror
    base = "https://geo-mirror.chaotic.cx/iso/latest/garuda/dr460nized/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'(garuda-dr460nized-linux-.*?\.iso)', html)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = base + iso_name
    ver = re.search(r'([0-9]{8})', iso_name)
    version = ver.group(1) if ver else "latest"
    checksum_url = iso_url + ".sha256"
    try:
        sha256 = requests.get(checksum_url, timeout=15).text.split()[0]
    except Exception:
        sha256 = None
    return {"name": "Garuda Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_rocky():
    base = "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'(Rocky-[0-9.]+-x86_64-dvd\.iso)', html)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = base + iso_name
    checksum_url = base + "CHECKSUM"
    try:
        sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
    except Exception:
        sha256 = None
    ver = re.search(r'Rocky-([0-9.]+)-', iso_name)
    version = ver.group(1) if ver else "9"
    return {"name": "Rocky Linux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_almalinux():
    base = "https://repo.almalinux.org/almalinux/9/isos/x86_64/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'(AlmaLinux-[0-9.]+-x86_64-dvd\.iso)', html)
    if not m:
        return None
    iso_name = m.group(1)
    iso_url = base + iso_name
    checksum_url = base + "CHECKSUM"
    try:
        sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
    except Exception:
        sha256 = None
    ver = re.search(r'AlmaLinux-([0-9.]+)-', iso_name)
    version = ver.group(1) if ver else "9"
    return {"name": "AlmaLinux", "version": version, "arch": ["x86_64"], "download_url": iso_url, "checksum": {"sha256": sha256, "url": checksum_url}}

def fetch_nixos(max_versions: int = 2):
    # Find stable nixos versions and use latest GNOME ISO per version
    index = requests.get("https://releases.nixos.org/?prefix=nixos/", timeout=15).text
    versions = re.findall(r'nixos/([0-9]{2}\.[0-9]{2})/', index)
    if not versions:
        return None
    ordered = sorted(set(versions), key=lambda v: tuple(map(int, v.split('.'))))
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for version in selected:
        base = f"https://channels.nixos.org/nixos-{version}/"
        iso_url = base + "latest-nixos-gnome-x86_64-linux.iso"
        checksum_url = base
        out.append({
            "name": "NixOS",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": None, "url": checksum_url}
        })
    return out or None

def fetch_clearlinux(max_versions: int = 2):
    index = requests.get("https://cdn.download.clearlinux.org/releases/", timeout=15).text
    rels = re.findall(r'href="([0-9]+)/"', index)
    if not rels:
        return None
    ordered = sorted({int(r) for r in rels})
    selected = list(reversed(ordered))[:max_versions]
    out = []
    for rel in selected:
        base = f"https://cdn.download.clearlinux.org/releases/{rel}/clear/ISO/"
        listing = requests.get(base, timeout=15).text
        m = re.search(r'(clear-[0-9]+-live-desktop\.iso)', listing)
        if not m:
            continue
        iso_name = m.group(1)
        iso_url = base + iso_name
        checksum_url = base + "SHA512SUMS"
        out.append({
            "name": "Clear Linux",
            "version": str(rel),
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": None, "url": checksum_url}
        })
    return out or None

# ------------------ Main ------------------ #
def main():
    output = {"last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "distros": []}
    fetchers = [
        fetch_ubuntu, fetch_debian, fetch_fedora, fetch_arch, fetch_linuxmint, fetch_manjaro,
        fetch_opensuse_tumbleweed, fetch_opensuse_leap, fetch_popos, fetch_elementary,
        fetch_zorin, fetch_mxlinux, fetch_kali, fetch_cachyos,
        fetch_endeavouros, fetch_parrot, fetch_tails, fetch_qubes, fetch_puppy,
        fetch_garuda, fetch_rocky, fetch_almalinux, fetch_nixos, fetch_clearlinux
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
    # mark latest per distro name
    by_name = {}
    for idx, item in enumerate(output["distros"]):
        name = item.get("name", "")
        if not name:
            continue
        # build a sortable key from version like 24.04.1 or 2025.08.01; fallback to original order
        ver = str(item.get("version", ""))
        def parse_ver(v: str):
            parts = []
            for p in re.split(r"[^0-9]+", v):
                if p.isdigit():
                    try:
                        parts.append(int(p))
                    except Exception:
                        parts.append(0)
            return tuple(parts) if parts else (0,)
        key = (parse_ver(ver), idx)
        if name not in by_name or key > by_name[name][0]:
            by_name[name] = (key, idx)
    for name, (_key, idx) in by_name.items():
        try:
            output["distros"][idx]["latest"] = True
        except Exception:
            pass
    with open("isos/linux.json", "w") as fp:
        json.dump(output, fp, indent=2)

if __name__ == "__main__":
    main()
