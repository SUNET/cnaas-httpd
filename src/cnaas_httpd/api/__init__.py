from fastapi import APIRouter

from cnaas_httpd.api.firmware import router as firmware_router
from cnaas_httpd.constants import __api_version__

router = APIRouter(prefix=f"/api/{__api_version__}")

router.include_router(firmware_router)
