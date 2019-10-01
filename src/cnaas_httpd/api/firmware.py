import os
import ssl
import shutil
import urllib.request

from flask import request
from flask_restful import Resource
from cnaas_httpd.api.generic import empty_result
from hashlib import sha1


PATH = '/opt/cnaas/www/firmware/'


def file_sha1(fname):
    hash_sha1 = sha1()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


def error(errstr):
    return empty_result(status='error', data=errstr), 404


class FirmwareFetchApi(Resource):
    def url_parse(self, url):
        parsed = urllib.parse.urlparse(url)
        return parsed.path.split('/')[-1]

    def files_get(self):
        return os.listdir(PATH)

    def file_download(self, url, checksum, filename, verify_tls=None):
        path = PATH + filename
        try:
            if verify_tls is not None:
                context = ssl._create_unverified_context()
            else:
                context = None
            with urllib.request.urlopen(url, timeout=120, context=context) as response, open(path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            return str(e)
        sha1 = file_sha1(path)
        if sha1 != checksum:
            os.remove(path)
            return 'Checksum mismatch, file corrupt'
        return ''

    def post(self):
        json_data = request.get_json()

        if 'url' not in json_data:
            return error('URL must be specified')
        if 'sha1' not in json_data:
            return error('Checksum must be specified')
        if 'verify_tls' not in json_data:
            json_data['verify_tls'] = None

        filename = self.url_parse(json_data['url'])
        if filename == '':
            return error('Invalid URL, could not parse filename')
        res = self.file_download(json_data['url'], json_data['sha1'],
                                 filename, json_data['verify_tls'])
        if res != '':
            return error(res)
        return empty_result(status='success')

    def get(self):
        files = self.files_get()
        data = {'files': files}
        return empty_result(status='success', data=data)


class FirmwareImageApi(Resource):
    def get(self, filename):
        path = PATH + filename
        try:
            sha1 = file_sha1(path)
        except Exception:
            return error('Could not find file ' + filename)
        res = {'file': {'filename': filename,
                        'sha1': sha1}}
        return empty_result(status='success', data=res)

    def delete(self, filename):
        path = PATH + filename
        try:
            os.remove(path)
        except Exception:
            return error('Could not remove file ' + filename)
        return empty_result(status='success')
