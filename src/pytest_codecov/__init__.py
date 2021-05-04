import argparse
import os
import pytest
import re

import pytest_codecov.git as git

from .codecov import CodecovError
from .codecov import CodecovUploader


__version__ = '0.1.0'
token_regex = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)
slug_regex = re.compile(
    r'^[0-9a-zA-Z-_]+/[0-9a-zA-Z-_]+$'
)


def validate_token(arg):
    if not token_regex.match(arg):
        msg = 'Invalid Codecov.io repository token supplied.'
        raise argparse.ArgumentTypeError(msg)
    return arg


def validate_slug(arg):
    if not slug_regex.match(arg):
        msg = 'Invalid repository slug supplied.'
        raise argparse.ArgumentTypeError(msg)
    return arg


def pytest_addoption(parser, pluginmanager):
    group = parser.getgroup('codecov')
    group.addoption(
        '--codecov',
        action='store_true',
        dest='codecov',
        default=False,
        help='Upload coverage results to codecov.io'
    )
    group.addoption(
        '--codecov-token',
        action='store',
        dest='codecov_token',
        default=os.environ.get('CODECOV_TOKEN'),
        metavar='TOKEN',
        type=validate_token,
        help='Set the codecov token for private repositories.'
    )
    group.addoption(
        '--codecov-slug',
        action='store',
        dest='codecov_slug',
        default=os.environ.get('CODECOV_SLUG', git.slug),
        metavar='SLUG',
        type=validate_slug,
        help='Set the git repository slug manually.'
    )
    group.addoption(
        '--codecov-branch',
        action='store',
        dest='codecov_branch',
        default=os.environ.get('CODECOV_BRANCH', git.branch),
        help='Set the git branch manually.'
    )
    group.addoption(
        '--codecov-commit',
        action='store',
        dest='codecov_commit',
        default=os.environ.get('CODECOV_COMMIT', git.commit),
        help='Set the git commit hash manually.'
    )
    group.addoption(
        '--codecov-dump',
        action='store_true',
        dest='codecov_dump',
        help='Dump codecov payload to terminal instead of uploading it'
    )

    parser.addini('codecov_token', 'Codecov token for private repositories.')
    parser.addini('codecov_slug', 'Codecov repository slug.')


class CodecovPlugin:

    @pytest.mark.trylast
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        cov_plugin = config.pluginmanager.get_plugin('_cov')
        if cov_plugin.cov_controller is None:
            return

        if cov_plugin.cov_total is None:
            return

        cov = cov_plugin.cov_controller.cov
        if cov is None:
            return

        uploader = CodecovUploader(
            config.option.codecov_slug,
            commit=config.option.codecov_commit,
            branch=config.option.codecov_branch,
            token=config.option.codecov_token,
        )
        uploader.add_coverage_report(cov)
        if config.option.codecov_dump:
            terminalreporter.section('Prepared Codecov.io payload')
            terminalreporter.write_line(uploader.get_payload())
            return

        terminalreporter.section('Codecov.io upload')

        if not config.option.codecov_slug:
            terminalreporter.write_line(
                'ERROR: Failed to determine git repository slug. '
                'Cannot upload without a valid slug.',
                red=True,
                bold=True,
            )
            terminalreporter.line('')
            return
        if not config.option.codecov_branch:
            terminalreporter.write_line(
                'WARNING: Failed to determine git repository branch.',
                yellow=True,
                bold=True,
            )
        if not config.option.codecov_commit:
            terminalreporter.write_line(
                'WARNING: Failed to determine git commit.',
                yellow=True,
                bold=True,
            )
        try:
            terminalreporter.write_line('Pinging codecov API...')
            uploader.ping()
            terminalreporter.line('')
            terminalreporter.write_line(
                'Uploading reports to storage endpoint...'
            )
            uploader.upload()
            terminalreporter.line('')
            terminalreporter.write_line(
                'Successfully queued reports for processing.',
                green=True
            )
            terminalreporter.line('')
        except CodecovError as error:
            terminalreporter.write_line(f'ERROR: {error}', red=True, bold=True)


def pytest_configure(config):
    # NOTE: if cov is missing we fail silently
    if config.option.codecov and config.pluginmanager.has_plugin('_cov'):
        config.pluginmanager.register(CodecovPlugin())
