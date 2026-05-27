# Pull Request

## What does this PR do?

<!-- One or two sentences. e.g. "Adds ffuf to the bounty extended phase" or "Fixes timeout crash in run_tool()" -->

## Type of change

- [ ] Bug fix
- [ ] New feature / tool addition
- [ ] Profile update (new tool, phase, or profile)
- [ ] Documentation update
- [ ] Refactor / code cleanup

## Checklist

### Code
- [ ] My code follows the existing style (colour helpers, section banners, etc.)
- [ ] I ran `bash scripts/lint.sh` and there are no syntax errors
- [ ] I tested this change locally against a real or dummy target

### Profiles (if you changed a .json file)
- [ ] I ran `bash scripts/validate.sh` and both profiles pass
- [ ] New tools include `name`, `verify_cmd`, and at least one `install` option
- [ ] Active tools are placed in a phase with `"requires_manual_approval": true`

### Documentation
- [ ] I updated `docs/roadmap.md` if this adds a planned feature
- [ ] I updated `docs/schema.md` if I changed the JSON structure

## How to test this

<!-- Brief steps a reviewer can follow to reproduce your change -->

1. `git clone` / `git pull`
2. Run: `python src/autorec.py -p <profile> <target> --phase <phase>`
3. Expected result: ...

## Related issues

Closes #<!-- issue number -->
