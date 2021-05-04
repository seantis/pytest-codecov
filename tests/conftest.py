import pytest

import pytest_codecov.git as git

pytest_plugins = 'pytester'


@pytest.fixture
def no_gitpython(monkeypatch):
    monkeypatch.setattr(git, 'slug', None)
    monkeypatch.setattr(git, 'branch', None)
    monkeypatch.setattr(git, 'commit', None)
