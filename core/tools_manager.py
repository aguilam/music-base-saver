from typing import Callable, Any
from core.loader import import_modules, load_tools
from tool.base import Tool


class ToolsManager:
    def __init__(self, plugin_dir: str):
        self.functions: dict[str, list[Callable[..., Any]]] = load_tools(
            import_modules("tool", Tool)
        )

    def send_event(self, event: str, **kwargs):
        for function in self.functions.get(event, []):
            function(**kwargs)
