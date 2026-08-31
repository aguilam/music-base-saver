from typing import cast, Any
from sqlalchemy.orm import InstrumentedAttribute


def in_load_typing(value) -> InstrumentedAttribute[Any]:
    return cast(InstrumentedAttribute[Any], value)
