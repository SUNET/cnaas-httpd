import os

from cnaas_httpd.api import app


os.environ['PYTHONPATH'] = os.getcwd()


def get_app():
    return app.app


if __name__ == '__main__':
    get_app().run(debug=False, host='0.0.0.0', port=5000)
else:
    cnaas_app = get_app()
