# python-project-templates

![GitHub last commit](https://img.shields.io/github/last-commit/karelplanken/python-project-templates?color=blue)
![GitHub repo size](https://img.shields.io/github/repo-size/karelplanken/python-project-templates?color=orange)
![License](https://img.shields.io/github/license/karelplanken/python-project-templates?color=success)
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Copier](https://img.shields.io/badge/scaffolding-copier-orange)

A personal collection of [Copier](https://copier.readthedocs.io/) templates
for scaffolding Python projects — one template per project shape, each
pre-wired with the same tool stack and conventions so a new project starts
with linting, type checking, complexity limits, spell checking, secret
scanning, and git hooks already working, not something to bolt on later.

Inspired by (and started from) Nacho Lorca's
[`mold`](https://github.com/nachollorca/mold), from his EuroPython 2026 talk.

## Shapes

Each shape is an independent template in its own `<shape>/template/`
subdirectory, because the shapes genuinely diverge in structure (some aren't
even src-layout). A single root `copier.yml` asks "what kind of project?"
first and renders only the chosen shape's directory — it never branches
inside a shape. Pick the one that matches what you're building:

| Shape | Directory | For |
|---|---|---|
| Library/Package | `library/` | Anything meant to be `import`ed elsewhere — published to PyPI or installed by other projects. |
| Application (CLI/GUI) | `app/` | A runtime entry point that isn't a library — CLI tools or GUI apps (tkinter, pygame, etc.). Toolkit-agnostic; README documents Typer for CLI. |
| Web Application | `web-app/` | A running server — FastAPI, Flask, or Dash. Framework-agnostic; README documents all three. |
| Data Analysis/Research | `data-analysis/` | Notebook-driven exploration: `data/`, `notebooks/`, `reports/figures/`, plus a `src/` package for anything promoted out of a notebook. Prompts for a notebook runtime (VS Code/ipykernel, JupyterLab, both, or none). |
| Multi-subpackage Project | `multi-subpackage/` | One package, N independent self-contained units sharing a lockfile — a production pipeline (extract/transform/load per unit) or a book/tutorial study repo (one unit per chapter) are both this shape. |
| Single-file Script/Collection | `scripts/` | Flat, not src-layout — standalone scripts (e.g. daily coding challenges) sharing one `shared/` helpers module. |

A seventh shape, a `uv` workspace monorepo, is deliberately **not**
templated here — see `python-project-structures.md` in this repo for why,
and for the fuller reasoning behind each shape above.

## Prerequisites

Install these once, system-wide, before using any template:

- **[`uv`](https://docs.astral.sh/uv/)** — the Python package/environment
  manager everything else here depends on, including `copier` itself and
  every generated project's `uv sync`/`uv run`.
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **[`copier`](https://copier.readthedocs.io/)** — renders the templates.
  ```bash
  uv tool install copier
  ```
- **[`just`](https://github.com/casey/just)** — the command runner every
  generated project's `justfile` relies on (`just install`, `just check`, …).
  Installable via `uv` too, as the [`rust-just`](https://pypi.org/project/rust-just/)
  PyPI package (same binary, published under that name since `just` was taken):
  ```bash
  uv tool install rust-just
  ```
- **[`gitleaks`](https://github.com/gitleaks/gitleaks)** — the secret-scanning
  binary each generated project pins (in `prek.toml`) and checks against.
  It's a standalone Go binary, not something `uv sync` installs:
  ```bash
  GITLEAKS_VERSION=<version>   # match what you'll pin at generation time
  curl -sSL -o gitleaks.tar.gz "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
  tar xzf gitleaks.tar.gz gitleaks
  sudo mv gitleaks /usr/local/bin/
  rm gitleaks.tar.gz
  ```
- **[`prek`](https://github.com/j178/prek)** — no separate install needed.
  It's a dev dependency of every generated project, so `just install`
  (`uv sync`) pulls it into that project's own venv automatically.

## Using a template

```bash
copier copy --trust gh:karelplanken/python-project-templates ./my-new-lib
```

The first prompt lists every shape from the table above. `--trust` is
required — the templates use Jinja features (like the `to_nice_yaml`
filter for the answers file) that Copier treats as needing explicit trust,
which is fine for a template you wrote yourself.

Copier will then prompt for `project_name`, `project_slug`, a description,
optional keywords, your Python version, author name, the `gitleaks` version
to pin, and a copyright year (plus a notebook runtime for `data-analysis`) —
then generate the project. From there:

```bash
cd my-new-lib
just install         # uv sync — pulls in ruff, mypy, complexipy, codespell, pytest, prek
git init              # optional — install-hooks runs it if this isn't a repo yet
just install-hooks    # one-time: wires up prek's git hooks
just check            # format + types + complexity + spelling + version-sync + tests
```

Each generated project's own `README.md` documents its specific dev
commands, git hook behavior, and (for `app/`/`web-app/`/`scripts/`) the
toolkit/framework choices left for you to make after generation.

## Updating a project

Generated projects record the template version they came from (`_commit`)
and every answer, including the shape, in `.copier-answers.yml`.
`just template-version` prints that version (since `v2.2.0`). To pull in
later template changes, from a clean git working tree in the project:

```bash
copier update --trust --skip-answered
```

Copier merges the template's changes since that version into the project,
keeping your own edits. `--skip-answered` reuses the recorded answers
instead of asking every question again; drop it to change one. Copier
updates to the newest tag and commits nothing, so `git restore .` undoes
an update you don't want.

Then review what it did:

```bash
git diff        # _commit bumped + exactly the template's changes
just check      # new template rules may flag existing code
```

- **The diff should be small:** `_commit` in `.copier-answers.yml` plus the
  template change you released. Anything else is worth a closer look.
- **Conflicts** show up as `<<<<<<<` / `>>>>>>>` markers in the file (or as
  `.rej` files) where your edits overlap the template's. Resolve them before
  committing.
- **"Make sure Git >= 2.24 is installed"** is harmless with any recent Git:
  copier tries a `git diff` flag that newer Git rejects, then falls back.

Commit the update on its own, so it stays separate from any code fixes it
makes necessary: `chore: update to template vX.Y.Z`, with a body saying
what the release brought in when that isn't obvious from the version.

### Linking an older project

Projects generated before the root template existed (2026-10) have no
`_commit`, so `copier update` doesn't know where they started. Link one
by editing its `.copier-answers.yml`:

```yaml
_src_path: gh:karelplanken/python-project-templates
_commit: v1.0.0
project_shape: app   # the shape it was generated from
```

Commit that, then run `copier update` as above. Copier now treats the
project as generated from `v1.0.0`, so any difference between `v1.0.0` and
the template it really came from counts as your own edit and is kept.

## Shared tooling

Every shape uses the same stack: [`uv`](https://docs.astral.sh/uv/) for
environments and dependencies, [Ruff](https://docs.astral.sh/ruff/) for
linting and formatting, `mypy --strict` for type checking,
[`complexipy`](https://github.com/rohaquinlop/complexipy) for cognitive
complexity limits, `pytest` + coverage, [`codespell`](https://github.com/codespell-project/codespell)
for spell checking, [`gitleaks`](https://github.com/gitleaks/gitleaks) for
secret scanning, and [`prek`](https://github.com/j178/prek) (a Rust
`pre-commit` reimplementation) for git hooks — all driven through one
`justfile` per project, so the commands you run locally are exactly what
the git hooks run too.

One recurring design decision worth knowing: a tool's version only needs
active drift-checking (`just check-versions-sync`) when it's pinned in two
independently-edited places. Everything installed into the project's own
venv (`ruff`, `mypy`, `complexipy`, `codespell`, `pytest`, `prek` itself)
has exactly one pin — `pyproject.toml` — so `uv sync` keeps it correct by
construction. `gitleaks` is the one exception: a standalone Go binary
outside the venv, pinned separately in `prek.toml` and each README's
install snippet, which is why it's the only tool `check-versions-sync`
actually checks.

Known pitfalls with this stack (prek hook stages, ruff under `ALL`, mypy
and Pylance, mocks, git renames, the `uv_build` pin) are collected in
[docs/tooling-gotchas.md](docs/tooling-gotchas.md).

## Maintaining this repo

The per-shape templates duplicate their shared tooling files (`justfile`,
`prek.toml.jinja`, the `[tool.*]` blocks in `pyproject.toml.jinja`) rather
than composing them from one source — Copier has no native mechanism to
share config across independent templates. `check_shared_drift.py`
(`just check-shared-drift`) catches unintended drift: it diffs each
shape's shared recipes/hooks/config blocks against `library/`, the
reference shape, tolerating shape-specific additions (like
`data-analysis`'s extra `clean-notebooks` recipe) but flagging anything
`library` has that another shape is missing or disagrees with.

### Releasing a template change

Projects only see a change once it's tagged: `copier update` moves to the
newest tag, not to `main`.

1. **Branch from `main`** and make the change in every shape it applies to
   (usually all six), plus this repo's own `pyproject.toml` for ruff/mypy
   settings.
2. **Check it:** `just check-shared-drift`, `uv run pytest`, and render
   each shape you touched:

   ```bash
   copier copy --trust --defaults --vcs-ref HEAD \
       -d project_shape=app -d project_name="Demo" -d author_name=X \
       . /tmp/demo-app
   ```

   `--vcs-ref HEAD` renders the branch including uncommitted edits; without
   it copier uses the newest tag and you'd test the old template. Run the
   project's tools in the result (e.g. `ruff check`).
3. **PR, squash-merge, tag.** Tags are annotated, on the squash commit:

   ```bash
   git fetch origin main:main
   git tag -a vX.Y.Z -m "vX.Y.Z: <what changed>" main
   git push origin vX.Y.Z
   ```

4. **Update a project** to try it out (see [Updating a
   project](#updating-a-project)).

Pick the version by what updating costs a project, not by how big the
template change is:

- **Major:** projects need work after updating, e.g. new lint rules that
  flag existing code (`v2.0.0`: ruff `select = ["ALL"]`), a dropped Python
  version, a removed recipe. Mark the commit with `!` and a
  `BREAKING CHANGE:` footer.
- **Minor:** something new that existing projects pass as-is.
- **Patch:** a fix (`v2.0.1`: the answers file's trailing blank line).

## License

[MIT](LICENSE).
