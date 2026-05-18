# Contributing to AutoRec

Thanks for wanting to help! AutoRec is a beginner-friendly project and contributions of all sizes are welcome — from fixing a typo to adding a whole new recon profile.

---

## Ways to contribute

- **Report a bug** → open an Issue using the Bug Report template
- **Suggest a new tool** → open an Issue using the Profile Submission template
- **Fix a bug or add a feature** → open a Pull Request (see below)
- **Improve docs** → even small clarifications help beginners a lot

---

## Getting started

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/autorec.git
cd autorec

# 2. Create a new branch for your change
git checkout -b feat/add-naabu-to-bounty

# 3. Make your changes

# 4. Run checks before pushing
bash scripts/lint.sh          # Python syntax check
bash scripts/validate.sh      # JSON profile validation

# 5. Commit and push
git add .
git commit -m "feat: add naabu to bounty extended phase"
git push origin feat/add-naabu-to-bounty

# 6. Open a Pull Request on GitHub
```

---

## Code style

- Match the existing style: colour helpers (`ok`, `warn`, `err`, `info`), `section()` banners, 4-space indent, 100-char line limit.
- New tools go in `build_command()` and `FRIENDLY_LABELS` in the relevant profile module.
- Keep function docstrings short and plain — this project is aimed at beginners.

---

## Adding a new tool to a profile

1. Add the tool object to `profiles/bounty.json` or `profiles/ctf.json`:

```json
{
  "name": "naabu",
  "flags": "",
  "verify_cmd": "naabu -version",
  "install": {
    "go": "go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
  }
}
```

2. Wire up the command in `src/bounty.py` (or `ctf.py`) inside `build_command()`:

```python
"naabu": ["naabu"] + flag_list + ["-host", target],
```

3. Add a plain-English label in `FRIENDLY_LABELS`:

```python
"naabu": "Fast port scanner",
```

4. Run `bash scripts/validate.sh` — both profiles must pass.

---

## Commit message format

Use the following prefixes so the changelog stays readable:

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature or tool |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change with no behaviour change |
| `ci:` | GitHub Actions / CI changes |
| `chore:` | Maintenance (deps, scripts) |

Example: `feat: add arjun to bounty default phase`

---

## Pull request rules

- PRs that change `.json` files **must** pass the `validate-profiles` CI job.
- PRs that change `.py` files **must** pass the `lint-python` CI job.
- Please fill in the PR template — it only takes a minute and helps reviewers a lot.

---

## Code of conduct

Be kind. This project is a learning environment. Everyone here is figuring things out.
