# Pre-launch Checklist

Everything you need to do before running AutoRec for the first time.

---

## 1 — Clone the repo

```bash
git clone https://github.com/rion090/autorec.git
cd autorec
```

---

## 2 — Check Python version

AutoRec requires **Python 3.10 or later** (uses modern type hints).

```bash
python3 --version
```

If you're below 3.10, upgrade via your package manager or [python.org](https://python.org).

---

## 3 — Install tools for your chosen profile

AutoRec will tell you which tools are missing when you run it, but installing ahead of time is faster.

### CTF Profile tools

| Tool | Install |
|------|---------|
| amass | `apt install amass` or `go install github.com/owasp-amass/amass/v4/...@master` |
| curl | `apt install curl` (usually pre-installed) |
| waybackurls | `go install github.com/tomnomnom/waybackurls@latest` |
| nmap | `apt install nmap` |
| dirb | `apt install dirb` |
| httpx | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |

### Bug Bounty Profile tools

| Tool | Install |
|------|---------|
| amass | `apt install amass` or Go (see above) |
| gau | `go install github.com/lc/gau/v2/cmd/gau@latest` |
| waybackurls | `go install github.com/tomnomnom/waybackurls@latest` |
| httpx | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| arjun | `pip install arjun` |
| LinkFinder | `git clone https://github.com/GerbenJavado/LinkFinder.git && cd LinkFinder && pip install -r requirements.txt` |
| subfinder | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| assetfinder | `go install github.com/tomnomnom/assetfinder@latest` |
| ffuf | `go install github.com/ffuf/ffuf/v2@latest` |

> **Go tools tip:** Make sure `$(go env GOPATH)/bin` is in your `$PATH`.  
> Add this to your `~/.bashrc` or `~/.zshrc`:
> ```bash
> export PATH="$PATH:$(go env GOPATH)/bin"
> ```

---

## 4 — (Optional) Validate profiles

Make sure the JSON profiles match the expected schema before running:

```bash
pip install jsonschema
bash scripts/validate.sh
```

Both profiles should print `[✔] ... is valid`.

---

## 5 — Run AutoRec

```bash
# Interactive (recommended for first run)
python3 src/autorec.py

# Direct — CTF profile, passive phase
python3 src/autorec.py -p ctf example.com

# Direct — Bug Bounty, passive phase only
python3 src/autorec.py -p bounty example.com --phase default

# Direct — Bug Bounty, all phases (will prompt before active)
python3 src/autorec.py -p bounty example.com --phase all
```

---

## 6 — Read your results

Output files are saved in:
```
recon_<profile>_<target>_<timestamp>/
├── default/
│   ├── amass.txt
│   ├── gau.txt
│   └── ...
└── extended/          (if you ran the extended phase)
    ├── subfinder.txt
    └── ...
```

Each file starts with a header showing exactly what command was run, making it easy to reproduce or tweak later.

---

## ⚠ Ethical reminder

- **CTF:** Check the competition rules before running any active scan. Some CTFs ban nmap/dirb entirely.
- **Bug Bounty:** Only scan domains explicitly listed in the programme scope. Stay in bounds.
- **Always:** Never scan targets you don't own or have written permission to test.
