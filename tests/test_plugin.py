import pytest

from pytest import UsageError
from pytest_codecov import CodecovPlugin


def test_options(pytester, no_gitpython):
    config = pytester.parseconfig('')
    assert config.option.codecov is False
    assert config.option.codecov_token is None
    assert config.option.codecov_slug is None
    assert config.option.codecov_branch is None
    assert config.option.codecov_commit is None
    assert config.option.codecov_dump is False
    assert config.option.codecov_upload_on_failure is True

    config = pytester.parseconfig('--codecov')
    assert config.option.codecov is True
    assert config.option.codecov_token is None
    assert config.option.codecov_slug is None
    assert config.option.codecov_branch is None
    assert config.option.codecov_commit is None
    assert config.option.codecov_dump is False
    assert config.option.codecov_upload_on_failure is True

    config = pytester.parseconfig(
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=seantis/pytest_codecov',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef',
        '--codecov-dump',
        '--no-codecov-on-failure'
    )
    assert config.option.codecov is True
    assert (
        config.option.codecov_token == '12345678-1234-1234-1234-1234567890ab'
    )
    assert config.option.codecov_slug == 'seantis/pytest_codecov'
    assert config.option.codecov_branch == 'master'
    assert config.option.codecov_commit == 'deadbeef'
    assert config.option.codecov_dump is True
    assert config.option.codecov_upload_on_failure is False


def test_options_invalid_token(pytester, no_gitpython):
    with pytest.raises(UsageError, match=r'Invalid.* token'):
        pytester.parseconfig('--codecov', '--codecov-token=invalid')


def test_options_invalid_slug(pytester, no_gitpython):
    with pytest.raises(UsageError, match=r'Invalid.* slug'):
        pytester.parseconfig('--codecov', '--codecov-slug=invalid')


def test_upload_report_no_slug(pytester, dummy_reporter, dummy_uploader,
                               dummy_cov, no_gitpython):
    config = pytester.parseconfig('--codecov')
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert len(dummy_reporter.lines) == 3
    assert 'Failed to determine git repository slug.' in dummy_reporter.text


def test_upload_report_no_branch(pytester, dummy_reporter, dummy_uploader,
                                 dummy_cov, no_gitpython):
    config = pytester.parseconfig(
        '--codecov',
        '--codecov-slug=foo/bar',
        '--codecov-commit=deadbeef'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert 'Failed to determine git repository branch.' in dummy_reporter.text


def test_upload_report_no_commit(pytester, dummy_reporter, dummy_uploader,
                                 dummy_cov, no_gitpython):
    config = pytester.parseconfig(
        '--codecov',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert 'Failed to determine git commit.' in dummy_reporter.text


def test_upload_report_dump(pytester, dummy_reporter, dummy_uploader,
                            dummy_cov, no_gitpython):
    config = pytester.parseconfig('--codecov', '--codecov-dump')
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert 'Prepared Codecov.io payload' in dummy_reporter.text


def test_upload_report(pytester, dummy_reporter, dummy_uploader,
                       dummy_cov, no_gitpython):
    config = pytester.parseconfig(
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert (
        'Environment:\n'
        'Slug:   foo/bar\n'
        'Branch: master\n'
        'Commit: deadbeef\n'
    ) in dummy_reporter.text


def test_upload_report_junit(pytester, dummy_reporter, dummy_uploader,
                             dummy_cov, no_gitpython, tmp_path):

    # create a junit xml
    junit_xml = tmp_path / 'junit.xml'
    junit_xml.write_text('foo')
    config = pytester.parseconfig(
        f'--junit-xml={junit_xml}',
        '-o',
        'junit_family=legacy',
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert (
        'Environment:\n'
        'Slug:   foo/bar\n'
        'Branch: master\n'
        'Commit: deadbeef\n'
        '\n'
        'JUnit XML file detected and included in upload.\n'
    ) in dummy_reporter.text
    assert (
        'INFO: We recommend using junit_family=legacy with Codecov.'
    ) not in dummy_reporter.text
    assert dummy_uploader.junit_xml == str(junit_xml)


def test_upload_report_junit_info(pytester, dummy_reporter, dummy_uploader,
                                  dummy_cov, no_gitpython, tmp_path):

    # create a junit xml
    junit_xml = tmp_path / 'junit.xml'
    junit_xml.write_text('foo')
    config = pytester.parseconfig(
        f'--junit-xml={junit_xml}',
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert (
        'INFO: We recommend using junit_family=legacy with Codecov.\n'
        'Environment:\n'
        'Slug:   foo/bar\n'
        'Branch: master\n'
        'Commit: deadbeef\n'
        '\n'
        'JUnit XML file detected and included in upload.\n'
    ) in dummy_reporter.text
    assert dummy_uploader.junit_xml == str(junit_xml)


def test_no_upload_report_junit(pytester, dummy_reporter, dummy_uploader,
                                dummy_cov, no_gitpython, tmp_path):

    # create a junit xml
    junit_xml = tmp_path / 'junit.xml'
    junit_xml.write_text('foo')
    config = pytester.parseconfig(
        f'--junit-xml={junit_xml}',
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef',
        '--codecov-exclude-junit-xml'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert (
        'Environment:\n'
        'Slug:   foo/bar\n'
        'Branch: master\n'
        'Commit: deadbeef\n'
    ) in dummy_reporter.text
    assert (
        'JUnit XML file detected and included in upload.'
    ) not in dummy_reporter.text
    assert (
        'INFO: We recommend using junit_family=legacy with Codecov.'
    ) not in dummy_reporter.text
    assert dummy_uploader.junit_xml is None


def test_upload_report_generation_failure(
    pytester, dummy_reporter, dummy_uploader,
    dummy_cov, no_gitpython
):
    dummy_uploader.fail_report_generation = True
    config = pytester.parseconfig(
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=foo/bar',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef'
    )
    plugin = CodecovPlugin()
    plugin.upload_report(dummy_reporter, config, dummy_cov)
    assert (
        'ERROR: Failed to generate XML report: test exception'
    ) in dummy_reporter.text
