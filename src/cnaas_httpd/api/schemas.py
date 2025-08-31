import hashlib
import re
import warnings
from typing import Annotated, Any, Generic, List, Literal, Optional, Self, TypeVar

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


class ChecksumModel(BaseModel):
    algorithm: str
    checksum: str

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        v = v.lower()
        if v not in hashlib.algorithms_available:
            raise ValueError(
                f"Unsupported algorithm '{v}'. "
                f"Supported algorithms: {', '.join(sorted(hashlib.algorithms_available))}"
            )
        return v

    @model_validator(mode="after")
    def validate_algorithm_checksum_match(self: Self) -> Self:
        expected_len = None
        algo = self.algorithm.lower()

        # Try creating a hash object to dynamically get digest size
        try:
            hash_obj = hashlib.new(algo)
            expected_len = (
                hash_obj.digest_size * 2
            )  # hex string length = digest size * 2
        except ValueError:
            raise ValueError(f"Unsupported algorithm '{algo}'")

        # Validate checksum matches expected hex length
        if not re.fullmatch(rf"[a-fA-F0-9]{{{expected_len}}}", self.checksum):
            raise ValueError(
                f"Checksum must be a {expected_len}-character hex string for algorithm '{algo}'"
            )

        return self


class FirmwaresPostModel(BaseModel):
    url: Annotated[
        HttpUrl,
        Field(..., examples=["https://example.com/fw.bin"]),
    ]
    checksum: ChecksumModel
    verify_tls: Optional[bool] = False

    def __init__(self, **data):
        # Handle deprecated sha1 field
        # Convert to checksum field if sha1 is provided
        # Using sha1 will override checksum field if both are provided
        if "sha1" in data:
            warnings.warn(
                "Directly sending sha1 is deprecated, use the checksum field instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            sha1_checksum = data.pop("sha1")

            data["checksum"] = {"algorithm": "sha1", "checksum": sha1_checksum}
        super().__init__(**data)

    # Custom error message for missing fields
    @model_validator(mode="before")
    @classmethod
    def check_fields_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "url" not in data:
                raise ValueError("url must be specified")
            if "checksum" not in data:
                raise ValueError("Field: checksum must be specified")
        return data


class FirmwareFileModel(BaseModel):
    filename: str
    md5: str
    sha1: str
    sha256: str
    sha512: str
    default: Annotated[
        Optional[str], Field(description="Default file name if file is set as default")
    ] = None
    linked_to: Annotated[
        Optional[str], Field(description="Linked file name if file is a symlink")
    ] = None


class FirmwareGetModel(BaseModel):
    file: FirmwareFileModel
