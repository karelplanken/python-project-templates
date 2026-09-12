# TODO

- **Explore commitizen's `cz bump`.** Automatic semantic-version bumping
  and changelog generation from Conventional Commit history
  (`feat:`/`fix:`/`BREAKING CHANGE:` → version bump). This is separate
  from the commit-msg *linting* (`commitizen` prek hook, enforcing
  Conventional Commits format) already wired into every generated
  project's `prek.toml` — `cz bump` itself hasn't been explored or
  adopted anywhere in this repo or the templates it generates.
