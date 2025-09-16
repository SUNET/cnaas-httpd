from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from cnaas_httpd.main import app


@pytest.fixture(scope="session")
def firmware_directory(tmp_path_factory):
    """Create a shared firmware directory for all tests."""
    firmware_dir = tmp_path_factory.mktemp("firmware")
    (firmware_dir / "fw1.bin").write_text("some-fake-data-1")
    (firmware_dir / "fw2.bin").write_text("some-fake-data-2")
    (firmware_dir / "fw3.bin").write_text("some-fake-data-3")
    # Add symlink to test-data
    (firmware_dir / "fw1-stable.bin").symlink_to((firmware_dir / "fw1.bin"))
    return firmware_dir


@pytest.fixture(autouse=True)
def patch_firmware_path(firmware_directory):
    """Patch the global PATH so all tests use the same temp firmware_directory."""
    patched_path = str(firmware_directory) + "/"
    with (
        patch("cnaas_httpd.api.firmware.PATH", patched_path),
        patch("cnaas_httpd.api.utils.PATH", patched_path),
    ):
        yield


@pytest.fixture
def client():
    return TestClient(app)
