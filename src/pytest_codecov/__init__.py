import argparse
import os
import pytest
import re

import pytest_codecov.git as git
import pytest_codecov.codecov as codecov


__version__ = '0.7.0'
token_regex = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)
slug_regex = re.compile(
    r'^[0-9a-zA-Z_.-]+/[0-9a-zA-Z_.-]+$'
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
        default=os.environ.get('CODECOV_TOKEN') or None,
        metavar='TOKEN',
        type=validate_token,
        help='Set the codecov token for private repositories.'
    )
    group.addoption(
        '--codecov-slug',
        action='store',
        dest='codecov_slug',
        default=os.environ.get('CODECOV_SLUG') or git.slug,
        metavar='SLUG',
        type=validate_slug,
        help='Set the git repository slug manually.'
    )
    group.addoption(
        '--codecov-branch',
        action='store',
        dest='codecov_branch',
        default=os.environ.get('CODECOV_BRANCH') or git.branch,
        help='Set the git branch manually.'
    )
    group.addoption(
        '--codecov-commit',
        action='store',
        dest='codecov_commit',
        default=os.environ.get('CODECOV_COMMIT') or git.commit,
        help='Set the git commit hash manually.'
    )
    group.addoption(
        '--codecov-dump',
        action='store_true',
        dest='codecov_dump',
        default=False,
        help='Dump codecov payload to terminal instead of uploading it'
    )
    group.addoption(
        '--no-codecov-on-failure',
        action='store_false',
        dest='codecov_upload_on_failure',
        default=True,
        help='Don\'t upload coverage results on test failure'
    )
    group.addoption(
        '--codecov-exclude-junit-xml',
        action='store_false',
        dest='codecov_junit_xml',
        default=True,
        help='Don\'t upload the junit xml file'
    )


class CodecovPlugin:

    def upload_report(self, terminalreporter, config, cov):
        option = config.option
        uploader = codecov.CodecovUploader(
            option.codecov_slug,
            commit=option.codecov_commit,
            branch=option.codecov_branch,
            token=option.codecov_token,
        )
        uploader.add_network_files(git.ls_files())
        from coverage.misc import CoverageException
        try:
            uploader.add_coverage_report(cov)
        except CoverageException as exc:
            terminalreporter.section('Codecov.io payload')
            terminalreporter.write_line(
                f'ERROR: Failed to generate XML report: {exc}',
                red=True,
                bold=True,
            )
            terminalreporter.line('')
            return

        xmlpath = option.xmlpath if option.codecov_junit_xml else None
        if xmlpath and os.path.isfile(xmlpath):
            uploader.add_junit_xml(xmlpath)
            has_junit_xml = True
        else:
            has_junit_xml = False

        if option.codecov_dump:
            terminalreporter.section('Prepared Codecov.io payload')
            terminalreporter.write_line(uploader.get_payload())
            return

        terminalreporter.section('Codecov.io upload')

        if not option.codecov_slug:
            terminalreporter.write_line(
                'ERROR: Failed to determine git repository slug. '
                'Cannot upload without a valid slug.',
                red=True,
                bold=True,
            )
            terminalreporter.line('')
            return
        if not option.codecov_branch:
            terminalreporter.write_line(
                'WARNING: Failed to determine git repository branch.',
                yellow=True,
                bold=True,
            )
        if not option.codecov_commit:
            terminalreporter.write_line(
                'WARNING: Failed to determine git commit.',
                yellow=True,
                bold=True,
            )
        if has_junit_xml and config.getini('junit_family') != 'legacy':
            terminalreporter.write_line(
                'INFO: We recommend using junit_family=legacy with Codecov.',
                blue=True,
                bold=True,
            )

        terminalreporter.write_line(
            'Environment:\n'
            f'Slug:   {option.codecov_slug}\n'
            f'Branch: {option.codecov_branch}\n'
            f'Commit: {option.codecov_commit}\n'
        )
        if has_junit_xml:
            terminalreporter.write_line(
                'JUnit XML file detected and included in upload.\n'
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
        except codecov.CodecovError as error:
            terminalreporter.write_line(f'ERROR: {error}', red=True, bold=True)

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        cov_plugin = config.pluginmanager.get_plugin('_cov')
        if cov_plugin.cov_controller is None:
            return

        cov = cov_plugin.cov_controller.cov
        if cov is None:
            return

        if exitstatus != 0 and not config.option.codecov_upload_on_failure:
            return

        self.upload_report(terminalreporter, config, cov)


def pytest_configure(config):  # pragma: no cover
    # NOTE: Don't report codecov results on worker nodes
    if hasattr(config, 'workerinput'):
        return

    # NOTE: if cov is missing we fail silently
    if config.option.codecov and config.pluginmanager.has_plugin('_cov'):
        config.pluginmanager.register(CodecovPlugin())
