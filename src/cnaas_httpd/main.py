from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

from cnaas_httpd.api import router as api_router
from cnaas_httpd.api.schemas import ErrorModel
from cnaas_httpd.api.utils import http_exception_handler, validation_exception_handler
from cnaas_httpd.constants import __version__

app = FastAPI(
    title=__name__,
    version=__version__,
    exception_handlers={
        RequestValidationError: validation_exception_handler,
        HTTPException: http_exception_handler,
    },
    responses={
        400: {
            "description": "Bad Request",
            "model": ErrorModel,
        },
        404: {
            "description": "Not Found",
            "model": ErrorModel,
        },
    },
)


app.include_router(api_router)
