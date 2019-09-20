from flask import Flask
from flask_restful import Api
from cnaas_httpd.api.fetch import FirmwareFetchApi, FirmwareImageApi
from cnaas_httpd.version import __api_version__

import os


app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = os.urandom(128)

api.add_resource(FirmwareFetchApi, f'/api/{ __api_version__ }/firmware')
api.add_resource(FirmwareImageApi, f'/api/{ __api_version__ }/firmware/<string:filename>')
