# TODO

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
  stable).** Gitleaks is security-patch only; its author moved to
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
