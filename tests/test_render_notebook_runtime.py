"""Renders the data-analysis shape once per `notebook_runtime` choice.

Its `pyproject.toml` and file list depend on that answer, and a blank line
in a list or a `just lab` recipe without JupyterLab only shows up in the
rendered output, never in the `.jinja` source.
"""

import tomllib
import warnings
from pathlib import Path

import copier
import pytest

REPO_ROOT = Path(__file__).parent.parent

EXPECTED_NOTEBOOK_GROUP = {
    'ipykernel': ['ipykernel'],
    'jupyterlab': ['jupyterlab', 'jupyterlab-lsp'],
    'both': ['ipykernel', 'jupyterlab', 'jupyterlab-lsp'],
    'none': None,
}
JUPYTERLAB_ONLY_FILES = ('jupyter_server_config.json', 'lab.just')


@pytest.fixture(scope='module', params=sorted(EXPECTED_NOTEBOOK_GROUP))
def rendered(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[str, Path]:
    """Render data-analysis with one `notebook_runtime` into a temp dir.

    Returns:
        The runtime and the directory the project was rendered into.
    """
    runtime: str = request.param
    destination = tmp_path_factory.mktemp(f'render-{runtime}')
    with warnings.catch_warnings():
        # Rendering from a working tree with uncommitted changes is the point
        # while editing a template; copier warns about it each time.
        warnings.simplefilter('ignore', copier.errors.DirtyLocalWarning)
        copier.run_copy(
            str(REPO_ROOT),
            destination,
            data={
                'project_shape': 'data-analysis',
                'project_name': 'render-test',
                'author_name': 'Test Author',
                'notebook_runtime': runtime,
            },
            defaults=True,
            vcs_ref='HEAD',
            quiet=True,
        )
    return runtime, destination


def test_pyproject_parses_without_blank_lines_in_arrays(
    rendered: tuple[str, Path],
) -> None:
    """The rendered pyproject.toml is valid TOML with no empty array lines."""
    _, destination = rendered
    text = (destination / 'pyproject.toml').read_text()
    tomllib.loads(text)
    in_array = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.endswith('= ['):
            in_array = True
        elif stripped.startswith(']'):
            in_array = False
        elif in_array:
            assert stripped, f'blank line {number} inside an array'


def test_notebook_group_holds_the_runtime_packages(
    rendered: tuple[str, Path],
) -> None:
    """The `notebook` group lists exactly the runtime's packages, or is absent."""
    runtime, destination = rendered
    config = tomllib.loads((destination / 'pyproject.toml').read_text())
    groups = config['dependency-groups']
    expected = EXPECTED_NOTEBOOK_GROUP[runtime]
    if expected is None:
        assert 'notebook' not in groups
        assert 'default-groups' not in config.get('tool', {}).get('uv', {})
    else:
        assert groups['notebook'] == expected
        assert config['tool']['uv']['default-groups'] == ['dev', 'notebook']
    assert not set(groups['dev']) & {'ipykernel', 'jupyterlab', 'jupyterlab-lsp'}


def test_jupyterlab_files_ship_only_with_jupyterlab(
    rendered: tuple[str, Path],
) -> None:
    """The JupyterLab config and `lab.just` exist only for jupyterlab/both."""
    runtime, destination = rendered
    wanted = runtime in {'jupyterlab', 'both'}
    for name in JUPYTERLAB_ONLY_FILES:
        assert (destination / name).exists() == wanted, name
