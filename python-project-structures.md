# Python Project Structures

Reference for scoping Copier templates. Seven structural families, based on
where source lives, whether there's a distributable package, and what kind
of non-code assets the project carries.

Shared across all templates regardless of shape: `uv`, Ruff (extending
`~/.dev-tools/ruff.toml`, not duplicating it), mypy `--strict`, pytest +
coverage gate, justfile, codespell, gitleaks. Only directory shape and
`pyproject.toml` target change between templates.

---

## 1. Installable Library / Package

For anything published to PyPI or installed by other projects (`import foo`).

```
my-lib/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_lib/
│       ├── __init__.py
│       ├── py.typed
│       └── core.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
└── docs/            # optional, mkdocs/sphinx
```

- src-layout is the PyPA-recommended default. It forces tests/tooling to run
  against the *installed* package (`uv pip install -e .`), not the working
  directory — catches "works because CWD is on sys.path" bugs early.
- `py.typed` marker required for downstream type-checkers to trust inline
  hints once installed elsewhere.

---

## 2. Application (CLI/GUI)

Same skeleton as a library, plus an entry point — for anything with a
runtime entry point that isn't meant to be `import`ed elsewhere (CLI tools,
but also GUI apps: tkinter, pygame, etc.). Matches `fb-fcc-dcc` /
`fcc-dcc-tool` shape, and also the shape of a repo like `oop-irv-kalb`'s
individual chapters (see #5 for the multi-chapter case).

```
my-app/
├── pyproject.toml        # [project.scripts] my-app = "my_app.__main__:app"
├── src/
│   └── my_app/
│       ├── __init__.py
│       ├── __main__.py   # entry point stub — CLI app object, tkinter
│       │                 # mainloop, etc., whatever you're building
│       ├── commands/      # CLI flavor: subcommand wiring, thin
│       │   ├── __init__.py
│       │   └── fetch.py
│       └── core/
│           └── processing.py
├── tests/
└── justfile
```

- `commands/` (subcommand wiring, thin) vs `core/` (logic, testable without
  invoking the CLI runner) — same split you already use between bash
  orchestration and `process_challenge_md.py`. For a GUI flavor,
  `commands/` doesn't apply — just `core/` for testable logic kept out of
  event handlers/callbacks.
- **Toolkit-agnostic by design (2026-08-23), same reasoning as #3's
  framework-agnostic decision:** no CLI/GUI toolkit dependency is added by
  the template — `__main__.py` stays a stub, and the README documents the
  recommendation instead: **Typer** for a CLI (type-hint-driven, matches
  the `mypy --strict` philosophy already in every template — chosen over
  Click) via `uv add typer`; tkinter for a GUI needs no install (stdlib);
  pygame/PySide etc. via `uv add` as needed. Baking in Typer as a real
  dependency would have made the broadened CLI/GUI name misleading, so the
  choice moved from "templated" to "documented," matching #3 and #5's
  precedent of accepting a little pre-wired boilerplate loss in exchange
  for one template instead of near-duplicates.

---

## 3. Web Application (FastAPI / Flask / Dash)

Distinct because there's a runtime entrypoint, not a distributable package,
and non-Python assets matter.

```
my-app/
├── pyproject.toml
├── src/
│   └── my_app/
│       ├── __init__.py
│       ├── main.py           # app factory / ASGI entrypoint
│       ├── api/
│       │   └── routes/
│       ├── models/            # ORM / pydantic models
│       ├── services/          # business logic
│       └── config.py
├── tests/
│   ├── unit/
│   └── integration/
├── migrations/                 # alembic, if using SQLAlchemy
├── static/
└── templates/                  # if server-rendered
```

- `api/` (transport) vs `services/` (logic) vs `models/` (data shape) keeps
  route handlers thin.
- Django has its own `manage.py` / app-per-directory convention — doesn't
  fit this shape, would need its own template if ever used.
- **Framework-agnostic by design (2026-08-23):** FastAPI and Flask differ
  enough in app-factory pattern, routing, and test client that picking one
  via a copier question would mean the same kind of heavy per-branch
  conditionals rejected at the repo level (independent per-shape templates
  instead of one root selector) — and splitting into two full templates
  (`fastapi/`, `flask/`) would duplicate all the shared tooling
  (justfile, prek.toml, ruff/mypy config) for what's really just a few
  lines of `main.py`/routes difference. So: no framework dependency is
  added by the template, `main.py` stays a stub, and the README documents
  what to do once you've picked one:
  - **Framework:** `uv add fastapi uvicorn[standard]` or `uv add flask`.
  - **`pytest-asyncio`** (only needed if you go FastAPI + async routes and
    want to test them directly, i.e. `async def test_...`): `uv add
    --group dev pytest-asyncio`, then add `asyncio_mode = "auto"` under
    `[tool.pytest.ini_options]` in `pyproject.toml`.
  - **`alembic`** (only if using SQLAlchemy for migrations): `uv add
    sqlalchemy alembic`, then `alembic init migrations`.
  - **justfile:** add a `serve` recipe once a framework's picked, e.g.
    `uv run --frozen uvicorn {{ project_slug }}.main:app --reload` or
    `uv run --frozen flask --app {{ project_slug }}.main run --debug`.
  - **prek:** no adjustments needed — ruff/mypy/complexipy/pytest hooks
    are already framework-agnostic.
- **Dash (Plotly) also fits this shape (2026-08-24), documented as a
  third option:** Dash is Flask underneath (`app.server` is a real Flask
  instance), has a runtime entrypoint rather than being an importable
  package, and the `services/`/`models/`/`config.py` split still applies
  — same reasoning that qualifies FastAPI/Flask. A few Dash-specific
  conventions worth calling out in the README rather than assuming
  FastAPI/Flask defaults:
  - **Framework:** `uv add dash` (bundles Flask + Plotly.js + the React
    wrapper).
  - **`assets/` replaces `static/`** — Dash auto-serves and hot-reloads
    everything in a folder literally named `assets/`; it isn't optional
    naming, it's a Dash convention.
  - **`pages/` can replace `api/routes/`** if using Dash's multi-page app
    support (`dash.register_page`) — Dash apps are usually callback-driven
    rather than REST-routed, so `api/` may go unused entirely unless you
    add your own Flask routes via `app.server.route(...)`.
  - **Testing:** Dash's own browser-based integration testing
    (`dash.testing`, Selenium-driven) is heavier than the default
    unit/integration split and is opt-in — `uv add --group dev
    dash[testing]` only if you need it; plain `services/`/`models/` logic
    stays testable the normal way without it.
  - `pytest-asyncio` doesn't apply (Dash/Flask are sync); `alembic`
    guidance is unchanged if a Dash app uses SQLAlchemy underneath.

---

## 4. Data Analysis / Research Project

Notebook-driven, exploratory. Output is a figure or conclusion, not a
destination. Reproducibility comes from re-running transforms, not from
committing data.

```
my-analysis/
├── pyproject.toml
├── data/
│   ├── raw/          # immutable, gitignored, read-only
│   ├── interim/       # intermediate transforms
│   └── processed/     # final, analysis-ready
├── notebooks/
│   └── 01-explore.ipynb   # numbered, throwaway exploration
├── src/
│   └── my_analysis/
│       ├── __init__.py
│       ├── data_loading.py
│       └── transforms.py
├── reports/
│   └── figures/
└── tests/
```

- Notebooks stay exploratory; anything reused gets promoted into
  `src/my_analysis/` as a tested function.
- Consider a `configs/` dir if instrument/acquisition parameters need
  separate version control from code (relevant given lab infra work).

---

## 5. Multi-subpackage Project (extensible, N independent units)

Generalized from an original "Data Pipeline" framing. Shape: one src-layout
package, one `pyproject.toml`/lockfile, and N independent, self-contained
subpackages under a units directory, each free to hold whatever it needs
internally, sharing a `shared/` for common code. No notebooks. Distinct
from #4 — units aren't exploratory research, whatever's inside them is
considered "done" code.

```
my-project/
├── pyproject.toml
├── src/
│   └── my_project/
│       ├── cli.py                 # optional: `my-project run <name>`
│       ├── units/
│       │   ├── example_unit_a/
│       │   │   └── ...            # whatever this unit needs
│       │   └── example_unit_b/
│       │       └── ...
│       └── shared/
│           ├── io.py
│           └── config.py
├── configs/                        # optional, if units need config files
│   ├── example_unit_a.toml
│   └── example_unit_b.toml
├── tests/
│   ├── example_unit_a/
│   └── example_unit_b/
└── justfile
```

- Extending = new subpackage under `units/` + its own test dir, sharing
  `shared/` and (optionally) its own config file.
- The template scaffolds the shape only — one example unit, empty inside —
  and doesn't bake in any convention for what goes inside a unit, since
  that varies by use case. Two known flavors:
  - **Production pipeline** (the original motivating case: a Canvas LMS
    grade report generator with sub-pipelines per course/report type).
    Recommended internal convention, documented in the generated README
    but not enforced by the template: stage each unit as
    extract.py → transform.py → load.py (E/T/L), idempotent, landing data
    somewhere (file, DB, report).
  - **Book/tutorial study repo** (e.g. working through a book chapter by
    chapter, each chapter its own runnable unit with its own
    `[project.scripts]` entry point, sharing one venv/lockfile — the shape
    `oop-irv-kalb` already uses). No E/T/L convention applies; a unit here
    is just "chapter N's code," e.g. `main.py` plus whatever supporting
    modules that chapter needs.
- Overlaps loosely with the CLI template's commands/core split; the
  differentiator is that each unit is independent enough to be added,
  removed, or run on its own, rather than being a subcommand of one
  cohesive CLI.

---

## 6. Single-file Script / Script Collection

Deliberately *not* src-layout. For fCC-style daily challenges or any script
meant to run standalone. Kept as a template mainly because the fCC repo is a
real, if outlier, use case — not because the pattern generalizes widely yet.

```
my-scripts/
├── pyproject.toml
├── shared/
│   └── helpers.py
├── challenge_042.py
├── challenge_043.py
└── tests/
```

- **Settled (2026-08-23): `shared/` is the default**, not per-script
  duplication. The `fcc-coding-challenges` repo's current per-script
  duplication was an unexamined artifact of how the repo grew, not a
  deliberate choice — the template should default to `shared/` for
  helpers reused across scripts (e.g. common test scaffolding).
- **Settled (2026-08-23): one shared `pyproject.toml`, mechanically
  identical to every other template** (one `dependencies = []`/`dev`
  group, one venv, no `src/`-layout) — not a "strict PEP 723" variant
  where each script declares its own inline deps. That was considered and
  rejected: it splits the world in two (the dev venv pytest runs in vs.
  each script's own ephemeral PEP-723 env), which forces testable logic
  out of scripts and into `shared/` just to keep it reachable from tests —
  disproportionate complexity for a use case (`fcc-coding-challenges`-style
  daily exercises) that rarely needs script-specific third-party deps
  anyway. PEP 723 inline metadata (`# /// script` block) stays available
  as a **documented, optional** pattern in the README — for a genuinely
  standalone one-off script meant to be copied elsewhere without the repo
  — but the template doesn't structurally commit to it.

---

## 7. Monorepo / Multi-package Workspace

**Description only — not being templated for now.**

```
my-workspace/
├── pyproject.toml          # workspace root, uv workspace config
├── packages/
│   ├── core-lib/
│   │   ├── pyproject.toml
│   │   └── src/core_lib/
│   └── cli-tool/
│       ├── pyproject.toml
│       └── src/cli_tool/
└── tests/
```

- `uv` supports workspaces natively (`[tool.uv.workspace]`) — multiple
  *installable* packages sharing one lockfile, each independently versioned.
- Only worth building once two+ packages need independent versioning.

**Related but distinct pattern (not a uv workspace, not templated):**
multi-target embedded projects like `pico-qty-expl` — separate on-device
targets (e.g. Pico W, QT Py ESP32-S3) in one repo, each with its own
`typings/` dir for IntelliSense, no `pyproject.toml`, no installable
package, no shared Python code between targets:

```
pico-qty-expl/
├── HANDOFF.md
├── README.md
├── pico-qty-expl.code-workspace
├── pico-w/
│   ├── sensor_test.py
│   └── typings/
└── qtpy-s3/
    ├── blink.py
    ├── hdc3022.py
    └── typings/
```

This is worth keeping as a documented pattern for future embedded projects,
but it isn't a Python packaging structure — no template needed unless the
pattern repeats enough to be worth automating the `typings/` + workspace
scaffolding itself.

---

## Summary

| Template | Layout | Notes |
|---|---|---|
| Library/Package | src-layout | PyPA default |
| Application (CLI/GUI) | src-layout | toolkit-agnostic (Typer/tkinter/etc. documented, not templated); commands/ vs core/ |
| Web Application (FastAPI/Flask/Dash) | src-layout | api/ vs services/ vs models/; Dash uses assets/ + pages/ instead of static/ + api/ |
| Data Analysis/Research | src-layout + data/ + notebooks/ | data/raw read-only |
| Multi-subpackage Project | src-layout + units/ + optional configs/ | N independent units, extensible; flavors: pipeline (E/T/L convention) or book/tutorial study repo |
| Single-file Script/Collection | flat, no src/ | shared/ for helpers |
| Monorepo/Multi-package Workspace | *(description only, not templated)* | uv workspace; embedded multi-target noted separately |
