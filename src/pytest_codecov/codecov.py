import gzip
import io
import json
import requests
import tempfile
import zlib
from base64 import b64encode
from urllib.parse import urljoin


def package():
    from pytest_codecov import __version__ as version
    return f'pytest_codecov-{version}'


class CodecovError(Exception):
    pass


class CodecovUploader:
    api_endpoint = 'https://codecov.io'
    storage_endpoint = 'https://storage.googleapis.com/codecov-production/'

    def __init__(self, slug, commit=None, branch=None, token=None):
        self.slug = slug
        self.commit = commit
        self.branch = branch
        self.token = token
        self._coverage_store_url = None
        self._coverage_buffer = io.StringIO()
        self._test_result_store_url = None
        self._test_result_files = []

    def add_network_files(self, files):
        self._coverage_buffer.write(
            '\n'.join(files + ['<<<<<< network'])
        )

    def add_coverage_report(self, cov, filename='coverage.xml', **kwargs):
        with tempfile.NamedTemporaryFile(mode='r') as xml_report:
            # embed xml report
            self._coverage_buffer.write(f'\n# path=./{filename}\n')
            cov.xml_report(outfile=xml_report.name)
            xml_report.seek(0)
            self._coverage_buffer.write(xml_report.read())
            self._coverage_buffer.write('\n<<<<<< EOF')

    def add_junit_xml(self, path, filename='junit.xml'):
        with open(path, 'rb') as junit_xml:
            self._test_result_files.append({
                'filename': filename,
                'format': 'base64+compressed',
                'data': b64encode(
                    zlib.compress(junit_xml.read())
                ).decode('ascii'),
                'labels': '',
            })

    def get_payload(self):
        return self._coverage_buffer.getvalue()

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
        self._coverage_store_url = lines[1]

        if not self._test_result_files:
            return

        headers = {} if self.token is None else {
            'Authorization': f'token {self.token}',
            'User-Agent': package()
        }
        data = {
            'slug': self.slug,
            'branch': self.branch or '',
            'commit': self.commit or '',
        }
        api_url = urljoin(self.api_endpoint, '/upload/test_results/v1')
        response = requests.post(api_url, headers=headers, json=data)
        if response.ok:
            # TODO: Fail more loudly?
            url = response.json()['raw_upload_location']
            if url.startswith(self.storage_endpoint):
                self._test_result_store_url = url

    def upload(self):
        if not self._coverage_store_url:
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
            self._coverage_store_url, headers=headers, data=gz_payload
        )

        if not response.ok:
            raise CodecovError('Failed to upload report to storage endpoint.')

        self._coverage_store_url = None

        if not self._test_result_store_url or not self._test_result_files:
            return

        json_payload = json.dumps({
            'test_results_files': self._test_result_files
        }).encode('ascii')
        # TODO: Fail more loudly?
        requests.put(self._test_result_store_url, data=json_payload)
        self._test_result_store_url = None
