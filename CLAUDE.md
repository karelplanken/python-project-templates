# Git Conventions

Follow these exactly when creating branches, commits, PRs, or tags in this repo.

## Branches

Format: `<type>/<short-kebab-description>`, or `<type>/<issue-number>-<short-kebab-description>` when the work is tied to an issue.

- Lowercase, hyphens only, 3–5 words after the type.
- Never use vague names (`fix/bug`, `feat/updates`) or personal names.

Types: `feat` `fix` `chore` `docs` `refactor` `test` `hotfix` `release`

Examples:
- `feat/pico-imu-driver`
- `fix/i2c-timeout-handling`
- `fix/1-toml-quote-escaping`

**When creating a branch from a GitHub issue via the web UI ("Development" → "Create a branch"):** edit the suggested branch name field to `<type>/<issue-number>-<short-description>` before clicking create. This keeps the branch linked to the issue (auto-shown in its sidebar, auto-closed on merge) while following the naming convention — GitHub's linking is tied to using that creation flow, not to the specific name it suggests.

## Commits — Conventional Commits

```
<type>(<scope>): <summary>

<body>

<footer>
```

- **Summary**: imperative mood, no trailing period, ≤72 chars. `feat(imu): add ISM330DHCX driver stub`, not `added the driver`.
- **Scope** (optional): affected module, in parens — `fix(hdc3022): correct humidity scaling`.
- **Body** (optional): explain what/why, not how. Wrap ~72 chars.
- **Footer** (optional): `Closes #42`, or `BREAKING CHANGE: ...`.
- Breaking change shorthand: `feat(api)!: drop support for Python 3.9`.

Types: `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`

**Always draft the commit message and show it before committing — do not commit automatically unless the user has explicitly said to.**

## Pull Requests

- Title mirrors commit convention: `feat: add QT Py S3 stub package`.
- Squash-merge into `main`.
- Delete the branch after merge.
- **Do not open PRs unless explicitly asked to** — leave that step for the user to review first.

## Tags

SemVer: `vMAJOR.MINOR.PATCH` (e.g. `v1.1.0`). Pre-release: `v1.2.0-rc.1`.

## Reference workflow

```bash
git checkout -b feat/qtpy-s3-imu-driver
git commit -m "feat(imu): add ISM330DHCX driver with typed stubs"
git commit -m "test(imu): add unit tests for accel scaling"
git push origin feat/qtpy-s3-imu-driver
# PR title: "feat: add QT Py S3 IMU driver" → squash-merge into main
git tag v1.3.0 && git push origin v1.3.0
```
