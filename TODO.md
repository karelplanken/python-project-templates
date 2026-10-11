# TODO

- **Link existing projects to the template, so `copier update` works for
  them.** Projects generated before v1.0.0 have no `_commit` in
  `.copier-answers.yml`. Do this before the betterleaks migration below, so
  that migration can reach them with `copier update` instead of by hand.
  Try one project first (e.g. pourbaix), on its own branch:
  - In `.copier-answers.yml`, set `_src_path:
    gh:karelplanken/python-project-templates` (pourbaix has an absolute
    path to `app/`; analyze-pptx, marimo-exporation and simple-odmr have
    the relative `python-project-templates/scripts/`), add `_commit: v1.0.0`
    and add `project_shape` (`app` for pourbaix, `scripts` for the other
    three).
  - Copier then treats the project as generated from v1.0.0, so any
    difference between v1.0.0 and the template state it was really
    generated from counts as the project's own edit and is kept. Check with
    `copier update --trust --skip-answered` against a later tag and
    review the `git diff`.
  - fcc-coding-challenges isn't copier-generated (no answers file). It
    needs a full answers file written by hand, or it stays manual.

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
    `copier update` for those linked as above, by hand for the rest
    (pourbaix, analyze-pptx, marimo-exporation, simple-odmr,
    fcc-coding-challenges). Then uninstall `/usr/local/bin/gitleaks`.

- **Explore commitizen's `cz bump`.** Automatic semantic-version bumping
  and changelog generation from Conventional Commit history
  (`feat:`/`fix:`/`BREAKING CHANGE:` → version bump). This is separate
  from the commit-msg *linting* (`commitizen` prek hook, enforcing
  Conventional Commits format) already wired into every generated
  project's `prek.toml` — `cz bump` itself hasn't been explored or
  adopted anywhere in this repo or the templates it generates.
