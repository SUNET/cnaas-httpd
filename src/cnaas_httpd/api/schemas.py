import re
from typing import Annotated, Any, Generic, List, Literal, Optional, TypeVar

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

T = TypeVar("T")


class ErrorModel(BaseModel):
    status: Literal["error"] = "error"
    message: str


class GenericResponseModel(BaseModel, Generic[T]):
    status: Literal["success"] = "success"
    data: Optional[T] = None


class FirmwaresGetModel(BaseModel):
    files: Optional[List] = []


class FirmwaresPostModel(BaseModel):
    url: Annotated[
        HttpUrl,
        Field(..., examples=["https://example.com/fw.bin"]),
    ]
    sha1: Optional[str] = None
    sha512: Optional[str] = None
    verify_tls: Optional[bool] = False

    # Custom error message for missing fields
    @model_validator(mode="before")
    @classmethod
    def check_fields_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "url" not in data:
                raise ValueError("url must be specified")
        return data

    @field_validator("sha1")
    @classmethod
    def validate_sha1(cls, v):
        if not re.fullmatch(r"[a-fA-F0-9]{40}", v):
            raise ValueError("sha1 must be a 40-character hex string")
        return v

    # validate sha512 value if provided
    @field_validator("sha512")
    @classmethod
    def validate_sha512(cls, v):
        if not re.fullmatch(r"[a-fA-F0-9]{128}", v):
            raise ValueError("sha512 must be a 128-character hex string")
        return v

    @model_validator(mode="after")
    def check_exclusive_sha(self):
        if bool(self.sha1) == bool(self.sha512):  # both None or both set
            raise ValueError("You must provide exactly one of sha1 or sha512")
        return self


class FirmwareFileModel(BaseModel):
    filename: str
    sha1: str
    sha512: str
    default: Optional[str] = None


class FirmwareGetModel(BaseModel):
    file: FirmwareFileModel
