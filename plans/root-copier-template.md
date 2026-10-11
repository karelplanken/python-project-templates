# Plan: single root copier template

Status: agreed 2026-10-11, not started. Follow the git conventions in
`CLAUDE.md`.

## Problem

Each shape (`app`, `data-analysis`, `library`, `multi-subpackage`,
`scripts`, `web-app`) is its own copier template in a subdirectory of this
repo. Copier only treats a template as versioned when its source is the root
of a git repo, so generated projects get no `_commit` in
`.copier-answers.yml` and `copier update` can't be used on them. The repo
also has no tags, which `copier update` uses to pick versions. Some existing
projects also recorded a relative `_src_path`
(`python-project-templates/scripts/`), which only resolves from one working
directory.

## Goal

One copier template at the repo root:

```bash
copier copy --trust gh:karelplanken/python-project-templates ./my-project
```

- **First question: what kind of project.** It's a `choices` question
  listing all six shapes, each with a one-line description (reuse the
  descriptions in the README's shape table), so every option is visible when
  choosing.
- `_subdirectory` is templated from that answer, e.g.
  `"{{ project_shape }}/template"`, so the per-shape `template/` directories
  stay where they are.
- The shared questions are defined once: `project_name`, `project_slug`,
  `project_description`, `project_keywords`, `python_version`,
  `author_name`, `gitleaks_version`, `license_year`. Keep their current
  `help`, `default` and `validator` text (check the six `copier.yml` files
  agree first, and flag any differences instead of silently picking one).
- Shape-specific questions are gated with `when:`; currently only
  `notebook_runtime` (data-analysis).
- Shape-specific `_exclude` entries must still apply only to their shape.
  Today `tests/.gitkeep` is excluded in every shape except `scripts`.
  Check whether a single list works or whether it needs Jinja conditions.
- Remove the per-shape `copier.yml` files once the root one replaces them.

## Out of scope

- Composing the duplicated shared files (justfile, prek.toml.jinja,
  pyproject.toml.jinja) from one source. `check_shared_drift.py` keeps
  guarding them and must still pass. Note that it discovers shapes with
  `REPO_ROOT.glob('*/copier.yml')` (line 56), which breaks once the
  per-shape `copier.yml` files are removed. Switch it to `*/template/`
  (or the root `copier.yml` choices) and keep its tests passing.
- The gitleaks → betterleaks migration (see `TODO.md`). Don't touch
  gitleaks config in this refactor.
- Creating tags, opening PRs, and migrating existing generated projects.
  These are left for the maintainer.

## Acceptance

1. **Byte-identical output.** For each of the six shapes, generating from
   the old per-shape template (at `main` before this branch) and from the
   new root template with the same answers produces identical trees, apart
   from `.copier-answers.yml`. Do this with `copier copy --defaults --data
   ...` into temp dirs and `diff -r`, and report the result for every shape.
2. **Updatable.** A project generated from a local clone of the branch,
   using its git path, records `_commit` and `_src_path`. After a test
   commit and tag in that clone, `copier update` on the project works.
   Do this in a throwaway clone, never in the real repo.
3. **Answers file.** `.copier-answers.yml` records the shape answer, so
   `copier update` doesn't ask it again.
4. The existing tests (`just test` or `uv run pytest`) and
   `check_shared_drift.py` pass.
5. `README.md` documents the new single command and how `copier update`
   works. Drop the "swap `library` for any shape directory" instructions.
   `python-project-structures.md` is updated if it describes the old
   per-shape invocation.

## Deliverable

A pushed branch, e.g. `refactor/single-root-copier-template`, with
Conventional Commits and no PR. Finish with a short summary listing the
acceptance results, anything that didn't match exactly, and suggested next
steps (first tag, e.g. `v1.0.0`; how to adopt existing projects).
