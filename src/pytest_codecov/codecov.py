import gzip
import io
import requests
import tempfile
from urllib.parse import urljoin


def package():
    from pytest_codecov import __version__ as version
    return f'pytest_codecov-{version}'


class CodecovUploader:
    api_endpoint = 'https://codecov.io'
    storage_endpoint = 'https://storage.googleapis.com/codecov/'

    def __init__(self, reporter, slug, commit=None, branch=None, token=None):
        self.reporter = reporter
        self.slug = slug
        self.commit = commit
        self.branch = branch
        self.token = token
        self._buffer = io.StringIO()
        # network preamble
        self._buffer.write('<<<<<< network\n')

    def add_coverage_report(self, cov, filename='coverage.xml', **kwargs):
        with tempfile.NamedTemporaryFile(mode='r') as xml_report:
            # embed xml report
            self._buffer.write(f'# path=./{filename}\n')
            cov.xml_report(outfile=xml_report.name)
            xml_report.seek(0)
            self._buffer.write(xml_report.read())
            self._buffer.write('\n<<<<<< EOF')

    def get_payload(self):
        return self._buffer.getvalue()

    def upload(self):
        self.reporter.section('Codecov.io upload')
        if not self.slug:
            self.reporter.write_line(
                'ERROR: Failed to determine git repository slug. '
                'Cannot upload without a valid slug.',
                red=True,
                bold=True,
            )
            self.reporter.line('')
            return
        if not self.branch:
            self.reporter.write_line(
                'WARNING: Failed to determine git repository branch.',
                yellow=True,
                bold=True,
            )
        if not self.branch:
            self.reporter.write_line(
                'WARNING: Failed to determine git commit.',
                yellow=True,
                bold=True,
            )
        self.reporter.write_line(f'Slug:   {self.slug}')
        self.reporter.write_line(f'Commit: {self.commit}')
        self.reporter.write_line(f'Branch: {self.branch}')

        # retrieve storage url from API
        self.reporter.line('')
        self.reporter.write_line('Pinging codecov API.')
        api_url = urljoin(self.api_endpoint, '/upload/v4')
        headers = {
            'X-Reduced-Redundancy': 'false',
            'X-Content-Type': 'application/x-gzip',
            'Content-Length': '0',
        }
        params = {
            'package': package(),
            'token': self.token or '',
            'branch': self.branch or '',
            'commit': self.commit or '',
            'build': '',  # TODO: support builds?
            'build_url': '',
            'name': '',
            'tag': '',  # TODO: support tags?
            'slug': self.slug,
            'service': '',
            'flags': '',  # TODO: support flags?
            'pr': '',  # TODO: support pull requests?
            'job': '',
            'cmd_args': '',
        }
        response = requests.post(api_url, headers=headers, params=params)
        lines = response.text.splitlines()
        if len(lines) != 2 or not lines[1].startswith(self.storage_endpoint):
            self.reporter.write_line(
                f'ERROR: Invalid response from codecov API:\n{response.text}',
                red=True,
                bold=True,
            )
            self.reporter.line('')
            return

        # upload file to retrieved storage url
        store_url = lines[1]
        self.reporter.line('')
        self.reporter.write_line(f'Uploading report to {store_url}.')
        headers = {
            'Content-Type': 'application/x-gzip',
            'Content-Encoding': 'gzip',
        }
        gz_payload = io.BytesIO()
        with gzip.open(gz_payload, 'wb', 9) as payload:
            payload.write(self.get_payload().encode('utf-8'))
        gz_payload.seek(0)
        requests.put(store_url, headers=headers, data=gz_payload)

        self.reporter.line('')
        self.reporter.write_line(f'Uploading report to {store_url}.')
        if not response.ok:
            self.reporter.write_line(
                'ERROR: Failed to upload report to storage endpoint.',
                red=True,
                bold=True,
            )
            self.reporter.line('')
            return

        self.reporter.write_line(
            'Successfully queued reports for processing.',
            green=True
        )
        self.reporter.line('')
