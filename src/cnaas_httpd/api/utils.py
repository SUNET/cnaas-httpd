import hashlib
import os
import shutil
import ssl
import urllib.request
from typing import Optional

from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import HttpUrl

from cnaas_httpd.api.schemas import ErrorModel
from cnaas_httpd.constants import PATH


def compute_file_hash(file_path: str, algorithm: str = "sha512"):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def file_download(
    url: HttpUrl,
    filename: str,
    sha1: str,
    sha512: str,
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
    if sha1 is not None: # use sha1 if defined
        file_hash = compute_file_hash(path, "sha1")
        checksum_match = file_hash == sha1
    else: # use 512
        file_hash = compute_file_hash(path, "sha512")
        checksum_match = file_hash == sha512

    if not checksum_match:
        os.remove(path)
        raise HTTPException(status_code=400, detail="Checksum mismatch, file corrupt")
    return


def validation_exception_handler(
    _, exc: RequestValidationError
) -> JSONResponse:
    # Displays only one error at a time.
    first_error = next((error.get("msg") for error in exc.errors()), "Invalid request")

    error = ErrorModel(message=first_error)

    return JSONResponse(status_code=400, content=error.model_dump())


def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    error = ErrorModel(message=exc.detail)

    return JSONResponse(status_code=exc.status_code, content=error.model_dump())
