from fastapi import Request, Depends
from typing import Annotated, NoReturn
from core.library_manager import LibraryManager


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


def raise_subsonic_error(code: int) -> NoReturn:
    message = opensubsonic_error.get(code, "Error")
    raise SubsonicException(code, message)


def get_library_manager(request: Request) -> "LibraryManager":
    return request.app.state.library_manager


CurrentLibrary = Annotated["LibraryManager", Depends(get_library_manager)]
