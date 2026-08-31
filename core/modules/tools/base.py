from abc import ABC
from typing import ClassVar, Protocol, Any
from core.modules.tools.events import Event


class ToolFunction(Protocol):
    __name__: str

    __event_name__: Event
    __func_id__: str
    __func_name__: str | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


def event_listener(event: Event, name: str | None = None):
    def decorator(func: ToolFunction) -> ToolFunction:
        func.__event_name__ = event
        func.__func_id__ = func.__module__ + "." + func.__name__
        if name is not None:
            func.__func_name__ = name
        return func

    return decorator


class Tool(ABC):
    NAME: ClassVar[str]
