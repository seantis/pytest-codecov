import importlib
import json

from coverage.misc import CoverageException
import pytest

import pytest_codecov
import pytest_codecov.codecov
import pytest_codecov.git

pytest_plugins = 'pytester'


@pytest.fixture
def no_gitpython(monkeypatch):
    monkeypatch.setattr('pytest_codecov.git.slug', None)
    monkeypatch.setattr('pytest_codecov.git.branch', None)
    monkeypatch.setattr('pytest_codecov.git.commit', None)
    monkeypatch.setattr(
        'pytest_codecov.git.ls_files',
        pytest_codecov.git.os_ls_files
    )


class DummyReporter:

    def __init__(self):
        self.lines = []

    def line(self, text=''):
        self.lines.append(text)

    def write_line(self, text='', **_):
        self.line(text)

    def section(self, title):
        self.line(f'###{title}###')

    def flush(self):
        self.lines = []

    @property
    def text(self):
        return '\n'.join(self.lines)


@pytest.fixture
def dummy_reporter():
    return DummyReporter()


class DummyCoverage:

    def xml_report(self, outfile):
        with open(outfile, 'w') as fp:
            fp.write('<dummy_report/>')


@pytest.fixture
def dummy_cov():
    return DummyCoverage()


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    # prevents tests from making live requests
    monkeypatch.delattr('requests.sessions.Session.request')


class MockResponse:

    def __init__(self, text='', ok=True):
        self.text = text
        self.ok = ok

    def json(self):
        return json.loads(self.text)


class MockRequests:

    def __init__(self) -> None:
        self._calls = []
        self._response = MockResponse()
        self.mock_connection_error = False

    def set_response(self, text, ok=True):
        self._response = MockResponse(text, ok=ok)

    def set_responses(self, *texts):
        assert texts
        self._response = [MockResponse(text) for text in texts]

    def pop(self):
        calls = self._calls
        self.clear()
        return calls

    def clear(self) -> None:
        self._calls = []

    def mock_method(self, method, url, **kwargs):
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
def mock_requests(monkeypatch):
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

    def __init__(self, factory, slug, **kwargs):
        self.factory = factory

    def add_network_files(self, files):
        pass

    def add_coverage_report(self, cov, **kwargs):
        if self.factory.fail_report_generation:
            raise CoverageException('test exception')

    def add_junit_xml(self, path):
        self.factory.junit_xml = path

    def get_payload(self):
        return 'stub'

    def ping(self):
        pass

    def upload(self):
        pass


class DummyUploaderFactory:

    def __init__(self):
        self.fail_report_generation = False
        self.junit_xml = None

    def __call__(self, slug, **kwargs):
        return DummyUploader(self, slug, **kwargs)

    def clear(self):
        self.junit_xml = None


@pytest.fixture
def dummy_uploader(monkeypatch):
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
importlib.reload(pytest_codecov.codecov)
