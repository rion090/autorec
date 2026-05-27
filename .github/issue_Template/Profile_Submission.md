---
name: Profile Submission
about: Propose a new recon profile or suggest tools to add to an existing one
title: "[PROFILE] "
labels: profile-submission
assignees: rion090
---

## Profile name

<!-- A short, descriptive name. e.g. "Mobile App Recon", "API-Only Bug Bounty" -->

## Use case

<!-- Who is this for? What scenario does it cover that the existing CTF / Bounty profiles don't? -->

## Proposed tools

| Tool name | Phase (passive/active) | What it does (plain English) | Install command |
|-----------|------------------------|------------------------------|-----------------|
| e.g. naabu | active | Fast port scanner | `go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest` |

## Draft JSON (optional but appreciated)

```json
{
  "profile": "your_profile_name",
  "description": "...",
  "aggressive_mode": false,
  "docker_support": false,
  "phases": {
    "default": {
      "description": "...",
      "requires_manual_approval": false,
      "tools": []
    }
  }
}
```

## Ethical considerations

<!-- Confirm this profile is designed for authorised use only.
     Does it require any special scope conditions? Does any tool make noise? -->

- [ ] All tools are passive-first or clearly gated behind manual approval
- [ ] Profile is intended for CTFs, authorised bounty programmes, or owned targets only
