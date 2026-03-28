#!/usr/bin/env python3
"""
AutoRec — Automated Recon Launcher
Unified entry point for CTF and Bug Bounty recon profiles.

Usage:
  python autorec.py                        # interactive profile selector
  python autorec.py -p ctf example.com
  python autorec.py -p bounty example.com --phase all
"""

import json
import subprocess
import shutil
import sys
import os
import argparse
from datetime import datetime

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):     print(f"{GREEN}[✔]{RESET} {msg}")
def warn(msg):   print(f"{YELLOW}[!]{RESET} {msg}")
def err(msg):    print(f"{RED}[✘]{RESET} {msg}")
def info(msg):   print(f"{CYAN}[→]{RESET} {msg}")
def section(msg):print(f"\n{BOLD}{CYAN}{'─'*58}\n  {msg}\n{'─'*58}{RESET}")

# ── ASCII banner (figlet-style, hand-drawn block letters) ─────────────────────
BANNER = f"""{BOLD}{CYAN}
   ██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ███████╗ ██████╗
  ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝██╔════╝
  ███████║██║   ██║   ██║   ██║   ██║██████╔╝█████╗  ██║     
  ██╔══██║██║   ██║   ██║   ██║   ██║██╔══██╗██╔══╝  ██║     
  ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║  ██║███████╗╚██████╗
  ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝
{RESET}{DIM}  Automated Reconnaissance V.0.1{RESET}
"""

# ── Path anchors ──────────────────────────────────────────────────────────────
# __file__  →  repo/src/initial.py
# _HERE     →  repo/src/
# REPO_ROOT →  repo/
_HERE     = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)

# ── Disclaimer + tool list (printed once after banner) ────────────────────────
DISCLAIMER = f"""{YELLOW}  ⚠  Disclaimer{RESET}
  Use this tool only against targets you have explicit permission to test.
  CTF players  : read the competition rules before running any active scans.
  Bounty hunters: stay strictly within the defined programme scope.
  Unauthorised scanning may be illegal. You are responsible for your actions.

{DIM}  --- Tools included -------------------------------------------------------{RESET}
  {CYAN}{BOLD}CTF   {RESET}  amass · curl · waybackurls · nmap · dirb · httpx
  {MAGENTA}{BOLD}Bounty{RESET}  amass · gau · waybackurls · httpx · arjun · linkfinder · assetfinder · ffuf
{DIM}  --------------------------------------------------------------------------{RESET}
"""

# ── Profile registry ──────────────────────────────────────────────────────────
PROFILES = {
    "1": {
        "key":    "ctf",
        "label":  "CTF Player",
        "desc":   "Passive-first recon. Light probing with manual approval.",
        "path":   os.path.join(REPO_ROOT, "profiles", "ctf.json"),
        "module": "ctf",
        "tools":  ["amass", "curl", "waybackurls", "nmap", "dirb", "httpx"],
        "phases": ["default", "probing"],
        "color":  CYAN,
    },
    "2": {
        "key":    "bounty",
        "label":  "Bug Bounty Hunter",
        "desc":   "Broader recon — subdomains, endpoints, headers, JS links.",
        "path":   os.path.join(REPO_ROOT, "profiles", "bounty.json"),
        "module": "bounty",
        "tools":  ["amass", "gau", "waybackurls", "httpx", "arjun",
                   "linkfinder", "assetfinder", "ffuf"],
        "phases": ["passive", "active"],
        "color":  MAGENTA,
    },
}

# ── Profile selector (interactive) ───────────────────────────────────────────
def select_profile() -> dict:
    """Print a numbered menu and return the chosen profile dict."""
    print(f"\n{BOLD}  Select a recon profile:{RESET}\n")
    for num, p in PROFILES.items():
        tools_str = "  ·  ".join(p["tools"])
        print(f"  {p['color']}{BOLD}[{num}]{RESET}  {BOLD}{p['label']}{RESET}")
        print(f"       {DIM}{p['desc']}{RESET}")
        print(f"       {DIM}tools → {tools_str}{RESET}\n")

    while True:
        choice = input(f"{CYAN}  Enter profile number: {RESET}").strip()
        if choice in PROFILES:
            return PROFILES[choice]
        err(f"Invalid choice '{choice}'. Enter 1 or 2.")

# ── Profile loader ────────────────────────────────────────────────────────────
def load_profile(path: str) -> dict:
    """Load and return a JSON profile. Exits on error."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        err(f"Profile file not found: {path}")
        err("Make sure profiles/ctf.json and profiles/bounty.json exist.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        err(f"Bad JSON in profile: {e}")
        sys.exit(1)

# ── Tool checks ───────────────────────────────────────────────────────────────
def is_tool_installed(tool_name: str, verify_cmd: str) -> bool:
    """Return True if the tool is on PATH and its verify command runs."""
    if not shutil.which(tool_name):
        return False
    try:
        subprocess.run(
            verify_cmd.split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return True
    except Exception:
        return False

def check_tools(tools: list) -> tuple[list, list]:
    """Split tool list into (ready, missing)."""
    ready, missing = [], []
    for tool in tools:
        if is_tool_installed(tool["name"], tool["verify_cmd"]):
            ready.append(tool)
        else:
            missing.append(tool)
    return ready, missing

def print_install_hints(missing_tools: list):
    """Print beginner-friendly install instructions for missing tools."""
    warn("The following tools need to be installed first:\n")
    for tool in missing_tools:
        print(f"  {BOLD}{tool['name']}{RESET}")
        installs = tool.get("install", {})
        if "apt" in installs:
            print(f"    {DIM}apt  →{RESET}  {installs['apt']}")
        if "go" in installs:
            print(f"    {DIM}go   →{RESET}  {installs['go']}")
        print()

# ── Approval gate (active phases) ─────────────────────────────────────────────
def request_approval(profile_key: str, phase_desc: str) -> bool:
    """Warn the user and ask for explicit confirmation before active scanning."""
    print()
    warn("This phase sends traffic to the target (active scanning).")
    if profile_key == "ctf":
        warn("Many CTFs forbid active scanning — read the rules before continuing!")
    elif profile_key == "bounty":
        warn("Only run this against targets explicitly listed in the program scope.")
    warn(f"Phase description: {phase_desc}\n")
    answer = input(f"{YELLOW}  Continue? [y/N]: {RESET}").strip().lower()
    return answer == "y"

# ── Command builder ───────────────────────────────────────────────────────────
# Maps tool name → how to call it with a target.
# Add new tools here as the project grows.
def build_command(tool_name: str, flags: str, target: str) -> list[str]:
    flag_list = flags.split() if flags else []

    commands = {
        # ── passive / CTF default ─────────────────────────────────────────────
        "amass":          ["amass", "enum"] + flag_list + ["-d", target],
        "curl":           ["curl", "-sI"] + flag_list + [f"https://{target}"],
        "waybackurls":    ["bash", "-c", f"echo {target} | waybackurls"],

        # ── probing / CTF active ──────────────────────────────────────────────
        "nmap":           ["nmap"] + flag_list + [target],
        "dirb":           ["dirb", f"http://{target}"] + flag_list,
        "httpx":          ["httpx"] + flag_list + ["-u", target],

        # ── bounty passive ────────────────────────────────────────────────────
        "subfinder":      ["subfinder"] + flag_list + ["-d", target],
        "assetfinder":    ["assetfinder"] + flag_list + [target],
        "gau":            ["bash", "-c", f"echo {target} | gau"],
        "whatweb":        ["whatweb"] + flag_list + [target],

        # ── bounty active ─────────────────────────────────────────────────────
        "nuclei":         ["nuclei"] + flag_list + ["-u", f"https://{target}"],
        "ffuf":           ["ffuf"] + flag_list + ["-u", f"https://{target}/FUZZ",
                                                   "-w", "/usr/share/wordlists/dirb/common.txt"],
        "katana":         ["katana"] + flag_list + ["-u", f"https://{target}"],
    }

    return commands.get(tool_name, [tool_name] + flag_list + [target])

# ── Human-readable tool labels ────────────────────────────────────────────────
FRIENDLY_LABELS = {
    "amass":       "Subdomain discovery",
    "curl":        "HTTP header grab",
    "waybackurls": "Archived URLs  (Wayback Machine)",
    "nmap":        "Open port scan",
    "dirb":        "Directory brute-force",
    "httpx":       "Live host + tech fingerprint",
    "subfinder":   "Subdomain enumeration",
    "assetfinder": "Asset / subdomain finder",
    "gau":         "Fetches known URLs  (GAU)",
    "whatweb":     "Tech stack fingerprint",
    "nuclei":      "Vulnerability templates scan",
    "ffuf":        "Fast web fuzzer",
    "katana":      "Web crawler",
}

# ── Single tool runner ────────────────────────────────────────────────────────
def run_tool(tool: dict, target: str, output_dir: str) -> None:
    """Execute one tool, preview output, and save full results to disk."""
    label = FRIENDLY_LABELS.get(tool["name"], tool["name"])
    info(f"Running  →  {BOLD}{label}{RESET}  {DIM}({tool['name']}){RESET}")

    cmd      = build_command(tool["name"], tool.get("flags", ""), target)
    out_file = os.path.join(output_dir, f"{tool['name']}.txt")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        output = result.stdout.strip() or result.stderr.strip()

        with open(out_file, "w") as f:
            f.write(f"# tool    : {tool['name']}\n")
            f.write(f"# target  : {target}\n")
            f.write(f"# command : {' '.join(cmd)}\n\n")
            f.write(output)

        if output:
            lines   = output.splitlines()
            preview = "\n".join(f"    {l}" for l in lines[:15])
            print(preview)
            if len(lines) > 15:
                print(f"    {YELLOW}… {len(lines) - 15} more lines → {out_file}{RESET}")
        else:
            warn(f"No output from {tool['name']}")

        ok(f"Saved  →  {out_file}\n")

    except subprocess.TimeoutExpired:
        err(f"{tool['name']} timed out (>180 s). Run it manually if needed.")
    except FileNotFoundError:
        err(f"{tool['name']} binary not found. Check your PATH.")
    except Exception as e:
        err(f"{tool['name']} failed: {e}")

# ── Phase runner ──────────────────────────────────────────────────────────────
def run_phase(profile_key: str, phase_name: str, phase_data: dict,
              target: str, output_dir: str) -> None:
    """Preflight-check tools, gate active phases, then run everything."""
    section(f"Phase: {phase_name.upper()}  —  {phase_data['description']}")

    ready, missing = check_tools(phase_data["tools"])

    if missing:
        print_install_hints(missing)
        if not ready:
            err("No tools available for this phase. Skipping.\n")
            return
        warn(f"Skipping {len(missing)} missing tool(s), running {len(ready)} available.\n")

    if phase_data.get("requires_manual_approval", False):
        if not request_approval(profile_key, phase_data["description"]):
            warn("Phase skipped by user.\n")
            return

    phase_out = os.path.join(output_dir, phase_name)
    os.makedirs(phase_out, exist_ok=True)

    for tool in ready:
        run_tool(tool, target, phase_out)

# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(output_dir: str) -> None:
    section("Recon complete — saved files")
    for root, _, files in os.walk(output_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            size  = os.path.getsize(fpath)
            rel   = os.path.relpath(fpath, output_dir)
            print(f"  {GREEN}{rel:<45}{RESET}  {DIM}{size} bytes{RESET}")
    print(f"\n{BOLD}Output directory:{RESET}  {output_dir}\n")

# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    # ── Always print the banner + disclaimer first ────────────────────────────
    print(BANNER)
    print(DISCLAIMER)

    # ── CLI argument parsing ──────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="autorec",
        description="AutoRec — one-command recon launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Profiles:
  1  ctf     — passive recon + optional light probing
  2  bounty  — subdomain enum, crawling, vuln templates

Examples:
  python autorec.py                              # interactive selector
  python autorec.py -p ctf example.com
  python autorec.py -p bounty example.com --phase passive
  python autorec.py -p bounty example.com --phase all
        """,
    )
    parser.add_argument(
        "target", nargs="?", default=None,
        help="Domain or IP to scan (e.g. example.com). Prompted if omitted.",
    )
    parser.add_argument(
        "-p", "--profile", choices=["ctf", "bounty"], default=None,
        help="Profile to use. Prompted if omitted.",
    )
    parser.add_argument(
        "--phase", default="default",
        help="Phase to run: 'default', 'passive', 'probing', 'active', or 'all'.",
    )
    parser.add_argument(
        "--output", default=None,
        help="Custom output directory (default: recon_<target>_<timestamp>).",
    )

    args = parser.parse_args()

    # ── Resolve profile (CLI flag → menu → exit) ──────────────────────────────
    if args.profile:
        meta = next((p for p in PROFILES.values() if p["key"] == args.profile), None)
        if meta is None:
            err(f"Unknown profile '{args.profile}'.")
            sys.exit(1)
    else:
        meta = select_profile()

    # ── Import the profile module (src/ctf.py or src/bounty.py) ──────────────
    # Both files live in the same folder as this script (src/)
    import importlib
    try:
        profile_module = importlib.import_module(meta["module"])
    except ModuleNotFoundError:
        err(f"Profile module '{meta['module']}.py' not found in src/.")
        err(f"Expected location: {os.path.join(_HERE, meta['module'] + '.py')}")
        sys.exit(1)

    # ── Resolve target ────────────────────────────────────────────────────────
    target = args.target
    if not target:
        target = input(f"\n{CYAN}  Enter target domain or IP: {RESET}").strip()
    if not target:
        err("No target provided. Exiting.")
        sys.exit(1)

    # ── Output directory ──────────────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output or os.path.join(
        _HERE, "output", f"{meta['key']}_{target}_{timestamp}"
    )
    os.makedirs(output_dir, exist_ok=True)

    # ── Run header ────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'═'*58}")
    print(f"  Profile  :  {meta['color']}{meta['label']}{RESET}{BOLD}")
    print(f"  Target   :  {target}")
    print(f"  Phase    :  {args.phase}")
    print(f"  Output   :  {output_dir}")
    print(f"{'═'*58}{RESET}\n")

    # ── Hand off to the profile module ───────────────────────────────────────
    # Each profile module (ctf.py / bounty.py) exposes a run(target, phase, output_dir)
    profile_module.run(target=target, phase=args.phase, output_dir=output_dir)


if __name__ == "__main__":
    main() 
