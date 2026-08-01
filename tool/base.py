from abc import ABC
from typing import ClassVar
from tool.events import Event


def event_listener(event: Event, name: str | None = None):
    def decorator(func):
        func.__event_name__ = event
        if name is not None:
            func.__func_name__ = name
        return func

    return decorator


class Tool(ABC):
    NAME: ClassVar[str]
