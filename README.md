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

Each shape is an independent Copier template in its own subdirectory —
there's no single root template with a "what kind of project?" prompt,
because the shapes genuinely diverge in structure (some aren't even
src-layout). Pick the one that matches what you're building:

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
copier copy gh:karelplanken/python-project-templates/library ./my-new-lib --trust
```

Swap `library` for any shape directory from the table above. `--trust` is
required — the templates use Jinja features (like the `to_nice_yaml`
filter for the answers file) that Copier treats as needing explicit trust,
which is fine for a template you wrote yourself.

Copier will prompt for `project_name`, `project_slug`, a description, your
Python version, author name/email, the `gitleaks` version to pin, and a
copyright year — then generate the project. From there:

```bash
cd my-new-lib
just install         # uv sync — pulls in ruff, mypy, complexipy, codespell, pytest, prek
just install-hooks    # one-time: wires up prek's git hooks
just check            # format + types + complexity + spelling + version-sync + tests
```

Each generated project's own `README.md` documents its specific dev
commands, git hook behavior, and (for `app/`/`web-app/`/`scripts/`) the
toolkit/framework choices left for you to make after generation.

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

## License

[MIT](LICENSE).
