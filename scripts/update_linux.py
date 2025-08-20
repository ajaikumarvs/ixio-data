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

def fetch_linuxmint(max_versions: int = 3):
    """Fetch Linux Mint Cinnamon editions"""
    try:
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
                "name": "Linux Mint",
                "version": version,
                "arch": ["x86_64"],
                "download_url": iso_url,
                "checksum": {"sha256": sha256, "url": checksum_url}
            })
        return out or None
    except Exception as e:
        print(f"Error fetching Linux Mint: {e}")
        return None

def fetch_zorin(max_versions: int = 2):
    """Fetch Zorin OS Core editions"""
    try:
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
    except Exception as e:
        print(f"Error fetching Zorin OS: {e}")
        return None

def fetch_elementary():
    """Fetch elementary OS"""
    try:
        base_url = "https://mirror.elementary.io/iso/"
        html = requests.get(base_url, timeout=15).text
        match = re.search(r'(elementaryos-[0-9.]+-stable\.iso)', html)
        if not match: 
            return None
        iso_name = match.group(1)
        iso_url = base_url + iso_name
        checksum_url = base_url + "SHA256SUMS"
        try:
            sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
        except Exception:
            sha256 = None
        version = re.search(r'elementaryos-([0-9.]+)-', iso_name).group(1)
        return {
            "name": "elementary OS",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        }
    except Exception as e:
        print(f"Error fetching elementary OS: {e}")
        return None

def fetch_manjaro(max_versions: int = 2):
    """Fetch Manjaro KDE editions"""
    try:
        base_url = "https://download.manjaro.org/kde/"
        html = requests.get(base_url, timeout=15).text
        matches = re.findall(r"(manjaro-kde-([0-9.]+)-[^\s\"']*-x86_64\.iso)", html)
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
            checksum_url = iso_url + ".sha256"
            try:
                sha256 = requests.get(checksum_url, timeout=15).text.split()[0]
            except Exception:
                sha256 = None
            out.append({
                "name": "Manjaro",
                "version": ver,
                "arch": ["x86_64"],
                "download_url": iso_url,
                "checksum": {"sha256": sha256, "url": checksum_url}
            })
        return out or None
    except Exception as e:
        print(f"Error fetching Manjaro: {e}")
        return None

def fetch_endeavouros():
    """Fetch EndeavourOS from GitHub releases"""
    try:
        url = "https://github.com/endeavouros-team/ISO/releases/latest"
        headers = {"User-Agent": "Mozilla/5.0 (Linux; x86_64) ixio-bot"}
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        html = response.text
        
        # Find ISO download link
        iso_match = re.search(r'href="([^"]*EndeavourOS[^"]*\.iso)"', html)
        if not iso_match:
            return None
        
        href = iso_match.group(1)
        if href.startswith("/"):
            iso_url = "https://github.com" + href
        else:
            iso_url = href
            
        iso_name = iso_url.split("/")[-1]
        ver_match = re.search(r"(\d{4}\.\d{2}|\d+\.\d+)", iso_name)
        version = ver_match.group(1) if ver_match else "latest"
        
        return {
            "name": "EndeavourOS",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": None, "url": url}
        }
    except Exception as e:
        print(f"Error fetching EndeavourOS: {e}")
        return None

def fetch_opensuse_leap(max_versions: int = 2):
    """Fetch openSUSE Leap"""
    try:
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
    except Exception as e:
        print(f"Error fetching openSUSE Leap: {e}")
        return None

def fetch_opensuse_tumbleweed():
    """Fetch openSUSE Tumbleweed"""
    try:
        base_url = "https://download.opensuse.org/tumbleweed/iso/"
        html = requests.get(base_url, timeout=15).text
        match = re.search(r'(openSUSE-Tumbleweed-DVD-x86_64-[0-9]+\.iso)', html)
        if not match: 
            return None
        iso_name = match.group(1)
        iso_url = base_url + iso_name
        checksum_url = iso_url + ".sha256"
        try:
            sha256 = requests.get(checksum_url, timeout=15).text.split()[0]
        except Exception:
            sha256 = None
        version = re.search(r'([0-9]+)\.iso', iso_name).group(1)
        return {
            "name": "openSUSE Tumbleweed",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        }
    except Exception as e:
        print(f"Error fetching openSUSE Tumbleweed: {e}")
        return None

def fetch_kali():
    """Fetch Kali Linux"""
    try:
        base_url = "https://cdimage.kali.org/kali-rolling/"
        html = requests.get(base_url, timeout=15).text
        match = re.search(r'(kali-linux-[0-9.]+-live-amd64\.iso)', html)
        if not match: 
            return None
        iso_name = match.group(1)
        iso_url = base_url + iso_name
        checksum_url = base_url + "SHA256SUMS"
        try:
            sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
        except Exception:
            sha256 = None
        version = re.search(r'kali-linux-([0-9.]+)-', iso_name).group(1)
        return {
            "name": "Kali Linux",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        }
    except Exception as e:
        print(f"Error fetching Kali Linux: {e}")
        return None

def fetch_parrot():
    """Fetch Parrot Security OS"""
    try:
        base = "https://mirror.parrot.sh/parrot/iso/rolling/"
        html = requests.get(base, timeout=15).text
        m = re.search(r'(Parrot-home-rolling-.*?_amd64\.iso)', html)
        if not m:
            return None
        iso_name = m.group(1)
        iso_url = base + iso_name
        checksum_url = base + "SHA256SUMS"
        try:
            sha256 = get_sha256_from_text(requests.get(checksum_url, timeout=15).text, iso_name)
        except Exception:
            sha256 = None
        ver = re.search(r'Parrot-home-rolling-([0-9.]+)-', iso_name)
        version = ver.group(1) if ver else "rolling"
        return {
            "name": "Parrot Security OS",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        }
    except Exception as e:
        print(f"Error fetching Parrot Security OS: {e}")
        return None

def fetch_tails(max_versions: int = 2):
    """Fetch Tails"""
    try:
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
    except Exception as e:
        print(f"Error fetching Tails: {e}")
        return None

def fetch_puppy():
    """Fetch Puppy Linux"""
    try:
        base = "https://distro.ibiblio.org/puppylinux/puppy64/"
        html = requests.get(base, timeout=15).text
        dirs = re.findall(r'href="([^\"]+/)"', html)
        dirs = [d for d in dirs if d not in ("../",) and not d.startswith("?")]
        if not dirs:
            return None
        # choose last dir alphabetically as heuristic for latest
        folder = base + sorted(dirs)[-1]
        listing = requests.get(folder, timeout=15).text
        m = re.search(r'([A-Za-z0-9_.-]*puppy.*64.*?\.iso)', listing)
        if not m:
            return None
        iso_name = m.group(1)
        iso_url = folder + iso_name
        version = re.search(r'([0-9.]+)', iso_name)
        ver = version.group(1) if version else "latest"
        return {
            "name": "Puppy Linux",
            "version": ver,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": None, "url": folder}
        }
    except Exception as e:
        print(f"Error fetching Puppy Linux: {e}")
        return None

def fetch_popos(max_versions: int = 2):
    """Fetch Pop!_OS"""
    try:
        base_url = "https://pop-iso.sfo2.cdn.digitaloceanspaces.com/"
        html = requests.get(base_url, timeout=15).text
        matches = re.findall(r"(pop-os_([0-9.]+)_amd64_intel_[^\s\"']*\.iso)", html)
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
    except Exception as e:
        print(f"Error fetching Pop!_OS: {e}")
        return None

def fetch_garuda():
    """Fetch Garuda Linux"""
    try:
        # Try official mirror first
        base = "https://geo-mirror.chaotic.cx/iso/latest/garuda/dr460nized/"
        html = requests.get(base, timeout=15).text
        m = re.search(r'(garuda-dr460nized-.*?\.iso)', html)
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
        return {
            "name": "Garuda Linux",
            "version": version,
            "arch": ["x86_64"],
            "download_url": iso_url,
            "checksum": {"sha256": sha256, "url": checksum_url}
        }
    except Exception as e:
        print(f"Error fetching Garuda Linux: {e}")
        return None

def fetch_nixos(max_versions: int = 2):
    """Fetch NixOS stable releases"""
    try:
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
    except Exception as e:
        print(f"Error fetching NixOS: {e}")
        return None

def fetch_clearlinux(max_versions: int = 2):
    """Fetch Clear Linux"""
    try:
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
    except Exception as e:
        print(f"Error fetching Clear Linux: {e}")
        return None

# ------------------ Main ------------------ #
def main():
    """Main function to fetch all distributions"""
    output = {
        "last_updated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", 
        "distros": []
    }
    
    # Define fetchers for the requested distributions
    fetchers = [
        fetch_linuxmint,
        fetch_zorin,
        fetch_elementary,
        fetch_manjaro,
        fetch_endeavouros,
        fetch_opensuse_leap,
        fetch_opensuse_tumbleweed,
        fetch_kali,
        fetch_parrot,
        fetch_tails,
        fetch_puppy,
        fetch_popos,
        fetch_garuda,
        fetch_nixos,
        fetch_clearlinux
    ]
    
    for f in fetchers:
        try:
            print(f"Fetching {f.__name__}...")
            data = f()
            if not data:
                print(f"No data returned for {f.__name__}")
                continue
            if isinstance(data, list):
                output["distros"].extend(data)
            else:
                output["distros"].append(data)
            print(f"Successfully fetched {f.__name__}")
        except Exception as e:
            print(f"Error fetching {f.__name__}: {e}")
    
    # Mark latest per distro name
    by_name = {}
    for idx, item in enumerate(output["distros"]):
        name = item.get("name", "")
        if not name:
            continue
        
        # Build a sortable key from version
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
    
    # Mark latest versions
    for name, (_key, idx) in by_name.items():
        try:
            output["distros"][idx]["latest"] = True
        except Exception:
            pass
    
    # Save to file
    import os
    os.makedirs("isos", exist_ok=True)
    with open("isos/linux.json", "w") as fp:
        json.dump(output, fp, indent=2)
    
    print(f"\nSuccessfully processed {len(output['distros'])} distributions")
    print("Output saved to isos/linux.json")

if __name__ == "__main__":
    main()
