from core.loader import import_modules, load_tools
from tool.base import Tool, ToolFunction
from tool.events import Event
from core.schemas.schemas import ShortToolResponse


class ToolsManager:
    def __init__(self, plugin_dir: str | None = None):
        self.functions: dict[Event, list[ToolFunction]] = load_tools(
            import_modules("tool", Tool)
        )

    def send_event(self, event: Event, **kwargs):
        event_functions = self.functions.get(event, [])
        if event is Event.PROCESS_TRACK:
            processed_function = next(
                func
                for func in event_functions
                if func.__func_id__ == kwargs.get("tool_func_id")
            )
            processed_function(**kwargs)
        else:
            for function in event_functions:
                function(**kwargs)

    def get_track_process_events(self) -> list[ShortToolResponse]:
        return [
            ShortToolResponse(tool_id=func.__func_id__, tool_name=func.__event_name__)
            for func in self.functions.get(Event.PROCESS_TRACK, [])
            if func.__event_name__ is not None
        ]
