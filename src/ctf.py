#!/usr/bin/env python3
"""
CTF Recon Profile Runner
Runs passive and (optionally) active recon tools defined in ctf.json
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
RESET  = "\033[0m"

def ok(msg):    print(f"{GREEN}[✔]{RESET} {msg}")
def warn(msg):  print(f"{YELLOW}[!]{RESET} {msg}")
def err(msg):   print(f"{RED}[✘]{RESET} {msg}")
def info(msg):  print(f"{CYAN}[→]{RESET} {msg}")
def banner(msg):print(f"\n{BOLD}{CYAN}{'─'*55}\n  {msg}\n{'─'*55}{RESET}")

# ── Load profile ──────────────────────────────────────────────────────────────
PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            "..", "profiles", "ctf.json")

def load_profile(path: str) -> dict:
    """Load and return the CTF profile JSON."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        err(f"Profile not found at: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        err(f"Bad JSON in profile: {e}")
        sys.exit(1)

# ── Tool checks ───────────────────────────────────────────────────────────────
def is_tool_installed(tool_name: str, verify_cmd: str) -> bool:
    """Return True if the tool exists on PATH and verify_cmd exits cleanly."""
    if not shutil.which(tool_name):
        return False
    try:
        subprocess.run(
            verify_cmd.split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
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
    """Print friendly install instructions for missing tools."""
    warn("The following tools are not installed:\n")
    for tool in missing_tools:
        print(f"  {BOLD}{tool['name']}{RESET}")
        installs = tool.get("install", {})
        if "apt" in installs:
            print(f"    via apt  →  {installs['apt']}")
        if "go" in installs:
            print(f"    via go   →  {installs['go']}")
        print()

# ── Manual approval gate ──────────────────────────────────────────────────────
def request_approval(phase_desc: str) -> bool:
    """Ask the user to confirm before running an active phase."""
    warn("This phase does ACTIVE probing (sends packets to the target).")
    warn(f"Phase: {phase_desc}")
    warn("Some CTFs forbid active scanning — check the rules first!\n")
    answer = input(f"{YELLOW}  Do you want to continue? [y/N]: {RESET}").strip().lower()
    return answer == "y"

# ── Command builders ──────────────────────────────────────────────────────────
def build_command(tool_name: str, flags: str, target: str) -> list[str]:
    """
    Build the command list for each tool.
    Extend this function when adding new tools.
    """
    flag_list = flags.split() if flags else []

    commands = {
        # passive
        "amass":       ["amass", "enum"] + flag_list + ["-d", target],
        "curl":        ["curl", "-sI"] + flag_list + [f"https://{target}"],
        "waybackurls": ["bash", "-c", f"echo {target} | waybackurls"],
        # probing
        "nmap":        ["nmap"] + flag_list + [target],
        "dirb":        ["dirb", f"http://{target}"] + flag_list,
        "httpx":       ["httpx"] + flag_list + ["-u", target],
    }

    if tool_name not in commands:
        # Fallback: tool + flags + target
        return [tool_name] + flag_list + [target]

    return commands[tool_name]

# ── Pretty output formatter ───────────────────────────────────────────────────
FRIENDLY_LABELS = {
    "amass":       "Subdomain discovery",
    "curl":        "HTTP header grab",
    "waybackurls": "Archived URLs (Wayback Machine)",
    "nmap":        "Open port scan",
    "dirb":        "Directory brute-force",
    "httpx":       "Live host / tech fingerprint",
}

def run_tool(tool: dict, target: str, output_dir: str) -> None:
    """Run a single tool and save + print its output."""
    label = FRIENDLY_LABELS.get(tool["name"], tool["name"])
    info(f"Running  →  {BOLD}{label}{RESET}  ({tool['name']})")

    cmd = build_command(tool["name"], tool.get("flags", ""), target)
    out_file = os.path.join(output_dir, f"{tool['name']}.txt")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip() or result.stderr.strip()

        # Save raw output
        with open(out_file, "w") as f:
            f.write(f"# {tool['name']} — {target}\n")
            f.write(f"# Command: {' '.join(cmd)}\n\n")
            f.write(output)

        if output:
            # Print a trimmed preview (first 15 lines)
            lines = output.splitlines()
            preview = "\n".join(f"    {l}" for l in lines[:15])
            print(preview)
            if len(lines) > 15:
                print(f"    {YELLOW}… {len(lines)-15} more lines → {out_file}{RESET}")
        else:
            warn(f"No output from {tool['name']}")

        ok(f"Saved to {out_file}\n")

    except subprocess.TimeoutExpired:
        err(f"{tool['name']} timed out (>120s). Try running manually.")
    except FileNotFoundError:
        err(f"{tool['name']} not found. Install it first.")
    except Exception as e:
        err(f"{tool['name']} failed: {e}")

# ── Phase runner ──────────────────────────────────────────────────────────────
def run_phase(phase_name: str, phase_data: dict, target: str, output_dir: str):
    """Check tools, (optionally) get approval, then run all tools in a phase."""
    banner(f"Phase: {phase_name.upper()}  —  {phase_data['description']}")

    tools = phase_data["tools"]
    ready, missing = check_tools(tools)

    if missing:
        print_install_hints(missing)
        if not ready:
            err("No tools available for this phase. Skipping.")
            return
        warn(f"Skipping {len(missing)} missing tool(s), running {len(ready)} available.\n")

    if phase_data.get("requires_manual_approval", False):
        if not request_approval(phase_data["description"]):
            warn("Skipped by user.\n")
            return

    phase_out = os.path.join(output_dir, phase_name)
    os.makedirs(phase_out, exist_ok=True)

    for tool in ready:
        run_tool(tool, target, phase_out)

# ── Summary ───────────────────────────────────────────────────────────────────
def print_summary(output_dir: str):
    banner("Recon Complete — Output Summary")
    for root, _, files in os.walk(output_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            size  = os.path.getsize(fpath)
            rel   = os.path.relpath(fpath, output_dir)
            print(f"  {GREEN}{rel}{RESET}  ({size} bytes)")
    print(f"\n{BOLD}All files saved in:{RESET} {output_dir}\n")

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="CTF Recon Profile Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ctf_profile.py example.com
  python ctf_profile.py example.com --phase default
  python ctf_profile.py example.com --phase probing
  python ctf_profile.py example.com --profile /path/to/ctf.json
        """
    )
    parser.add_argument("target",
                        help="Domain or IP to recon (e.g. example.com)")
    parser.add_argument("--phase",
                        choices=["default", "probing", "all"],
                        default="default",
                        help="Which phase to run (default: 'default' — passive only)")
    parser.add_argument("--profile",
                        default=PROFILE_PATH,
                        help="Path to ctf.json profile file")
    parser.add_argument("--output",
                        default=None,
                        help="Output directory (default: ./recon_<target>_<timestamp>)")

    args = parser.parse_args()

    # ── Load profile
    profile = load_profile(args.profile)

    # ── Output directory
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output or f"recon_{args.target}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # ── Header
    print(f"\n{BOLD}{'═'*55}")
    print(f"  CTF Recon Runner  —  profile: {profile['profile']}")
    print(f"  Target  : {args.target}")
    print(f"  Phase   : {args.phase}")
    print(f"  Output  : {output_dir}")
    print(f"{'═'*55}{RESET}\n")

    # ── Determine which phases to run
    phases = profile["phases"]

    if args.phase == "all":
        phases_to_run = list(phases.keys())
    else:
        if args.phase not in phases:
            err(f"Phase '{args.phase}' not found in profile.")
            sys.exit(1)
        phases_to_run = [args.phase]

    # ── Run phases
    for phase_name in phases_to_run:
        run_phase(phase_name, phases[phase_name], args.target, output_dir)

    print_summary(output_dir)


if __name__ == "__main__":
    main()
