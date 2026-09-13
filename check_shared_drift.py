#!/usr/bin/env python3
"""Catches unintentional drift in tooling shared across the per-shape templates.

Repo-root meta-tooling — lives outside every <shape>/template/ dir, so it
never ships into a generated project. Copier's independent-per-shape design
means shared files (justfile, prek.toml.jinja, pyproject.toml.jinja) are
duplicated across shapes rather than composed from one source, so nothing
enforces they stay in sync except deliberately re-reading them. This script
is that check, run by hand (or in CI) against `library/`, the reference
shape all others were built from.

It does not require every shape's file to be byte-identical to library's —
a shape is allowed to add recipes/hooks/sections library doesn't have (e.g.
data-analysis's `clean-notebooks`). It only flags what library has that a
shape is *missing*, or where a shared name exists in both but its content
disagrees — that's the actual "someone changed one copy and forgot the
others" failure mode this guards against.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
REFERENCE_SHAPE = 'library'

# [tool.*] blocks expected byte-identical across every shape — these are
# "ported 1:1" from a shared source of truth, never meant to vary per shape.
INVARIANT_TOML_SECTIONS = [
    '[tool.ruff]',
    '[tool.ruff.lint]',
    '[tool.ruff.lint.pydocstyle]',
    '[tool.ruff.lint.isort]',
    '[tool.ruff.format]',
    '[tool.complexipy]',
    '[tool.codespell]',
]

RECIPE_HEADER_RE = re.compile(r'^([a-zA-Z_][\w-]*)\b[^:]*:')
HOOK_BLOCK_RE = re.compile(
    r'\[\[repos\.hooks\]\](.*?)(?=\[\[repos\.hooks\]\]|\Z)', re.DOTALL
)
HOOK_ID_RE = re.compile(r'id\s*=\s*"([^"]+)"')
HOOK_ENTRY_RE = re.compile(r'entry\s*=\s*"([^"]+)"')
SECTION_RE = re.compile(r'^\[[\w.]+\]\s*$', re.MULTILINE)


def find_shapes() -> list[Path]:
    """Find every shape directory (one per per-shape template) in the repo.

    Returns:
        Each shape's root directory, sorted by name.
    """
    return sorted(
        p.parent
        for p in REPO_ROOT.glob('*/copier.yml')
        if (p.parent / 'template').is_dir()
    )


def parse_justfile_recipes(text: str) -> dict[str, list[str]]:
    """Map recipe name -> its body lines (the indented block under it).

    Returns:
        Recipe name to its body lines.
    """
    lines = text.splitlines()
    recipes: dict[str, list[str]] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(('set ', '#', ' ', '\t')) or not line.strip():
            i += 1
            continue
        m = RECIPE_HEADER_RE.match(line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        body: list[str] = []
        i += 1
        while i < len(lines) and (
            lines[i].startswith((' ', '\t')) or not lines[i].strip()
        ):
            body.append(lines[i].rstrip())
            i += 1
        recipes[name] = body
    return recipes


def parse_prek_local_hooks(text: str) -> dict[str, str]:
    """Map local (delegated-to-just) hook id -> its entry command.

    Returns:
        Hook id to its `entry` command.
    """
    hooks: dict[str, str] = {}
    for block in HOOK_BLOCK_RE.findall(text):
        if 'language' not in block or '"system"' not in block:
            continue
        id_match = HOOK_ID_RE.search(block)
        entry_match = HOOK_ENTRY_RE.search(block)
        if id_match and entry_match:
            hooks[id_match.group(1)] = entry_match.group(1)
    return hooks


def parse_toml_sections(text: str, names: list[str]) -> dict[str, str]:
    """Map section header -> its raw body text, up to the next [section] or EOF.

    Trailing blank/comment lines are dropped from each captured block — those
    belong to whatever section comes *next* (a comment explaining it), not to
    this one, even though they sit between the two headers positionally.

    Returns:
        Section header to its body text.
    """
    sections: dict[str, str] = {}
    headers = [(m.start(), m.group().strip()) for m in SECTION_RE.finditer(text)]
    for idx, (start, header) in enumerate(headers):
        if header not in names:
            continue
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(text)
        lines = text[start:end].strip('\n').splitlines()
        while len(lines) > 1 and (
            not lines[-1].strip() or lines[-1].lstrip().startswith('#')
        ):
            lines.pop()
        sections[header] = '\n'.join(lines).strip()
    return sections


def check_justfiles(shapes: list[Path], reference: dict[str, list[str]]) -> list[str]:
    """Flag any shape justfile missing (or disagreeing with) a reference recipe.

    Returns:
        One human-readable problem string per drift found.
    """
    problems: list[str] = []
    for shape in shapes:
        if shape.name == REFERENCE_SHAPE:
            continue
        justfile = shape / 'template' / 'justfile'
        if not justfile.exists():
            problems.append(f'{shape.name}: no justfile found')
            continue
        recipes = parse_justfile_recipes(justfile.read_text())
        for name, body in reference.items():
            if name not in recipes:
                problems.append(f"{shape.name}/justfile: missing recipe '{name}'")
            elif recipes[name] != body:
                problems.append(
                    f"{shape.name}/justfile: recipe '{name}' body differs "
                    f'from {REFERENCE_SHAPE}'
                )
    return problems


def check_prek(shapes: list[Path], reference: dict[str, str]) -> list[str]:
    """Flag any shape prek.toml.jinja missing (or disagreeing with) a reference hook.

    Returns:
        One human-readable problem string per drift found.
    """
    problems: list[str] = []
    for shape in shapes:
        if shape.name == REFERENCE_SHAPE:
            continue
        prek_file = shape / 'template' / 'prek.toml.jinja'
        if not prek_file.exists():
            problems.append(f'{shape.name}: no prek.toml.jinja found')
            continue
        hooks = parse_prek_local_hooks(prek_file.read_text())
        for hook_id, entry in reference.items():
            if hook_id not in hooks:
                problems.append(
                    f"{shape.name}/prek.toml.jinja: missing local hook '{hook_id}'"
                )
            elif hooks[hook_id] != entry:
                problems.append(
                    f"{shape.name}/prek.toml.jinja: hook '{hook_id}' entry differs "
                    f"('{hooks[hook_id]}' vs '{entry}')"
                )
    return problems


def check_pyproject(shapes: list[Path], reference: dict[str, str]) -> list[str]:
    """Flag any shape pyproject.toml.jinja missing (or disagreeing with) a section.

    Returns:
        One human-readable problem string per drift found.
    """
    problems: list[str] = []
    for shape in shapes:
        if shape.name == REFERENCE_SHAPE:
            continue
        pyproject = shape / 'template' / 'pyproject.toml.jinja'
        if not pyproject.exists():
            problems.append(f'{shape.name}: no pyproject.toml.jinja found')
            continue
        sections = parse_toml_sections(pyproject.read_text(), INVARIANT_TOML_SECTIONS)
        for name, body in reference.items():
            if name not in sections:
                problems.append(
                    f"{shape.name}/pyproject.toml.jinja: missing section '{name}'"
                )
            elif sections[name] != body:
                problems.append(
                    f"{shape.name}/pyproject.toml.jinja: section '{name}' "
                    f'differs from {REFERENCE_SHAPE}'
                )
    return problems


def main() -> int:
    """Compare every shape's shared tooling files against the reference shape.

    Returns:
        0 if no drift was found, 1 if drift was found, 2 if the reference
        shape itself is missing.
    """
    shapes = find_shapes()
    reference_dir = REPO_ROOT / REFERENCE_SHAPE
    if not (reference_dir / 'template').is_dir():
        print(f"Reference shape '{REFERENCE_SHAPE}' not found at {reference_dir}")
        return 2

    reference_template = reference_dir / 'template'
    reference_recipes = parse_justfile_recipes(
        (reference_template / 'justfile').read_text()
    )
    reference_hooks = parse_prek_local_hooks(
        (reference_template / 'prek.toml.jinja').read_text()
    )
    reference_sections = parse_toml_sections(
        (reference_template / 'pyproject.toml.jinja').read_text(),
        INVARIANT_TOML_SECTIONS,
    )

    problems = [
        *check_justfiles(shapes, reference_recipes),
        *check_prek(shapes, reference_hooks),
        *check_pyproject(shapes, reference_sections),
    ]

    if problems:
        print(f"Drift found against '{REFERENCE_SHAPE}' ({len(problems)}):")
        for p in problems:
            print(f'  - {p}')
        return 1

    print(f"No drift — {len(shapes) - 1} shape(s) checked against '{REFERENCE_SHAPE}'.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
