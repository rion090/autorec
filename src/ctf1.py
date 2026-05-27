#!/usr/bin/env python3
"""
AutoRec — CTF Profile
Runs passive and (optionally) active recon tools defined in ctf.json.

Phases:
  default  —  passive recon, safe for all CTFs, no approval needed
  probing  —  light active scanning, requires manual approval

Called by initial.py via:
  profile_module.run(target=target, phase=args.phase, output_dir=output_dir)
"""

import json
import subprocess
import shutil
import sys
import os
import argparse
from datetime import datetime

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):     print(f"{GREEN}[✔]{RESET} {msg}")
def warn(msg):   print(f"{YELLOW}[!]{RESET} {msg}")
def err(msg):    print(f"{RED}[✘]{RESET} {msg}")
def info(msg):   print(f"{CYAN}[→]{RESET} {msg}")
def section(msg):print(f"\n{BOLD}{CYAN}{'─'*58}\n  {msg}\n{'─'*58}{RESET}")

# ── Path anchors ──────────────────────────────────────────────────────────────
# __file__  →  repo/src/ctf.py
# _HERE     →  repo/src/
# REPO_ROOT →  repo/
_HERE     = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)

PROFILE_PATH = os.path.join(REPO_ROOT, "profiles", "ctf.json")

# ── Profile loader ────────────────────────────────────────────────────────────
def load_profile(path: str) -> dict:
    """Load ctf.json and return it as a Python dict."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        err(f"Profile not found at: {path}")
        err("Make sure profiles/ctf.json exists in the repo root.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        err(f"Bad JSON in ctf.json: {e}")
        sys.exit(1)

# ── Tool checks ───────────────────────────────────────────────────────────────
def is_tool_installed(tool_name: str, verify_cmd: str) -> bool:
    """Return True if the tool exists on PATH and verify_cmd runs cleanly."""
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
    """Split tools into (ready, missing) lists."""
    ready, missing = [], []
    for tool in tools:
        if is_tool_installed(tool["name"], tool["verify_cmd"]):
            ready.append(tool)
        else:
            missing.append(tool)
    return ready, missing

def print_install_hints(missing_tools: list):
    """Print beginner-friendly install instructions for missing tools."""
    warn("The following tools are not installed:\n")
    for tool in missing_tools:
        print(f"  {BOLD}{tool['name']}{RESET}")
        installs = tool.get("install", {})
        if "apt" in installs:
            print(f"    {DIM}apt  →{RESET}  {installs['apt']}")
        if "go" in installs:
            print(f"    {DIM}go   →{RESET}  {installs['go']}")
        print()

# ── Manual approval gate ──────────────────────────────────────────────────────
def request_approval(phase_desc: str) -> bool:
    """Ask the user to confirm before running an active phase."""
    print()
    warn("This phase does ACTIVE probing (sends packets to the target).")
    warn(f"Phase: {phase_desc}")
    warn("Some CTFs forbid active scanning — check the rules first!\n")
    answer = input(f"{YELLOW}  Do you want to continue? [y/N]: {RESET}").strip().lower()
    return answer == "y"

# ── Command builder ───────────────────────────────────────────────────────────
def build_command(tool_name: str, flags: str, target: str) -> list[str]:
    """
    Translate tool name + flags + target into the command list
    that subprocess.run() will execute.

    Each tool needs its own pattern because they all take arguments differently.
    Extend this dict when adding new tools.
    """
    flag_list = flags.split() if flags else []

    commands = {
        # ── default phase (passive) ───────────────────────────────────────────

        # FIX: "-passive" and "-d" must be separate list items, not one string.
        # Before (broken): ["-passive -d", target]  ← subprocess sees this as
        #                   one argument with a space, amass rejects it
        # After  (correct): ["-passive", "-d", target] ← three clean arguments
        "amass":       ["amass", "enum"] + flag_list + ["-passive", "-d", target],

        # curl: grabs HTTP headers only (-sI = silent + head request)
        "curl":        ["curl", "-sI"] + flag_list + [f"https://{target}"],

        # waybackurls: reads target from stdin, piped via bash
        "waybackurls": ["bash", "-c", f"echo {target} | waybackurls"],

        # ── probing phase (active) ────────────────────────────────────────────

        # nmap: port scanner — flags from ctf.json e.g. "-T2"
        "nmap":        ["nmap"] + flag_list + [target],

        # dirb: directory brute-force — target goes first, flags after
        "dirb":        ["dirb", f"http://{target}"] + flag_list,

        # httpx: live host probe — -u flag needed before the target
        "httpx":       ["httpx"] + flag_list + ["-u", target],
    }

    # fallback for any tool not listed above
    if tool_name not in commands:
        return [tool_name] + flag_list + [target]

    return commands[tool_name]

# ── Human-readable tool labels ────────────────────────────────────────────────
FRIENDLY_LABELS = {
    "amass":       "Subdomain discovery          (passive OSINT)",
    "curl":        "HTTP header grab",
    "waybackurls": "Archived URL fetcher         (Wayback Machine)",
    "nmap":        "Open port scan",
    "dirb":        "Directory brute-force",
    "httpx":       "Live host / tech fingerprint",
}

# ── Single tool runner ────────────────────────────────────────────────────────
def run_tool(tool: dict, target: str, output_dir: str) -> None:
    """Execute one tool, show a 15-line preview, and save full output to disk."""
    label = FRIENDLY_LABELS.get(tool["name"], tool["name"])
    info(f"Running  →  {BOLD}{label}{RESET}  {DIM}({tool['name']}){RESET}")

    cmd      = build_command(tool["name"], tool.get("flags", ""), target)
    out_file = os.path.join(output_dir, f"{tool['name']}.txt")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip() or result.stderr.strip()

        # ── Save full output to file ──────────────────────────────────────────
        with open(out_file, "w") as f:
            f.write(f"# tool    : {tool['name']}\n")
            f.write(f"# target  : {target}\n")
            f.write(f"# command : {' '.join(cmd)}\n\n")
            f.write(output)

        # ── Print 15-line preview in terminal ─────────────────────────────────
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
        err(f"{tool['name']} timed out (>120 s). Try running it manually.")
    except FileNotFoundError:
        err(f"{tool['name']} binary not found. Install it first.")
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

    tools          = phase_data["tools"]
    ready, missing = check_tools(tools)

    if missing:
        print_install_hints(missing)
        if not ready:
            err("No tools available for this phase. Skipping.\n")
            return
        warn(f"Skipping {len(missing)} missing tool(s), running {len(ready)} available.\n")

    if phase_data.get("requires_manual_approval", False):
        if not request_approval(phase_data["description"]):
            warn("Skipped by user.\n")
            return

    # separate subfolder per phase so default/ and probing/ don't mix
    phase_out = os.path.join(output_dir, phase_name)
    os.makedirs(phase_out, exist_ok=True)

    for tool in ready:
        run_tool(tool, target, phase_out)

# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(output_dir: str) -> None:
    """List every saved file with its size after all phases finish."""
    section("Recon Complete — Output Summary")
    for root, _, files in os.walk(output_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            size  = os.path.getsize(fpath)
            rel   = os.path.relpath(fpath, output_dir)
            print(f"  {GREEN}{rel:<50}{RESET}  {DIM}({size} bytes){RESET}")
    print(f"\n{BOLD}All files saved in:{RESET}  {output_dir}\n")

# ── Entry point (called by initial.py) ───────────────────────────────────────
def run(target: str, phase: str, output_dir: str) -> None:
    """
    Public entry point — initial.py calls this as:
        profile_module.run(target=target, phase=args.phase, output_dir=output_dir)

    Loads ctf.json, resolves which phases to run, and hands each
    phase off to run_phase().
    """
    profile = load_profile(PROFILE_PATH)
    phases  = profile["phases"]

    # ── Print profile header ──────────────────────────────────────────────────
    print(f"\n{BOLD}{'═'*58}")
    print(f"  Profile  :  {CYAN}CTF Player{RESET}{BOLD}")
    print(f"  Target   :  {target}")
    print(f"  Phase    :  {phase}")
    print(f"  Output   :  {output_dir}")
    print(f"{'═'*58}{RESET}\n")

    # ── Resolve which phases to run ───────────────────────────────────────────
    if phase == "all":
        # run every phase in ctf.json in order
        phases_to_run = list(phases.keys())

    elif phase == "default":
        # no phase specified → run only the first phase (passive, safe default)
        phases_to_run = [list(phases.keys())[0]]

    else:
        # user asked for a specific phase by name e.g. --phase probing
        if phase not in phases:
            err(f"Phase '{phase}' not found in the CTF profile.")
            err(f"Available phases: {', '.join(phases.keys())}")
            sys.exit(1)
        phases_to_run = [phase]

    # ── Run ───────────────────────────────────────────────────────────────────
    for phase_name in phases_to_run:
        run_phase(phase_name, phases[phase_name], target, output_dir)

    print_summary(output_dir)


# ── Standalone mode (lets you run ctf.py directly for testing) ────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AutoRec — CTF Recon Profile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ctf.py example.com
  python ctf.py example.com --phase probing
  python ctf.py example.com --phase all
        """,
    )
    parser.add_argument("target",
                        help="Domain or IP to recon (e.g. example.com)")
    parser.add_argument("--phase",
                        choices=["default", "probing", "all"],
                        default="default",
                        help="Phase to run (default: passive only)")
    parser.add_argument("--output",
                        default=None,
                        help="Output directory (auto-generated if omitted)")

    args       = parser.parse_args()
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output or os.path.join(
        REPO_ROOT, "output", f"ctf_{args.target}_{timestamp}"
    )
    os.makedirs(output_dir, exist_ok=True)

    run(target=args.target, phase=args.phase, output_dir=output_dir)
