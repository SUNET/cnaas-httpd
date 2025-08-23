# CNaaS-HTTPd

API that handles firmware images for [cnaas-nms](https://github.com/SUNET/cnaas-nms).

## Docker build

```bash
# Be at root of the repo
docker build -f docker/httpd/Dockerfile .
```


## Test

```bash
# Install dev dependencies
pip install -r requirements-dev.txt
# Run tests
pytest src/cnaas_httpd/tests
```