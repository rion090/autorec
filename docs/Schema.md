# Profile Schema Reference

AutoRec uses JSON profiles to define which tools run, in what order, and under what conditions. This page documents every field.

---

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile` | string | ✅ | Unique identifier for this profile (e.g. `ctf_player`, `bounty_hunter`) |
| `description` | string | ✅ | Plain-English summary of what this profile is for |
| `aggressive_mode` | boolean | ✅ | Global flag — when `true`, tools may run with noisier/faster flags. Currently `false` for all profiles |
| `docker_support` | boolean | ✅ | Reserved for future Docker-based execution. Always `false` for now |
| `phases` | object | ✅ | Named phases (see below). Must have at least one |

---

## Phase object

A phase groups tools that share the same risk level and approval requirements.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | ✅ | What this phase does, in plain English |
| `requires_manual_approval` | boolean | ✅ | If `true`, the user must type `y` before any tools in this phase run |
| `aggressive_mode` | boolean | ❌ | Phase-level override of the top-level flag |
| `tools` | array of tool objects | ✅ | The tools to run in this phase (at least one) |

### Phase naming conventions

| Profile | Phase name | Meaning |
|---------|------------|---------|
| CTF | `default` | Passive-only recon, no target interaction |
| CTF | `probing` | Light active scanning — needs approval |
| Bounty | `default` | Safe passive recon, no direct traffic |
| Bounty | `extended` | Light active recon — needs approval |

---

## Tool object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | The CLI binary name exactly as it appears on PATH (e.g. `amass`, `httpx`) |
| `verify_cmd` | string | ✅ | Command AutoRec runs to confirm the tool is installed. Should exit cleanly (e.g. `amass -version`) |
| `flags` | string | ❌ | Extra flags passed to the tool, space-separated (e.g. `-passive`, `-T2`) |
| `install` | object | ❌ | Install instructions. Supported keys: `apt`, `go`, `pip`, `git` |

### Install object

```json
"install": {
  "apt": "apt install amass",
  "go":  "go install github.com/owasp-amass/amass/v4/...@master"
}
```

All install keys are optional. Include whichever methods are available for that tool.

---

## Full example

```json
{
  "profile": "bounty_hunter",
  "description": "Passive-first recon for bug bounty programs.",
  "aggressive_mode": false,
  "docker_support": false,
  "phases": {
    "default": {
      "description": "Safe passive recon. No direct target interaction.",
      "requires_manual_approval": false,
      "tools": [
        {
          "name": "amass",
          "flags": "-passive",
          "verify_cmd": "amass -version",
          "install": {
            "apt": "apt install amass",
            "go":  "go install github.com/owasp-amass/amass/v4/...@master"
          }
        }
      ]
    },
    "extended": {
      "description": "Light active recon. Check scope before running.",
      "requires_manual_approval": true,
      "tools": [
        {
          "name": "ffuf",
          "flags": "",
          "verify_cmd": "ffuf -V",
          "install": {
            "go": "go install github.com/ffuf/ffuf/v2@latest"
          }
        }
      ]
    }
  }
}
```

---

## Validation

Profiles are validated against JSON Schema files in `profiles/schemas/`.

Run locally:
```bash
bash scripts/validate.sh
```

This also runs automatically in CI on every pull request that touches a `.json` file.

---

## Adding a new tool

1. Add the tool object to the correct phase in the relevant `.json` file.
2. Add a `build_command` entry in `src/bounty.py` or `src/ctf.py`.
3. Add a human-readable label to `FRIENDLY_LABELS` in the same file.
4. Run `bash scripts/validate.sh` to confirm the profile is still valid.
5. Open a PR — CI will validate automatically.
