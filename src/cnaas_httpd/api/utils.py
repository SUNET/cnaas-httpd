import hashlib
import os
import re
import shutil
import ssl
import urllib.request

from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import HttpUrl

from cnaas_httpd.api.schemas import ErrorModel, ChecksumModel
from cnaas_httpd.constants import PATH


def compute_file_hash(file_path: str, algorithm: str = "sha512"):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def get_default_name(filename: str) -> str:
    # Extract base prefix and extension
    match = re.match(r"^([^.\\-]+)(?:[.-].*)?(\.[^.]+)$", filename)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid firmware filename format")

    prefix, ext = match.groups()
    link_name = f"{prefix}-stable{ext}"
    return link_name


def file_download(
    url: HttpUrl,
    filename: str,
    checksum: ChecksumModel,
    verify_tls: bool,
):
    path = PATH + filename
    try:
        if verify_tls is not None:
            context = ssl._create_unverified_context()
        else:
            context = None
        with (
            urllib.request.urlopen(str(url), timeout=120, context=context) as response,
            open(path, "wb") as out_file,
        ):
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_hash = compute_file_hash(path, checksum.algorithm)
    checksum_match = file_hash == checksum.checksum

    if not checksum_match:
        os.remove(path)
        raise HTTPException(status_code=400, detail="Checksum mismatch, file corrupt")
    return


def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    # Displays only one error at a time.
    first_error = next((error.get("msg") for error in exc.errors()), "Invalid request")

    error = ErrorModel(message=first_error)

    return JSONResponse(status_code=400, content=error.model_dump())


def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    error = ErrorModel(message=exc.detail)

    return JSONResponse(status_code=exc.status_code, content=error.model_dump())
