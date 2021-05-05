import gzip
import io
import requests
import tempfile
from urllib.parse import urljoin


def package():
    from pytest_codecov import __version__ as version
    return f'pytest_codecov-{version}'


class CodecovError(Exception):
    pass


class CodecovUploader:
    api_endpoint = 'https://codecov.io'
    storage_endpoint = 'https://storage.googleapis.com/codecov/'

    def __init__(self, slug, commit=None, branch=None, token=None):
        self.slug = slug
        self.commit = commit
        self.branch = branch
        self.token = token
        self.store_url = None
        self._buffer = io.StringIO()

    def write_network_files(self, files):
        self._buffer.write(
            '\n'.join(files + ['<<<<<< network'])
        )

    def add_coverage_report(self, cov, filename='coverage.xml', **kwargs):
        with tempfile.NamedTemporaryFile(mode='r') as xml_report:
            # embed xml report
            self._buffer.write(f'\n# path=./{filename}\n')
            cov.xml_report(outfile=xml_report.name)
            xml_report.seek(0)
            self._buffer.write(xml_report.read())
            self._buffer.write('\n<<<<<< EOF')

    def get_payload(self):
        return self._buffer.getvalue()

    def ping(self):
        if not self.slug:
            raise CodecovError(
                'Failed to determine git repository slug. '
                'Cannot upload without a valid slug.'
            )
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
            raise CodecovError(
                f'Invalid response from codecov API:\n{response.text}'
            )
        self.store_url = lines[1]

    def upload(self):
        if not self.store_url:
            raise CodecovError('Need to ping API before upload.')

        headers = {
            'Content-Type': 'application/x-gzip',
            'Content-Encoding': 'gzip',
        }
        gz_payload = io.BytesIO()
        with gzip.open(gz_payload, 'wb', 9) as payload:
            payload.write(self.get_payload().encode('utf-8'))
        gz_payload.seek(0)
        response = requests.put(
            self.store_url, headers=headers, data=gz_payload
        )

        if not response.ok:
            raise CodecovError('Failed to upload report to storage endpoint.')

        self.store_url = None  # NOTE: Invalidate store url after upload
