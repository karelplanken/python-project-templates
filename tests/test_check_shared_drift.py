"""Tests for check_shared_drift.py's parsers and drift comparators."""

from pathlib import Path

import check_shared_drift as csd

# parse_justfile_recipes -----------------------------------------------------


def test_parse_justfile_recipes_extracts_name_and_body() -> None:
    """A recipe header and its indented body lines are captured together."""
    text = (
        'set dotenv-load := true\n'
        '\n'
        '# A comment above a recipe, ignored.\n'
        'install:\n'
        '    uv sync --all-extras --all-groups\n'
        '\n'
        'format *paths=".":\n'
        '    uv run --frozen ruff check --fix {{ paths }}\n'
        '    uv run --frozen ruff format {{ paths }}\n'
    )
    recipes = csd.parse_justfile_recipes(text)
    assert set(recipes) == {'install', 'format'}
    # Trailing blank line before the next recipe header is part of the body —
    # parse_justfile_recipes keeps blank lines until a non-indented line ends it.
    assert recipes['install'] == ['    uv sync --all-extras --all-groups', '']
    assert recipes['format'] == [
        '    uv run --frozen ruff check --fix {{ paths }}',
        '    uv run --frozen ruff format {{ paths }}',
    ]


def test_parse_justfile_recipes_ignores_set_and_comment_lines() -> None:
    """`set` statements and top-level comments never become recipe names."""
    text = (
        'set dotenv-load := true\n'
        '# top-level comment, not a recipe\n'
        'check:\n'
        '    echo ok\n'
    )
    recipes = csd.parse_justfile_recipes(text)
    assert list(recipes) == ['check']


# parse_prek_local_hooks -----------------------------------------------------


def test_parse_prek_local_hooks_only_keeps_system_language_hooks() -> None:
    """Only `[[repos.hooks]]` blocks with language = "system" are returned."""
    text = (
        '[[repos]]\n'
        'repo = "https://github.com/gitleaks/gitleaks"\n'
        'rev = "v8.30.1"\n'
        'hooks = [{ id = "gitleaks" }]\n'
        '\n'
        '[[repos]]\n'
        'repo = "local"\n'
        '\n'
        '[[repos.hooks]]\n'
        'id = "check-types"\n'
        'entry = "just check-types"\n'
        'language = "system"\n'
        'types = ["python"]\n'
        '\n'
        '[[repos.hooks]]\n'
        'id = "check-spelling"\n'
        'entry = "just check-spelling"\n'
        'language = "system"\n'
    )
    hooks = csd.parse_prek_local_hooks(text)
    assert hooks == {
        'check-types': 'just check-types',
        'check-spelling': 'just check-spelling',
    }
    assert 'gitleaks' not in hooks


# parse_toml_sections ---------------------------------------------------------


def test_parse_toml_sections_strips_trailing_comment_before_next_header() -> None:
    """A section's body must not swallow the next section's leading comment.

    Regression test for a real bug: the two sit between the same pair of
    [section] headers positionally, but the comment explains what comes
    *after* it, not what came before.
    """
    text = (
        '[tool.ruff.format]\n'
        'quote-style = "single"\n'
        '\n'
        '# mypy (type checking) -----------------------------------------\n'
        '[tool.mypy]\n'
        'strict = true\n'
    )
    names = ['[tool.ruff.format]', '[tool.mypy]']
    sections = csd.parse_toml_sections(text, names)
    assert (
        sections['[tool.ruff.format]'] == '[tool.ruff.format]\nquote-style = "single"'
    )
    assert sections['[tool.mypy]'] == '[tool.mypy]\nstrict = true'


def test_parse_toml_sections_ignores_unrequested_sections() -> None:
    """A section not in `names` is left out of the result entirely."""
    text = '[tool.a]\nx = 1\n\n[tool.b]\ny = 2\n'
    sections = csd.parse_toml_sections(text, ['[tool.a]'])
    assert list(sections) == ['[tool.a]']


# check_justfiles / check_prek / check_pyproject ------------------------------


def _make_shape(
    root: Path,
    name: str,
    *,
    justfile: str = '',
    prek: str = '',
    pyproject: str = '',
) -> Path:
    """Build a fake `<root>/<name>/template/` shape directory for tests.

    Returns:
        The shape's root directory.
    """
    shape = root / name
    template = shape / 'template'
    template.mkdir(parents=True)
    (template / 'justfile').write_text(justfile)
    (template / 'prek.toml.jinja').write_text(prek)
    (template / 'pyproject.toml.jinja').write_text(pyproject)
    return shape


def test_check_justfiles_flags_missing_and_differing_recipes(tmp_path: Path) -> None:
    """A missing recipe and a body mismatch are both reported."""
    other = _make_shape(tmp_path, 'other', justfile='present:\n    echo different\n')
    reference = {
        'present': ['    echo original'],
        'missing': ['    echo only-in-reference'],
    }
    problems = csd.check_justfiles([other], reference)
    assert any("missing recipe 'missing'" in p for p in problems)
    assert any("recipe 'present' body differs" in p for p in problems)


def test_check_justfiles_no_drift_when_recipes_match(tmp_path: Path) -> None:
    """Matching recipe names and bodies produce no problems."""
    other = _make_shape(tmp_path, 'other', justfile='present:\n    echo original\n')
    reference = {'present': ['    echo original']}
    assert csd.check_justfiles([other], reference) == []


def test_check_prek_flags_missing_and_differing_hooks(tmp_path: Path) -> None:
    """A missing hook and an entry mismatch are both reported."""
    prek = (
        '[[repos]]\n'
        'repo = "local"\n'
        '\n'
        '[[repos.hooks]]\n'
        'id = "check-types"\n'
        'entry = "just check-types-slow"\n'
        'language = "system"\n'
    )
    other = _make_shape(tmp_path, 'other', prek=prek)
    reference = {
        'check-types': 'just check-types',
        'check-spelling': 'just check-spelling',
    }
    problems = csd.check_prek([other], reference)
    assert any("missing local hook 'check-spelling'" in p for p in problems)
    assert any("hook 'check-types' entry differs" in p for p in problems)


def test_check_pyproject_flags_missing_and_differing_sections(tmp_path: Path) -> None:
    """A missing section and a body mismatch are both reported."""
    other = _make_shape(
        tmp_path, 'other', pyproject='[tool.codespell]\nskip = "*.venv"\n'
    )
    reference = {
        '[tool.codespell]': '[tool.codespell]\nskip = "*.lock,.venv"',
        '[tool.mypy]': '[tool.mypy]\nstrict = true',
    }
    problems = csd.check_pyproject([other], reference)
    assert any("missing section '[tool.mypy]'" in p for p in problems)
    assert any("section '[tool.codespell]' differs" in p for p in problems)


def test_checks_skip_the_reference_shape_itself(tmp_path: Path) -> None:
    """A shape named like REFERENCE_SHAPE is never checked against itself."""
    reference_shape = tmp_path / csd.REFERENCE_SHAPE
    (reference_shape / 'template').mkdir(parents=True)
    assert csd.check_justfiles([reference_shape], {'anything': ['body']}) == []
    assert csd.check_prek([reference_shape], {'hook': 'entry'}) == []
    assert csd.check_pyproject([reference_shape], {'[tool.x]': 'body'}) == []


# main --------------------------------------------------------------------------------


def test_main_reports_no_drift_against_the_real_repo() -> None:
    """The real shapes in this repo currently show no drift against library/."""
    assert csd.main() == 0
