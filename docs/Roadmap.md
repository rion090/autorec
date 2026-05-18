# AutoRec Roadmap

This is a living document. Items are grouped by priority, not by timeline.

---

## ✅ Done (v0.1)

- [x] CTF profile with passive (`default`) and active (`probing`) phases
- [x] Bug Bounty profile with passive (`default`) and extended phases
- [x] Unified launcher (`autorec.py`) with interactive profile selector
- [x] Tool preflight checks — detects missing tools and prints install hints
- [x] Manual approval gate before any active phase
- [x] Per-tool output files saved to timestamped directories
- [x] JSON schema validation (`scripts/validate.sh`)
- [x] CI via GitHub Actions (validate profiles + lint Python on PR)
- [x] Beginner-friendly colour output with plain-English tool labels

---

## 🔜 Near-term (v0.2)

- [ ] **Install script** (`scripts/install.sh`) — one command to install all tools for a chosen profile
- [ ] **`--dry-run` flag** — show what would run without actually running anything; great for beginners learning the tool
- [ ] **Summary report** — generate a single `summary.md` in the output directory with key findings highlighted
- [ ] **`httpx` extended output** — parse httpx results and flag interesting status codes (401, 403, 500)
- [ ] **Wordlist auto-detect** — check multiple wordlist paths for ffuf/dirb instead of hardcoding one

---

## 🔮 Future (v0.3+)

- [ ] **Third profile: API Recon** — tools aimed at REST/GraphQL endpoints (arjun, kiterunner)
- [ ] **Docker support** — run tools inside containers so nothing needs to be installed locally
- [ ] **Output deduplication** — merge subdomain lists from amass + subfinder + assetfinder into one clean file
- [ ] **Scope file support** — pass a `scope.txt` to restrict all tools to in-scope domains automatically
- [ ] **Config file** (`~/.autorec.conf`) — save preferred wordlist path, output directory, default profile
- [ ] **Progress bar** — show a spinner or ETA for long-running tools (nmap, amass)
- [ ] **JSON output mode** — `--json` flag to write machine-readable results alongside the text files

---

## 💡 Ideas under consideration

- Slack / Discord notification when recon finishes (for long bounty runs left overnight)
- Web UI (lightweight Flask/FastAPI dashboard to browse results)
- Plugin system so users can add custom tools without editing core files

---

Have an idea not listed here? Open an Issue with the **Profile Submission** template or start a discussion.
