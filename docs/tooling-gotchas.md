# Python tooling gotchas

General know-how about uv, prek, ruff, mypy, Pylance, pytest and git,
collected while moving pourbaix onto the `app` shape (2026-10/11). None of
it is specific to that project: it applies to any project made from these
templates. Checked on 2026-11-24 with ruff 0.16.5, mypy 2.3.1, prek
0.5.0 and uv 0.13.9.

## prek hooks

- **Hooks without `stages` run at every installed hook type,** including
  `pre-push` and `commit-msg`. Only hooks with an explicit `stages = [...]`
  are limited, so a push can fail on the same checks as a commit, and
  each commit runs the checks twice (pre-commit and commit-msg). A
  top-level `default_stages` sets the stages for every hook without its
  own; since `v2.2.1` the templates use `["pre-commit", "pre-push"]`. Since `v2.1.0` the
  templates limit the hooks that edit files to `pre-commit`; the checks
  still run on `pre-push` too. Since `v2.2.0` each fixer that has a
  check mode also has a pre-push twin that only checks: `check-ruff`
  and `check-format` for `ruff-format`, `check-notebooks` for
  `clean-notebooks`.
- **Hooks that fix files change them even when they fail.** For example
  `ruff check --fix` (in `just format`), `pretty-format-json --autofix`
  and `end-of-file-fixer`. After a rejected commit, check `git status` and
  `git restore` any edits that don't belong in this commit.
  `prek run --all-files` does the same to every file in the repo.
- **mypy needs `pass_filenames = false`.** prek passes the changed files
  to a hook, so `just check-types` would become `mypy tests/test_x.py`.
  mypy then can't resolve the package from `src/` ("module is installed,
  but missing library stubs or py.typed marker"). Checking the whole
  project is also more correct, because a change in one file can break
  types in another. The templates set it since `v2.1.0`. Don't add it to
  hooks that fix files, like `ruff-format`: they would then rewrite files
  you didn't touch.
- **`--no-verify` skips the hooks,** for `git commit` and `git push`
  alike. There is no `--no-check`.
- **Generated files that hooks check:** make the generator write the
  hook's format, rather than excluding the folder. For
  `pretty-format-json --indent=4 --no-ensure-ascii` (which sorts keys
  unless given `--no-sort-keys`), that's
  `json.dumps(obj, indent=4, sort_keys=True, ensure_ascii=False) + '\n'`.
  A test can run the real hook on the output with
  `pre_commit_hooks.pretty_format_json.main([...])`.

## ruff

- **`preview = true` in `[tool.ruff.format]` also formats Python code
  blocks in `.md` files.** A badly formatted example in a Markdown file
  fails `just check-format`.
- **Under `select = ["ALL"]`, tests need docstrings and `-> None` too.**
  Typical `tests/**` ignores: `INP001`, `PLR2004`, `S101`.
- **TC001–TC003** want imports that are only used in annotations moved
  under `if TYPE_CHECKING:`. On Python 3.14 annotations are evaluated
  lazily, so that's safe. Once the name is used at runtime as well, ruff
  wants the import back at the top.
- **Suppressing one rule on one line:** `# ruff: ignore[print]` names the
  rule instead of its code (`# noqa: T201`). With `select = ["ALL"]` and
  preview on, the `noqa-comments` rule flags every `# noqa:` and its fix
  rewrites it into the `# ruff: ignore[...]` form, so expect `just format`
  to do that.

## mypy and Pylance

- **A `[tool.pyright]` section in `pyproject.toml` (or a
  `pyrightconfig.json`) can override `python.analysis.typeCheckingMode`**
  from the VS Code settings, so the editor may not follow it. Set
  `typeCheckingMode = "strict"` in `pyproject.toml` itself. The Pylance
  docs don't say whether `diagnosticSeverityOverrides` is overridden too,
  or whether an empty section is enough to trigger this.
- **Third-party packages without type information (no `py.typed`):**
  prefer `[[tool.mypy.overrides]]` with `module = ["pkg.*"]` and
  `follow_untyped_imports = true` over `ignore_missing_imports`. You keep
  real types instead of `Any`.
- **`untyped_calls_exclude = ["pymatgen"]`** allows untyped calls into one
  library without turning the check off everywhere.

## Notebooks

- **nbstripout skips directories without a word.** `nbstripout
  notebooks/` exits 0 and strips nothing; it only acts on files (checked
  with 0.9.2). Expand directories first, e.g. `find notebooks/ -name
  '*.ipynb' -exec nbstripout {} +`. Run with no file at all, it waits for
  a notebook on stdin.
- **`nbstripout --verify`** changes nothing and exits 1 when it would
  strip something: the check-mode counterpart for a pre-push hook.
- **On WSL2, `jupyter lab` opens Windows Explorer instead of the
  browser** when `BROWSER=explorer.exe` (e.g. set in `~/.profile` for
  marimo). Jupyter doesn't hand the browser the URL but a redirect file,
  as `file:/home/...` (one slash), and `explorer.exe` can't resolve a
  Linux path. Don't work around it with `use_redirect_file = false`:
  that puts the token on the browser's command line, visible in process
  lists. Instead set `BROWSER=winbrowser`, a small wrapper on `PATH`
  (e.g. `~/.local/bin/winbrowser`) that converts `file:` URLs and plain
  paths with `wslpath -w` before calling `explorer.exe`:

  ```bash
  #!/usr/bin/env bash
  # Open URLs and local files in the default Windows browser from WSL.
  set -euo pipefail
  shopt -s extglob

  for arg in "$@"; do
      case "$arg" in
          file:*)
              # Jupyter passes file:/path, others file:///path: keep one slash.
              path="${arg#file:}"
              path="/${path##+(/)}"
              path="$(printf '%b' "${path//%/\\x}")"  # URL-decode, %20 -> space
              target="$(wslpath -w "$path")"
              ;;
          *://*) target="$arg" ;;
          *) target="$(wslpath -w "$arg")" ;;
      esac
      explorer.exe "$target" || true  # exits 1 even when it succeeds
  done
  ```

  `wslu`'s `wslview` does the same, but the project is archived and no
  longer maintained.

## pytest and mock

- **`assert mock.assert_called_once()` always fails.** The `assert_*`
  methods return `None`, so drop the `assert`. mypy reports it as
  `func-returns-value`.
- **Patch where the name is looked up,** not where it's defined:
  `monkeypatch.setattr('pkg.module.func', mock)`.
- **Use `create_autospec(SomeClass)` instead of `Mock()`** for
  third-party classes. A typo in a method name then raises
  `AttributeError`, and calls are checked against the real signatures.
  Without a spec, static tools see `mock.return_value` as `Any`, which is
  why the editor shows no highlighting after it.
- **Code under test that calls `load_dotenv(override=True)`:** mock
  `load_dotenv`. Otherwise the real `.env` overrides
  `monkeypatch.setenv`, the test behaves differently on each machine, and
  your real key can end up in failure output.
- **Plots:** call `matplotlib.use('Agg')` in `tests/conftest.py`, and
  patch `plt.show`. Under WSLg the default backend is TkAgg, because WSLg
  provides a display.
- **Fixtures that need a patch only while they set up:** use
  `with pytest.MonkeyPatch.context() as mp:`, so the patch is undone
  before the test runs.

## git and GitHub

- **Git doesn't record renames; it detects them,** by default at ≥50%
  similarity. If a file is moved *and* heavily changed on a branch, a
  squash merge puts both in one commit, which then looks like a delete
  plus an add, and `git log --follow` stops there. Either make a separate
  pure `git mv` commit and merge with a **merge commit**, or use
  `git log --follow -M40%` to follow the history past the move.
- **Merge commits need `required_linear_history` off** in the ruleset,
  and "merge" in `allowed_merge_methods`.
- **No hook checks merge or squash messages made on GitHub.** Set the
  title and body yourself, e.g.
  `gh pr merge N --merge --subject "..." --body-file msg.txt`.
- **`gh pr create --editor`:** the first line of the file becomes the PR
  title, the rest the body.
- **Rewording a pushed commit:** `git rebase -i` with "reword", then
  `git push --force-with-lease`. Every later commit gets a new ID. Make a
  backup branch first, and check that `git diff backup HEAD` is empty
  afterwards.

## uv

- **The `uv_build` range in `[build-system]`** (e.g. `<0.12`) makes
  `uv build` warn once uv is newer ("does not contain the current uv
  version"), and download that old `uv_build` instead of using the one
  built into uv. Raise both bounds, e.g. `uv_build>=0.13.9,<0.14`. In
  this repo, `tests/test_uv_build_pin.py` fails when that's due.
- **A newer uv bumps `revision` in `uv.lock`.** That's harmless, but it
  shows up in the next diff.
