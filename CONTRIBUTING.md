# Contributing to AutoRec

Full contributing guide is in [`docs/contributing.md`](docs/contributing.md).

**Quick version:**

```bash
# Fork → clone → branch
git checkout -b feat/your-change

# Make changes, then check everything works
bash scripts/lint.sh
bash scripts/validate.sh

# Commit using a prefix: feat / fix / docs / refactor / ci / chore
git commit -m "feat: add naabu to bounty extended phase"

# Push and open a Pull Request
```

Pull requests that change `.json` profiles or `.py` source files must pass CI before merging.

See the [full guide](docs/contributing.md) for code style, how to add tools, and commit message conventions.
