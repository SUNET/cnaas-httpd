import io
import os
from unittest.mock import patch

from cnaas_httpd.api.utils import get_default_name

# ----------------------------
# Tests for FirmwareFetchApi
# ----------------------------


def test_get_firmware_list(client):
    """GET should list available firmware files"""

    response = client.get("/api/v1.0/firmware")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert sorted(data["data"]["files"]) == ["fw1.bin", "fw2.bin", "fw3.bin"]


def test_post_missing_url(client):
    """POST should fail if URL is missing"""
    response = client.post("/api/v1.0/firmware", json={"sha512": "abc"})
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "url must be specified" in data["message"]


def test_post_missing_checksum(client):
    """POST should fail if sha1 or sha512 is missing"""
    response = client.post(
        "/api/v1.0/firmware", json={"url": "http://example.com/fw.bin"}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "one of sha1 or sha512" in data["message"]


def test_post_wrong_sha1(client):
    """POST should fail if sha1 is the wrong format"""
    response = client.post(
        "/api/v1.0/firmware", json={"url": "http://example.com/fw.bin", "sha1": "wrong"}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "sha1 must be a 40-character hex string" in data["message"]


def test_post_wrong_sha512(client):
    """POST should fail if sha1 is the wrong format"""
    response = client.post(
        "/api/v1.0/firmware",
        json={"url": "http://example.com/fw.bin", "sha512": "wrong"},
    )
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "sha512 must be a 128-character hex string" in data["message"]


def test_post_invalid_url_parsing(client):
    """POST should fail on bad URL"""
    response = client.post(
        "/api/v1.0/firmware", json={"url": "http://", "sha512": "abc"}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "Input should be a valid URL" in data["message"]

    # No filename set
    response = client.post(
        "/api/v1.0/firmware", json={"url": "http://example.com", "sha512": "A" * 128}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "could not parse filename" in data["message"]


@patch("shutil.copyfileobj")
@patch("urllib.request.urlopen")
def test_post_successful_download(
    mock_urlopen, mock_copyfileobj, client, firmware_directory
):
    """POST should download, validate and succeed"""

    url = "http://example.com/fw.bin"
    content = b"fake data"
    checksum_sha1 = "e4af1d0a59733d47cb82e5e568303ee138d17feb"
    checksum_sha512 = "579cf3de3801730584cb77e5946767bf199742fd00b3b512b75bef99c9eeed702f719073082301a43b78b623d0080450ce0d68d16fc729ab47a0de15e205be86"

    mock_urlopen.return_value.__enter__.return_value = io.BytesIO(content)

    # Mock copyfileobj to write the fake content to file
    def fake_copy(src, dst):
        dst.write(content)

    mock_copyfileobj.side_effect = fake_copy

    # Test download using sha512
    response = client.post(
        "/api/v1.0/firmware",
        json={"url": url, "sha512": checksum_sha512, "verify_tls": None},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    # Verify the file really exists
    downloaded_file = firmware_directory / "fw.bin"
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == content

    # Test download using sha1
    response = client.post(
        "/api/v1.0/firmware",
        json={"url": url, "sha1": checksum_sha1, "verify_tls": None},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    # Verify the file really exists
    downloaded_file = firmware_directory / "fw.bin"
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == content


@patch("shutil.copyfileobj")
@patch("urllib.request.urlopen")
def test_post_checksum_mismatch(
    mock_urlopen, mock_copyfileobj, client, firmware_directory
):
    """POST should download, validate and succeed"""

    url = "http://example.com/fw.bin"
    content = b"fake data"

    checksum_sha1 = "A" * 40
    checksum_sha512 = "B" * 128

    mock_urlopen.return_value.__enter__.return_value = io.BytesIO(content)

    # Mock copyfileobj to write the fake content to file
    def fake_copy(src, dst):
        dst.write(content)

    mock_copyfileobj.side_effect = fake_copy

    # sha1 download fail
    response = client.post(
        "/api/v1.0/firmware",
        json={"url": url, "sha1": checksum_sha1, "verify_tls": False},
    )

    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "Checksum mismatch" in data["message"]
    downloaded_file = firmware_directory / "fw.bin"
    # File have not been downloaded
    assert not downloaded_file.exists()

    # sha512 download fail
    response = client.post(
        "/api/v1.0/firmware",
        json={"url": url, "sha512": checksum_sha512, "verify_tls": False},
    )

    data = response.json()

    assert response.status_code == 400
    assert data["status"] == "error"
    assert "Checksum mismatch" in data["message"]
    downloaded_file = firmware_directory / "fw.bin"
    # File have not been downloaded
    assert not downloaded_file.exists()


# ----------------------------
# Tests for FirmwareImageApi
# ----------------------------


def test_image_get_success(client):
    """GET single firmware image info"""

    response = client.get("/api/v1.0/firmware/fw1.bin")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    # sha1
    assert data["data"]["file"]["sha1"] == "6c6264482e9930da144bab69c1af3dcb13c37f85"
    # sha512
    assert (
        data["data"]["file"]["sha512"]
        == "84ff6e12461adace2b87e8e97186d9afab3d96e34f18fa34e52ebf5e1608b04d927a08142e4cee930a353f9c010e3e57cb5cbfbfe42c542f4a1baeea819c98ad"
    )
    # default = None
    assert not data["data"]["file"]["default"]


def test_image_get_not_found(client):
    """GET single firmware image info fails file missing"""

    response = client.get("/api/v1.0/firmware/missing.bin")
    data = response.json()
    assert response.status_code == 404
    assert data["status"] == "error"


def test_image_delete_success(client, firmware_directory):
    """DELETE should remove file successfully"""

    response = client.delete("/api/v1.0/firmware/fw2.bin")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    deleted_file = firmware_directory / "fw2.bin"
    # File have been downloaded
    assert not deleted_file.exists()


def test_image_delete_not_found(client):
    """DELETE should fail if file does not exist"""

    response = client.delete("/api/v1.0/firmware/missing.bin")
    data = response.json()
    assert response.status_code == 404
    assert data["status"] == "error"


def test_set_eos_default_firmware_symlink(client, firmware_directory):
    test1_file = firmware_directory / "EOS64-4.31.5M.swi"
    test1_file.write_text("fake firmware data")
    expected1_link = firmware_directory / "EOS64-stable.swi"

    response = client.post(f"/api/v1.0/firmware/{test1_file.name}/set-default")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert os.path.islink(expected1_link)
    assert os.readlink(expected1_link) == str(test1_file)

    # Do it again and make sure the symlink have moved to another file
    test2_file = firmware_directory / "EOS64-4.32.5M.swi"
    test2_file.write_text("fake firmware data")
    expected2_link = firmware_directory / "EOS64-stable.swi"

    response = client.post(f"/api/v1.0/firmware/{test2_file.name}/set-default")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert os.path.islink(expected2_link)
    assert os.readlink(expected2_link) == str(test2_file)


def test_set_ios_default_firmware_symlink(client, firmware_directory):
    test_file = firmware_directory / "cat9k_lite_iosxe.17.12.05.SPA.bin"
    test_file.write_text("fake firmware data")
    expected_link = firmware_directory / "cat9k_lite_iosxe-stable.bin"

    response = client.post(f"/api/v1.0/firmware/{test_file.name}/set-default")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert os.path.islink(expected_link)
    assert os.readlink(expected_link) == str(test_file)

    # GET the file from API and check default
    response = client.get("/api/v1.0/firmware/cat9k_lite_iosxe.17.12.05.SPA.bin")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["file"]["default"] == "cat9k_lite_iosxe-stable.bin"

    # GET the symlinked file from API and check default
    response = client.get("/api/v1.0/firmware/cat9k_lite_iosxe-stable.bin")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    # Should be None
    assert not data["data"]["file"]["default"]

def test_set_default_default_linked_to(client, firmware_directory):
    filename = "EOS-4.32.6.1M.swi"
    (firmware_directory / filename).write_text("fake firmware data")
    
    link_name = get_default_name(filename)
    
    assert link_name == "EOS-stable.swi"
    
    # Create the test symlink
    os.symlink((firmware_directory / filename), (firmware_directory / link_name))
    
    # GET the file from API and check default and linked_to
    response = client.get(f"/api/v1.0/firmware/{filename}")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["file"]["default"] == link_name
    # Should be None
    assert not data["data"]["file"]["linked_to"]

    # GET the symlinked file from API and check default and linked_to
    response = client.get(f"/api/v1.0/firmware/{link_name}")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    # Should be None
    assert not data["data"]["file"]["default"]
    assert data["data"]["file"]["linked_to"] == filename

def test_set_default_not_found(client, firmware_directory):
    response = client.post("/api/v1.0/firmware/notfoundfile.bin/set-default")
    data = response.json()

    assert response.status_code == 404
    assert data["status"] == "error"


def test_delete_firmware_symlink(client, firmware_directory):
    """Cannot delete a symlink file"""
    test_file = firmware_directory / "original.bin"
    test_file.write_text("")
    expected_link = firmware_directory / "symlink.bin"
    # Create temporary symlink
    os.symlink(test_file, expected_link)

    # Cannot delete file that is symlinked
    response = client.delete(f"/api/v1.0/firmware/{test_file.name}")
    data = response.json()
    assert response.status_code == 400
    assert data["status"] == "error"

    # Delete the symlink
    response = client.delete(f"/api/v1.0/firmware/{expected_link.name}")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"

    # Delete the test_file
    response = client.delete(f"/api/v1.0/firmware/{test_file.name}")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
