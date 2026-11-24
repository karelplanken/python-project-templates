# TODO

The first four entries form the next release, `v2.1.0`; the fifth (a
docs file) can go on the same branch. Do them on one branch, then
release and `copier update` pourbaix.

- **Bug: `check-types` hook lacks `pass_filenames = false` (`v2.1.0`).**
  prek passes the changed files to the hook, so `just check-types` runs
  `mypy tests/test_x.py` instead of `mypy .`. mypy then can't resolve the
  project package from `src/` and fails with `Skipping analyzing
  '<pkg>.__main__': module is installed, but missing library stubs or
  py.typed marker [import-untyped]`. Any generated project hits this on
  its first commit or push that touches `tests/`. Found in pourbaix on
  2026-11-15, already fixed there in its own commit.
  - **Fix:** add `pass_filenames = false` to the hook, keeping
    `types = ["python"]`, so mypy always checks the whole project. That's
    also more correct: a change in one file can break types in another.
  - **Where:** the hook is in the root `prek.toml` and in all six shapes'
    `template/prek.toml.jinja`, not only `app` and `library`.
  - **Only `check-types` needs it.** What matters is whether a tool has
    to see other files to check one. mypy follows imports, so it does.
    `format` (ruff), `check-complexity` (complexipy) and `check-spelling`
    (codespell) check each file on its own, so passing file names is
    better: it's faster and only reports on what's being committed. For
    `format`, `pass_filenames = false` would make things worse: it would
    rewrite untouched files across the project and leave them as unstaged
    edits. Leave those three as they are.
  - pourbaix already has this fix locally, so its `copier update` to
    `v2.1.0` should merge it without changes.

- **Add a `default` recipe that lists the recipes (`v2.1.0`).** In all
  seven justfiles (root and the six shapes) the first recipe is
  `install`, so a bare `just` runs `uv sync`. Most people expect a bare
  `just` to show the recipe list. Make this the first recipe:
  ```just
  # Show which justfile is in use and list its recipes.
  default:
      @echo "Using {{ justfile() }}"
      @just --list
  ```
  - The first line prints the justfile's full path. That's the safeguard
    against running a parent project's recipes from a folder without its
    own justfile.
  - Optional: put `[private]` above `default:` to leave `default` out of
    its own list. A bare `just` still runs it, since it's the first
    recipe.
  - The recipe must be the same in every shape, or
    `check_shared_drift.py` flags it (it compares recipe bodies against
    `library/`).
  - The shapes ship a plain `justfile`, not `justfile.jinja`, so Jinja
    leaves `{{ }}` alone. If a justfile ever becomes `.jinja`, wrap the
    recipe in `{% raw %}…{% endraw %}`.
  - Not needed: `[confirm]` (no recipe deletes anything) and `[no-cd]`
    (recipes are meant to run from the project root). Note that attribute
    text isn't filled in: `[confirm("… {{ justfile_directory() }}?")]`
    prints the braces literally (tested with just 1.59.0).

- **Bug: the `uv_build` pin is out of date (`v2.1.0`).** Five shapes
  (all but `scripts`, which has no build backend) pin
  `uv_build>=0.11.28,<0.12.0`, while the local uv is 0.13.9. `uv build`
  only uses the backend built into uv when uv's version is inside that
  range. Otherwise it downloads an old `uv_build` from PyPI, which is
  slower and misses backend fixes. uv never raises the bound for you.
  - **Fix:** set `requires = ["uv_build>=0.13.9,<0.14"]` in each shape's
    `pyproject.toml.jinja`. The 0.12 and 0.13 release notes list no
    breaking changes to the backend config.
  - **Guard:** add a test in `tests/` that reads the pinned range from the
    shapes and fails when the local `uv --version` is above the upper
    bound (and that all five shapes pin the same range). Then the next
    uv minor release shows up as a failing test, not as a silent slow
    build.
  - Decided against (2026-11-24): a Jinja extension that reads
    `uv --version` during `copier copy`. It needs `--trust` on every
    copy and update plus the `copier-templates-extensions` plugin, and
    Copier stores the answer, so later updates keep the old value anyway.
    Projects get the new pin through `copier update`, like any template
    change.

- **Run fixing hooks on `pre-commit` only (`v2.1.0`).** The shapes
  install `pre-commit`, `commit-msg` and `pre-push` hooks, and every hook
  without `stages` runs at all of them. So the hooks that edit files run
  again during a push, and an edit made then is left as an uncommitted
  change after the push is rejected.
  - **Fix:** add `stages = ["pre-commit"]` to the fixing hooks:
    `trailing-whitespace`, `end-of-file-fixer`, `mixed-line-ending`
    (`--fix=lf`), `pretty-format-json` (`--autofix`) and `ruff-format`.
    The checks (mypy, complexity, spelling, gitleaks, the `check-*`
    hooks from pre-commit-hooks) keep running on `pre-push` too, as a
    second safety net after a `git commit --no-verify`.
  - In the root `prek.toml` and all six shapes' `prek.toml.jinja`.

- **Commit the tooling gotchas as `docs/tooling-gotchas.md`.** General
  know-how from moving pourbaix onto the `app` shape (prek, ruff, mypy,
  Pylance, pytest and mock, git and GitHub, uv). It's in
  `.collected-todos/python-tooling-gotchas.md`, which
  `.git/info/exclude` keeps out of git. Before committing, check each
  claim; in particular whether ruff really has a
  `# ruff: ignore[print]` comment form. Link it from README.md. No
  release needed (it's not part of any shape), but it can go on the
  `v2.1.0` branch.

- **Bring every project in `~/python-projects/` onto a template.** The
  goal: all projects are based on one of the shapes and take template
  changes with `copier update`. Do this before the betterleaks migration
  below, so that migration can reach them with `copier update` instead of
  by hand. How to link and update is in README.md ("Linking an older
  project", "Updating a project"). Expect repair work in each project after
  the first update: since `v2.0.0` ruff selects `ALL`. Commit the update
  and the fixes separately.

  State as of 2026-11-15 (from scanning for `.copier-answers.yml`):
  - **Linked and updated:** pourbaix (`app`, `v2.0.1`). Its ruff fixes
    continue in pourbaix's own `HANDOFF.md`.
  - **Answers file, not linked yet:** analyze-pptx and simple-odmr.
    Relative `_src_path: python-project-templates/scripts/`, no `_commit`
    and no `project_shape`. Set `_src_path:
    gh:karelplanken/python-project-templates`, `_commit: v1.0.0` and
    `project_shape: scripts`.
  - **Linked, but to the local folder:** snippets and var-py
    (`_commit: v1.0.0`, shape `scripts`, relative `_src_path` to this
    repo on disk). Switch `_src_path` to the `gh:` URL like the others,
    then update.
  - **No answers file:** algos, beginners-data-workshop, canvas-publisher,
    cegc-dshbrd, fcc-coding-challenges, fcc-dcc-tool, grade-pipeline,
    ollama-python-lab, oop-irv-kalb, practical-data-analysis-python,
    real-python (no `pyproject.toml` either), sqla-cc. For each, decide:
    which shape fits, then migrate with `copier copy` as pourbaix was
    (or write an answers file by hand and link it), or leave it alone
    (e.g. course material or archived work).
  - **fcc-coding-challenges only** (not the template): when it's migrated,
    add this to its own `pyproject.toml`:
    ```toml
    # fail_under is a starting point, not a mandate — adjust per project.
    # Each challenge file ends with an `if __name__ == '__main__':` debugging block
    # that the tests never run; exclude it so it doesn't count against coverage.
    # (Dots in the pattern are regex wildcards, matching either quote style.)
    [tool.coverage.report]
    fail_under = 70
    exclude_also = [
        'if __name__ == .__main__.:',
    ]
    ```

- **Migrate gitleaks → betterleaks, prek-only (after betterleaks v2.0.0
  stable).** Still waiting: `v2.0.0-rc.11` came out on 2026-11-24. Start
  from a fresh branch off `main` (the old `feat/migrate-to-betterleaks`
  branch only held TODO commits and was renamed). Gitleaks is
  security-patch only; its author moved to
  [betterleaks](https://github.com/betterleaks/betterleaks). Covers the root
  config, all six shapes and `tests/test_check_shared_drift.py`:
  - Let prek's `language: golang` hook build the pinned `rev`, and stop
    installing the binary system-wide. `just check-secrets` →
    `prek run betterleaks`.
  - Full-history scan: a second entry for the same hook in the same repo
    block, with `alias = "betterleaks-history"`, `stages = ["manual"]`,
    `always_run = true` (without it prek skips the hook with "no files to
    check") and an `entry` that drops `--staged`. Check the flags against the
    v2 CLI. Tested working with gitleaks on prek 0.5.0.
  - Drop `check-versions-sync` (justfile recipe + prek hook), the README
    install snippets and the copier `gitleaks_version` question. Templates
    ship a known-good `rev` that's updated with `prek autoupdate`; make sure
    it doesn't pick an rc tag.
  - Release it as a new tag, then bring existing projects along: with
    `copier update` for those linked by then, by hand for the rest. The
    first entry's inventory says which is which. Then uninstall
    `/usr/local/bin/gitleaks`.

- **Choose an automatic versioning tool.** Derive the SemVer bump,
  changelog and tag from Conventional Commit history
  (`feat:`/`fix:`/`BREAKING CHANGE:` → version bump) instead of picking
  the version by hand (see "Releasing a template change" in README.md).
  Candidates: commitizen's `cz bump` (the `commitizen` prek hook already
  lints commit messages in every generated project) and Python Semantic
  Release; compare them before choosing. Decide separately for this repo
  (only git tags carry the version, since there's no package) and for the
  generated projects (version in `pyproject.toml`, maybe a PyPI release).
  Current idea: Python Semantic Release in the templates, made optional
  through a copier question so each project opts in at generation (or
  later via `copier update` without `--skip-answered`).
  This was decided against once before, for a reason nobody recorded —
  write the reason down this time, whichever way it goes.

- **Consider a MicroPython template, probably separate from this repo.**
  Every MicroPython project needs the same setup to get type checking and
  editor completion for code that runs on a board: the board's stubs as a
  dev dependency, plus type-checker settings that use them instead of
  CPython's standard library. A template would set that up once.
  - **Leaning towards a separate template** rather than a seventh shape
    here: the parts that differ (stubs, deploying with e.g. `mpremote`,
    no `pytest`/coverage on the board, no package to build) touch most of
    the justfile and `pyproject.toml`, and the drift check would then flag
    them as drift against `library/`.
  - **Still shared, so decide what to copy:** ruff and formatting, type
    checking (with stubs), prek, codespell, secret scanning and commit-msg
    linting all work the same. Logic that doesn't touch hardware can still
    be tested with `pytest` on CPython.
  - **To work out first:** which stubs packages and boards to support (a
    copier question per board?). The MicroPython projects aren't in
    `~/python-projects/`, so look at them first.
