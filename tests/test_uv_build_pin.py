"""Guards the shapes' `uv_build` pin against falling behind the local uv.

`uv build` only uses the backend built into uv when uv's version is inside
the `requires` range; otherwise it quietly downloads an older `uv_build`.
These tests turn the next uv minor release into a failing test instead.
"""

import re
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import]
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PIN_RE = re.compile(r'"uv_build>=(?P<lower>[\d.]+),<(?P<upper>[\d.]+)"')
# Every shape with a build backend; `scripts` is flat and has none.
SHAPES_WITH_BACKEND = {'app', 'data-analysis', 'library', 'multi-subpackage', 'web-app'}


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split('.'))


def _pins() -> dict[str, tuple[str, str]]:
    """Map shape name -> its (lower, upper) `uv_build` bounds.

    Returns:
        Shape name to the bounds in its `pyproject.toml.jinja`.
    """
    pins: dict[str, tuple[str, str]] = {}
    for pyproject in REPO_ROOT.glob('*/template/pyproject.toml.jinja'):
        match = PIN_RE.search(pyproject.read_text())
        if match:
            pins[pyproject.parent.parent.name] = (match['lower'], match['upper'])
    return pins


def test_every_shape_with_a_backend_pins_the_same_range() -> None:
    """The five shapes with a build backend all pin one identical range."""
    pins = _pins()
    assert set(pins) == SHAPES_WITH_BACKEND
    assert len(set(pins.values())) == 1, pins


def test_local_uv_is_inside_the_pinned_range() -> None:
    """The local uv falls inside the range, so builds use its built-in backend."""
    uv = shutil.which('uv')
    if uv is None:
        pytest.skip('uv is not on PATH')
    # Fixed argv, no shell: nothing untrusted reaches the command.
    output = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [uv, '--version'], capture_output=True, text=True, check=True
    ).stdout
    local = output.split()[1]  # "uv 0.13.9 (...)" -> "0.13.9"
    lower, upper = next(iter(_pins().values()))
    assert _version(local) < _version(upper), (
        f'uv {local} is past the uv_build pin <{upper}: raise both bounds in '
        'every shape, e.g. uv_build>=<uv version>,<0.<minor + 1>'
    )
    assert _version(local) >= _version(lower), (
        f'uv {local} is older than the uv_build pin >={lower}'
    )
