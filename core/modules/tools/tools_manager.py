from core.loader import import_modules
from core.modules.tools.loader import load_tools
from core.modules.tools.base import Tool
from core.modules.tools.events import Event
from core.responses import ShortToolResponse


class _ToolsManager:
    def __init__(self, plugin_dir: str | None = None):
        self.functions = load_tools(import_modules(__file__, Tool))

    def send_event(self, event: Event, **kwargs):
        event_functions = self.functions.get(event, [])
        if event is Event.PROCESS_TRACK:
            processed_function = next(
                func
                for func in event_functions
                if func.__func_id__ == kwargs.pop("tool_func_id")
            )
            processed_function(**kwargs)
        else:
            for function in event_functions:
                function(**kwargs)

    def get_track_process_events(self) -> list[ShortToolResponse]:
        return [
            ShortToolResponse(tool_id=func.__func_id__, tool_name=func.__func_name__)
            for func in self.functions.get(Event.PROCESS_TRACK, [])
            if func.__func_name__ is not None
        ]


ToolsManager = _ToolsManager()
