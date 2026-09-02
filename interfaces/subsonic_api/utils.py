from fastapi import Request, Depends, HTTPException
from typing import Annotated, NoReturn, TypeVar, Any, Sequence
from core.library_manager import LibraryManager
from core.errors import BaseError

T = TypeVar("T")


class SubsonicException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


opensubsonic_error = {
    0: "A generic error.",
    10: "Required parameter is missing.",
    20: "Incompatible Subsonic REST protocol version. Client must upgrade.",
    40: "Wrong username or password.",
    42: "Provided authentication mechanism not supported.",
    43: "Multiple conflicting authentication mechanisms provided.",
    44: "Invalid API key.",
    50: "User is not authorized for the given operation.",
    70: "The requested data was not found.",
}
server_to_subsonic_errors = {404: 70, 403: 50, 401: 40, 422: 10}


def check_subsonic_error[T](result: T | BaseError) -> T:
    if isinstance(result, BaseError):
        code = server_to_subsonic_errors.get(result.code, 0)
        message = opensubsonic_error.get(code, "Error")
        raise SubsonicException(code, message)
    return result


def raise_subsonic_error(code: int) -> NoReturn:
    message = opensubsonic_error.get(code, "Error")
    raise SubsonicException(code, message)


def get_library_manager(request: Request) -> "LibraryManager":
    return request.app.state.library_manager


CurrentLibrary = Annotated["LibraryManager", Depends(get_library_manager)]


def to_camel(response: dict[str, Any]) -> dict[str, Any]:
    camel_response = {}
    for key, value in response.items():
        snaked = key.split("_")
        new_value = value
        snaked = [k.capitalize() if i > 0 else k for i, k in enumerate(snaked)]
        new_key = "".join(snaked)
        if isinstance(value, dict):
            new_value = to_camel(value)
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            new_value = [to_camel(item) for item in value]
        camel_response[new_key] = new_value
    return camel_response


def check_result(result: T | BaseError) -> T:
    if isinstance(result, BaseError):
        raise HTTPException(status_code=result.code, detail=result.detail)
    return result
