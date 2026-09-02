from core.modules.tools.base import ToolFunction, Tool
from core.modules.tools.events import Event
import inspect
from collections import defaultdict


def load_tools(modules: dict[str, type[Tool]]) -> dict[Event, list[ToolFunction]]:
    tools: defaultdict[Event, list[ToolFunction]] = defaultdict(list)
    for module in modules.values():
        tool_class = module()
        for _, method in inspect.getmembers(tool_class, inspect.ismethod):
            if hasattr(method, "__event_name__"):
                tools[method.__event_name__].append(method)
    return dict(tools)
