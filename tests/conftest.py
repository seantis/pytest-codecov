from __future__ import annotations

import importlib
import json
from typing import Any
from typing import TYPE_CHECKING

import pytest
from coverage.exceptions import CoverageException

import pytest_codecov
import pytest_codecov.codecov
import pytest_codecov.git

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

    from coverage import Coverage

    Reporter = pytest.TerminalReporter
else:
    # NOTE: pretend our dummy objects inherit from the real thing
    Coverage = object
    Reporter = object

pytest_plugins = 'pytester'


@pytest.fixture
def no_gitpython(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('pytest_codecov.git.slug', None)
    monkeypatch.setattr('pytest_codecov.git.branch', None)
    monkeypatch.setattr('pytest_codecov.git.commit', None)
    monkeypatch.setattr(
        'pytest_codecov.git.ls_files',
        pytest_codecov.git.os_ls_files  # type: ignore[attr-defined]
    )


class DummyReporter(Reporter):  # type: ignore[misc]

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, msg: str = '', **kw: bool) -> None:
        self.lines.append(msg)

    def write_line(self, line: str | bytes = '', **_: object) -> None:
        if isinstance(line, bytes):
            line = line.decode()
        self.line(line)

    def section(self, title: str, sep: str = '', **kw: bool) -> None:
        self.line(f'###{title}###')

    def flush(self) -> None:
        self.lines = []

    @property
    def text(self) -> str:
        return '\n'.join(self.lines)


@pytest.fixture
def dummy_reporter() -> DummyReporter:
    return DummyReporter()


class DummyCoverage(Coverage):

    def xml_report(self, outfile: StrOrBytesPath) -> None:  # type: ignore[override]
        with open(outfile, 'w') as fp:
            fp.write('<dummy_report/>')


@pytest.fixture
def dummy_cov() -> DummyCoverage:
    return DummyCoverage()


@pytest.fixture(autouse=True)
def no_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    # prevents tests from making live requests
    monkeypatch.delattr('requests.sessions.Session.request')


class MockResponse:

    def __init__(self, text: str = '', ok: bool = True) -> None:
        self.text = text
        self.ok = ok

    def json(self) -> Any:
        return json.loads(self.text)


class MockRequests:

    _calls: list[tuple[str, str, dict[str, Any]]]
    _response: MockResponse | list[MockResponse]

    def __init__(self) -> None:
        self._calls = []
        self._response = MockResponse()
        self.mock_connection_error = False

    def set_response(self, text: str, ok: bool = True) -> None:
        self._response = MockResponse(text, ok=ok)

    def set_responses(self, *texts: str) -> None:
        assert texts
        self._response = [MockResponse(text) for text in texts]

    def pop(self) -> list[tuple[str, str, dict[str, Any]]]:
        calls = self._calls
        self.clear()
        return calls

    def clear(self) -> None:
        self._calls = []

    def mock_method(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> MockResponse:

        if self.mock_connection_error:
            raise ConnectionError()

        self._calls.append((method.lower(), url, kwargs))
        if isinstance(self._response, list):
            response = self._response.pop(0)
            if not self._response:
                # repeat the final response indefinitely
                self._response = response
            return response
        return self._response


@pytest.fixture
def mock_requests(monkeypatch: pytest.MonkeyPatch) -> MockRequests:
    monkeypatch.undo()
    mock_requests = MockRequests()
    monkeypatch.setattr(
        'requests.sessions.Session.request',
        mock_requests.mock_method
    )
    return mock_requests


class DummyUploader:
    # TODO: Implement some basic behavior, so we can test
    #       more exhaustively.

    def __init__(
        self,
        factory: DummyUploaderFactory,
        slug: str,
        **kwargs: object
    ) -> None:
        self.factory = factory

    def add_network_files(self, files: list[str]) -> None:
        pass

    def add_coverage_report(self, cov: object) -> None:
        if self.factory.fail_report_generation:
            raise CoverageException('test exception')

    def add_junit_xml(self, path: StrOrBytesPath) -> None:
        self.factory.junit_xml = path

    def get_payload(self) -> str:
        return 'stub'

    def ping(self) -> None:
        pass

    def upload(self) -> None:
        pass


class DummyUploaderFactory:

    def __init__(self) -> None:
        self.fail_report_generation = False
        self.junit_xml: StrOrBytesPath | None = None

    def __call__(self, slug: str, **kwargs: object) -> DummyUploader:
        return DummyUploader(self, slug, **kwargs)

    def clear(self) -> None:
        self.junit_xml = None


@pytest.fixture
def dummy_uploader(monkeypatch: pytest.MonkeyPatch) -> DummyUploaderFactory:
    factory = DummyUploaderFactory()
    monkeypatch.setattr(
        'pytest_codecov.codecov.CodecovUploader',
        factory
    )
    return factory


# NOTE: Ensure modules are reloaded when coverage.py is looking.
#       This means we want to avoid importing module members when
#       using these modules, to ensure they get reloaded as well.
importlib.reload(pytest_codecov)
importlib.reload(pytest_codecov.codecov)  # type: ignore[attr-defined]
