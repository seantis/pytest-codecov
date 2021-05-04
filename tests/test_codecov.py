def test_options(testdir, no_gitpython):
    config = testdir.parseconfig('')
    assert config.option.codecov is False
    assert config.option.codecov_token is None
    assert config.option.codecov_slug is None
    assert config.option.codecov_branch is None
    assert config.option.codecov_commit is None
    assert config.option.codecov_dump is False

    config = testdir.parseconfig('--codecov')
    assert config.option.codecov is True
    assert config.option.codecov_token is None
    assert config.option.codecov_slug is None
    assert config.option.codecov_branch is None
    assert config.option.codecov_commit is None
    assert config.option.codecov_dump is False

    config = testdir.parseconfig(
        '--codecov',
        '--codecov-token=12345678-1234-1234-1234-1234567890ab',
        '--codecov-slug=seantis/pytest_codecov',
        '--codecov-branch=master',
        '--codecov-commit=deadbeef',
        '--codecov-dump'
    )
    assert config.option.codecov is True
    assert (
        config.option.codecov_token == '12345678-1234-1234-1234-1234567890ab'
    )
    assert config.option.codecov_slug == 'seantis/pytest_codecov'
    assert config.option.codecov_branch == 'master'
    assert config.option.codecov_commit == 'deadbeef'
    assert config.option.codecov_dump is True
