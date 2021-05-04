import pytest

pytest_plugins = 'pytester'


class DummyCoverage:

    def xml_report(self, outfile):
        with open(outfile, 'w') as fp:
            fp.write('<dummy_report/>')


@pytest.fixture
def no_gitpython(monkeypatch):
    monkeypatch.setattr('pytest_codecov.git.slug', None)
    monkeypatch.setattr('pytest_codecov.git.branch', None)
    monkeypatch.setattr('pytest_codecov.git.commit', None)


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
