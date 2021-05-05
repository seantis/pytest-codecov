import pytest

from pytest_codecov.codecov import CodecovError
from pytest_codecov.codecov import CodecovUploader


def test_init():
    uploader = CodecovUploader('seantis/pytest-codecov')
    assert uploader.slug == 'seantis/pytest-codecov'
    assert uploader.commit is None
    assert uploader.branch is None
    assert uploader.token is None
    assert uploader.get_payload() == '<<<<<< network'


def test_add_coverage_report(dummy_cov):
    uploader = CodecovUploader('seantis/pytest-codecov')
    uploader.add_coverage_report(dummy_cov)
    assert uploader.get_payload() == (
        '<<<<<< network\n'
        '# path=./coverage.xml\n'
        '<dummy_report/>\n'
        '<<<<<< EOF'
    )

    uploader.add_coverage_report(dummy_cov, filename='coverage_2.xml')
    assert uploader.get_payload() == (
        '<<<<<< network\n'
        '# path=./coverage.xml\n'
        '<dummy_report/>\n'
        '<<<<<< EOF\n'
        '# path=./coverage_2.xml\n'
        '<dummy_report/>\n'
        '<<<<<< EOF'
    )


def test_ping(dummy_cov, mock_requests):
    mock_requests.set_response('Invalid response')
    uploader = CodecovUploader('seantis/pytest-codecov')
    with pytest.raises(CodecovError, match=r'Invalid response'):
        uploader.ping()

    mock_requests.set_response(f'codecov.io\n{uploader.storage_endpoint}')
    uploader.ping()
    assert uploader.store_url == uploader.storage_endpoint

    # TODO: Verify correct url/headers/params


def test_ping_no_slug(dummy_cov, mock_requests):
    uploader = CodecovUploader(None)
    with pytest.raises(CodecovError, match=r'valid slug'):
        uploader.ping()


def test_upload(dummy_cov, mock_requests):
    uploader = CodecovUploader('seantis/pytest-codecov')
    with pytest.raises(CodecovError, match=r'Need to ping API before upload'):
        uploader.upload()

    mock_requests.set_response(f'codecov.io\n{uploader.storage_endpoint}')
    uploader.ping()

    mock_requests.set_response('', ok=False)
    with pytest.raises(CodecovError, match='Failed to upload report'):
        uploader.upload()

    mock_requests.set_response('')
    uploader.upload()
    assert uploader.store_url is None

    # TODO: Verify correct url/headers/params
