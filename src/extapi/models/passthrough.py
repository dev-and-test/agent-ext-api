from typing import Literal

from pydantic import BaseModel


class PassthroughRequest(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    path: str
    body: dict | None = None
    params: dict[str, str] | None = None
