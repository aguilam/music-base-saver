from typing import TypeVar, Callable
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


@dataclass(slots=True)
class UnprocessableDataError(BaseError):
    code: int = 422
    detail: str = "Not enought data or invalid data types"


T = TypeVar("T")

U = TypeVar("U")


def check_error(result: T | BaseError, func: Callable[..., U]) -> U | BaseError:
    if isinstance(result, BaseError):
        return result
    return func(result)
