# autorec 🕵️‍♀️
Modular CLI automated recon toolkit built for ethical use in CTFs and bug bounty workflows.

## 🚀 Goals
- Modular, fast recon across multiple targets — designed for repeatability and speed in real CTFs and bounty hunts
- Separate traffic profiles for CTF vs Bug Bounty — prevents tools like nmap or dirb from hitting 
official infrastructure by mistake
- Beginner-friendly setup and extensibility — clear installation path, modular structure, and docs 
that lower the barrier for new contributors
- Ethical by design — tooling is meant for learning, competition, and approved bounty scopes — 
not unauthorized scanning

## 📦 Setup
- Clone repo
- Run install script (coming soon)
- See [`docs/prelaunch.md`](docs/prelaunch.md) for launch checklist

## 🔐 License
MIT — open, modifiable, yours to build upon. See [LICENSE](LICENSE).

## 🧠 Git Notes
This project prefers merge-based pull behavior, to avoid rebase-related confusion during pulls, consider configuring:
```bash
git config --global pull.rebase false

##Project Repo structure Planned:
.
├── docs/
│   ├── prelaunch.md
│   ├── contributing.md
│   ├── schema.md              # Document the JSON profile schemas
│   └── roadmap.md
│
├── profiles/
│   ├── bounty.json
│   ├── ctf.json
│   └── schemas/
│       ├── bounty.schema.json  # JSON Schema validation files
│       └── ctf.schema.json
│
├── scripts/
│   ├── validate.sh             # Validate profiles against schemas
│   └── lint.sh
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── profile_submission.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       └── validate.yml        # CI to auto-validate profile JSON on PR
│
├── LICENSE
├── README.md
└── CONTRIBUTING.md
