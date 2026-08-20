from dataclasses import dataclass


@dataclass(slots=True)
class BaseError:
    code: int
    detail: str


@dataclass(slots=True)
class NotFoundError(BaseError):
    code: int = 404
    detail: str = "Content not found"


@dataclass(slots=True)
class ForbiddenError(BaseError):
    code: int = 403
    detail: str = "Not permitted action"
