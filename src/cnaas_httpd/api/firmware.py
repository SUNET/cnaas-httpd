import os

from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from cnaas_httpd.api.schemas import (
    FirmwareGetModel,
    FirmwaresGetModel,
    FirmwaresPostModel,
    GenericResponseModel,
)
from cnaas_httpd.api.utils import compute_file_hash, file_download, get_default_name
from cnaas_httpd.constants import PATH

router = APIRouter(tags=["firmware"])


@router.get("/firmware")
async def firmwares_get() -> GenericResponseModel[FirmwaresGetModel]:
    """List all firmwares"""
    files = os.listdir(PATH)
    defaults = []
    for file in files:
        # Skip non symlinks
        full_path = os.path.join(PATH, file)
        if not os.path.islink(full_path):
            continue
        real_file_name = os.path.basename(os.path.realpath(full_path))
        # If it is a symlink add to defaults
        defaults.append({"file": real_file_name, "default": file})
    return {"data": {"files": files, "defaults": defaults}}


@router.post("/firmware")
async def firmwares_post(body: FirmwaresPostModel) -> GenericResponseModel[None]:
    """Download firmware image"""
    filename = body.url.path.split("/")[-1]

    if filename == "":
        raise HTTPException(
            status_code=400, detail="Invalid URL, could not parse filename"
        )

    try:
        file_download(body.url, filename, body.checksum, body.verify_tls)
    except Exception:
        raise  # re-raise the same exception

    return {}


@router.get("/firmware/{filename}")
async def firmware_get(filename: str) -> GenericResponseModel[FirmwareGetModel]:
    """Get firmware image"""
    file_data = {"filename": filename}
    path = PATH + filename
    real_path = os.path.realpath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    try:
        file_data["md5"] = compute_file_hash(real_path, "md5")
        file_data["sha1"] = compute_file_hash(real_path, "sha1")
        file_data["sha256"] = compute_file_hash(real_path, "sha256")
        file_data["sha512"] = compute_file_hash(real_path, "sha512")
    except Exception:
        raise HTTPException(
            status_code=500, detail=f"Could not extract checksum from file: {filename}"
        )

    return {"data": {"file": file_data}}


@router.delete("/firmware/{filename}")
async def firmware_delete(filename: str) -> GenericResponseModel:
    """Delete firmware image"""
    path = PATH + filename
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    # Check if a symlink is assigned to the file
    for entry in os.listdir(PATH):
        full_path = os.path.join(PATH, entry)
        if os.path.islink(full_path) and os.path.realpath(full_path) == path:
            raise HTTPException(
                status_code=400,
                detail=f"File: {filename} is symlinked to {entry}, delete the symlink first.",
            )
    try:
        os.remove(path)
        # Clear cache incase another file with the same name is downloaded but with another hash.
        compute_file_hash.cache_clear()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not remove file {filename}: {e}"
        )
    return {}


@router.post("/firmware/{filename}/set-default")
async def firmware_set_stable(filename: str) -> GenericResponseModel:
    """
    Set the given firmware as the default/stable image.
    Automatically generates a symlink like "prefix-stable.ext".
    """
    src_path = os.path.join(PATH, filename)

    if not os.path.exists(src_path):
        raise HTTPException(
            status_code=404, detail=f"Firmware image not found: {filename}"
        )

    try:
        link_name = get_default_name(filename)
    except Exception:
        raise
    link_path = os.path.join(PATH, link_name)

    try:
        # Remove old symlink/file if it exists
        if os.path.exists(link_path) or os.path.islink(link_path):
            os.remove(link_path)

        # Create new symlink
        os.symlink(src_path, link_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not set default firmware symlink: {e}"
        )

    return {}
