import pytest
import pytest_codecov
import pytest_codecov.codecov

from importlib import reload

pytest_plugins = 'pytester'


@pytest.fixture
def no_gitpython(monkeypatch):
    monkeypatch.setattr('pytest_codecov.git.slug', None)
    monkeypatch.setattr('pytest_codecov.git.branch', None)
    monkeypatch.setattr('pytest_codecov.git.commit', None)


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


class MockRequests:

    def __init__(self) -> None:
        self._calls = []
        self._response = MockResponse()
        self.mock_connection_error = False

    def set_response(self, text, ok=True):
        self._response = MockResponse(text, ok=ok)

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

    def __init__(self, slug, **kwargs):
        pass

    def add_coverage_report(self, cov, **kwargs):
        pass

    def get_payload(self):
        return 'stub'

    def ping(self):
        pass

    def upload(self):
        pass


@pytest.fixture
def dummy_uploader(monkeypatch):
    monkeypatch.setattr(
        'pytest_codecov.codecov.CodecovUploader',
        DummyUploader
    )


# NOTE: Ensure modules are reloaded when coverage.py is looking.
#       This means we want to avoid importing module members when
#       using these modules, to ensure they get reloaded as well.
reload(pytest_codecov)
reload(pytest_codecov.codecov)
