#!/usr/bin/env python3
"""
AutoRec — Bug Bounty Profile
Runs passive and (optionally) active recon tools defined in bounty.json.

Phases:
  passive  —  safe enumeration, no direct target interaction
  active   —  sends requests to the target, requires manual approval

Called by initial.py via:
  profile_module.run(target, phase, output_dir)
"""

import json
import subprocess
import shutil
import sys
import os
from datetime import datetime

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

def ok(msg):      print(f"{GREEN}[✔]{RESET} {msg}")
def warn(msg):    print(f"{YELLOW}[!]{RESET} {msg}")
def err(msg):     print(f"{RED}[✘]{RESET} {msg}")
def info(msg):    print(f"{MAGENTA}[→]{RESET} {msg}")
def section(msg): print(f"\n{BOLD}{MAGENTA}{'─'*58}\n  {msg}\n{'─'*58}{RESET}")

# ── Path anchors ──────────────────────────────────────────────────────────────
# __file__  →  repo/src/bounty.py
# _HERE     →  repo/src/
# REPO_ROOT →  repo/
_HERE     = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)

PROFILE_PATH = os.path.join(REPO_ROOT, "profiles", "bounty.json")

# ── Profile loader ────────────────────────────────────────────────────────────
def load_profile(path: str) -> dict:
    """Load bounty.json and return it as a Python dict."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        err(f"Profile not found: {path}")
        err("Make sure profiles/bounty.json exists in the repo root.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        err(f"Bad JSON in bounty.json: {e}")
        sys.exit(1)

# ── Tool checks ───────────────────────────────────────────────────────────────
def is_tool_installed(tool_name: str, verify_cmd: str) -> bool:
    """Return True if the tool exists on PATH and its verify command runs."""
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
    """Split a tool list into (ready, missing)."""
    ready, missing = [], []
    for tool in tools:
        if is_tool_installed(tool["name"], tool["verify_cmd"]):
            ready.append(tool)
        else:
            missing.append(tool)
    return ready, missing

def print_install_hints(missing_tools: list):
    """Print beginner-friendly install commands for missing tools."""
    warn("The following tools need to be installed first:\n")
    for tool in missing_tools:
        print(f"  {BOLD}{tool['name']}{RESET}")
        installs = tool.get("install", {})
        if "apt" in installs:
            print(f"    {DIM}apt  →{RESET}  {installs['apt']}")
        if "go" in installs:
            print(f"    {DIM}go   →{RESET}  {installs['go']}")
        if "pip" in installs:
            print(f"    {DIM}pip  →{RESET}  {installs['pip']}")
        if "git" in installs:
            print(f"    {DIM}git  →{RESET}  {installs['git']}")
        print()

# ── Approval gate ─────────────────────────────────────────────────────────────
def request_approval(phase_desc: str) -> bool:
    """
    Warn the user and ask for confirmation before running active tools.
    Bug bounty specific — reminds about staying in programme scope.
    """
    print()
    warn("This phase sends live requests directly to the target.")
    warn("Only run this against domains explicitly listed in the programme scope.")
    warn("Running out-of-scope scans may get you banned or face legal action.\n")
    warn(f"Phase: {phase_desc}\n")
    answer = input(f"{YELLOW}  Have you confirmed this target is in scope? [y/N]: {RESET}").strip().lower()
    return answer == "y"

# ── Command builder ───────────────────────────────────────────────────────────
def build_command(tool_name: str, flags: str, target: str) -> list[str]:
    """
    Translate a tool name + flags + target into the actual command list
    that subprocess.run() will execute.

    Each tool has its own argument pattern — extend this dict when adding tools.
    """
    flag_list = flags.split() if flags else []

    commands = {
        # ── passive phase ─────────────────────────────────────────────────────

        # amass: subdomain enumeration using passive OSINT sources only
        # -passive = no direct DNS queries to the target
        "amass":       ["amass", "enum", "-passive"] + flag_list + ["-d", target],

        # assetfinder: fast subdomain discovery via certificate transparency + APIs
        "assetfinder": ["assetfinder"] + flag_list + [target],

        # gau: pulls known URLs from Wayback Machine, OTX, CommonCrawl
        # piped via bash because gau reads from stdin
        "gau":         ["bash", "-c", f"echo {target} | gau {' '.join(flag_list)}"],

        # waybackurls: fetches archived URLs from the Wayback Machine
        # also stdin-based like gau
        "waybackurls": ["bash", "-c", f"echo {target} | waybackurls"],

        # ── active phase ──────────────────────────────────────────────────────

        # httpx: probes discovered subdomains/URLs for live hosts
        # -title grabs page title, -tech-detect fingerprints tech stack
        # -status-code shows HTTP response codes
        "httpx":       ["httpx"] + flag_list + [
                            "-u", target,
                            "-title",
                            "-tech-detect",
                            "-status-code",
                        ],

        # arjun: discovers hidden HTTP parameters on endpoints
        # useful for finding unlinked params that could be injection points
        "arjun":       ["arjun"] + flag_list + ["-u", f"https://{target}"],

        # linkfinder: extracts endpoints and paths from JavaScript files
        # -i = input URL or file, -o = output format (cli = print to terminal)
        "linkfinder":  ["python3",
                            os.path.join(_HERE, "LinkFinder", "linkfinder.py"),
                            "-i", f"https://{target}",
                            "-o", "cli"] + flag_list,

        # ffuf: fast web fuzzer for directory and file discovery
        # FUZZ is the placeholder that gets replaced with wordlist entries
        "ffuf":        ["ffuf"] + flag_list + [
                            "-u", f"https://{target}/FUZZ",
                            "-w", "/usr/share/wordlists/dirb/common.txt",
                            "-mc", "200,301,302,403",   # only show these status codes
                            "-t", "50",                  # 50 threads
                        ],
    }

    # fallback: tool + flags + target for anything not listed above
    return commands.get(tool_name, [tool_name] + flag_list + [target])

# ── Human-readable tool labels ────────────────────────────────────────────────
FRIENDLY_LABELS = {
    "amass":       "Subdomain discovery          (passive OSINT)",
    "assetfinder": "Asset & subdomain finder",
    "gau":         "Known URL harvester          (Wayback, OTX, CommonCrawl)",
    "waybackurls": "Archived URL fetcher         (Wayback Machine)",
    "httpx":       "Live host probe + tech fingerprint",
    "arjun":       "Hidden HTTP parameter finder",
    "linkfinder":  "JavaScript endpoint extractor",
    "ffuf":        "Directory & file fuzzer",
}

# ── Single tool runner ────────────────────────────────────────────────────────
def run_tool(tool: dict, target: str, output_dir: str) -> None:
    """
    Execute one tool, show a 15-line preview in the terminal,
    and save the full output to a .txt file.
    """
    label    = FRIENDLY_LABELS.get(tool["name"], tool["name"])
    info(f"Running  →  {BOLD}{label}{RESET}  {DIM}({tool['name']}){RESET}")

    cmd      = build_command(tool["name"], tool.get("flags", ""), target)
    out_file = os.path.join(output_dir, f"{tool['name']}.txt")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,            # bounty tools can be slower — 5 min limit
        )
        output = result.stdout.strip() or result.stderr.strip()

        # ── Save full output ──────────────────────────────────────────────────
        with open(out_file, "w") as f:
            f.write(f"# tool    : {tool['name']}\n")
            f.write(f"# target  : {target}\n")
            f.write(f"# command : {' '.join(cmd)}\n\n")
            f.write(output)

        # ── Print preview (first 15 lines) ───────────────────────────────────
        if output:
            lines   = output.splitlines()
            preview = "\n".join(f"    {line}" for line in lines[:15])
            print(preview)
            if len(lines) > 15:
                print(f"    {YELLOW}… {len(lines) - 15} more lines → {out_file}{RESET}")
        else:
            warn(f"No output from {tool['name']}")

        ok(f"Saved  →  {out_file}\n")

    except subprocess.TimeoutExpired:
        err(f"{tool['name']} timed out (>300 s). Try running it manually.")
    except FileNotFoundError:
        err(f"{tool['name']} binary not found. Check your PATH.")
    except Exception as e:
        err(f"{tool['name']} failed: {e}")

# ── Phase runner ──────────────────────────────────────────────────────────────
def run_phase(phase_name: str, phase_data: dict, target: str, output_dir: str) -> None:
    """
    For one phase:
      1. check which tools are installed
      2. warn about + skip missing ones
      3. ask for approval if the phase is active
      4. run each available tool
    """
    section(f"Phase: {phase_name.upper()}  —  {phase_data['description']}")

    ready, missing = check_tools(phase_data["tools"])

    if missing:
        print_install_hints(missing)
        if not ready:
            err("No tools available for this phase. Skipping.\n")
            return
        warn(f"Skipping {len(missing)} missing tool(s), running {len(ready)} available.\n")

    # active phase gate — ask before sending any traffic
    if phase_data.get("requires_manual_approval", False):
        if not request_approval(phase_data["description"]):
            warn("Phase skipped by user.\n")
            return

    # create a subfolder per phase so passive/ and active/ stay separate
    phase_out = os.path.join(output_dir, phase_name)
    os.makedirs(phase_out, exist_ok=True)

    for tool in ready:
        run_tool(tool, target, phase_out)

# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(output_dir: str) -> None:
    """List every saved file with its size after all phases finish."""
    section("Recon complete — saved files")
    for root, _, files in os.walk(output_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            size  = os.path.getsize(fpath)
            rel   = os.path.relpath(fpath, output_dir)
            print(f"  {GREEN}{rel:<50}{RESET}  {DIM}{size} bytes{RESET}")
    print(f"\n{BOLD}Output directory:{RESET}  {output_dir}\n")

# ── Entry point (called by initial.py) ───────────────────────────────────────
def run(target: str, phase: str, output_dir: str) -> None:
    """
    Public entry point — initial.py calls this as:
        profile_module.run(target=target, phase=args.phase, output_dir=output_dir)

    Loads bounty.json, resolves which phases to run, and hands each
    phase off to run_phase().
    """
    profile = load_profile(PROFILE_PATH)
    phases  = profile["phases"]

    # ── Print a profile header ────────────────────────────────────────────────
    print(f"\n{BOLD}{'═'*58}")
    print(f"  Profile  :  {MAGENTA}Bug Bounty Hunter{RESET}{BOLD}")
    print(f"  Target   :  {target}")
    print(f"  Phase    :  {phase}")
    print(f"  Output   :  {output_dir}")
    print(f"{'═'*58}{RESET}\n")

    # ── Resolve which phases to run ───────────────────────────────────────────
    if phase == "all":
        # run every phase defined in bounty.json in order
        phases_to_run = list(phases.keys())

    elif phase == "default":
        # "default" means the user didn't pick a phase explicitly
        # → run only the first phase (passive) so active is never surprise-triggered
        phases_to_run = [list(phases.keys())[0]]

    else:
        # user asked for a specific phase by name e.g. --phase active
        if phase not in phases:
            err(f"Phase '{phase}' not found in the bounty profile.")
            err(f"Available phases: {', '.join(phases.keys())}")
            sys.exit(1)
        phases_to_run = [phase]

    # ── Run ───────────────────────────────────────────────────────────────────
    for phase_name in phases_to_run:
        run_phase(phase_name, phases[phase_name], target, output_dir)

    print_summary(output_dir)


# ── Standalone mode (optional — lets you run bounty.py directly for testing) ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoRec — Bug Bounty Profile")
    parser.add_argument("target", help="Domain to recon (e.g. example.com)")
    parser.add_argument(
        "--phase",
        choices=["passive", "active", "all", "default"],
        default="default",
        help="Phase to run (default: passive only)",
    )
    parser.add_argument("--output", default=None,
                        help="Output directory (auto-generated if omitted)")

    args       = parser.parse_args()
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output or os.path.join(
        REPO_ROOT, "output", f"bounty_{args.target}_{timestamp}"
    )
    os.makedirs(output_dir, exist_ok=True)

    run(target=args.target, phase=args.phase, output_dir=output_dir)
