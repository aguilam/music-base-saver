from core.modules.tools.base import Tool, event_listener
from core.modules.tools.events import Event
from structlog import get_logger
from structlog.stdlib import BoundLogger
from core.schemas.schemas import Track


class LoggerTool(Tool):
    NAME = "LoggerTool"

    def __init__(self):
        self.logger: BoundLogger = get_logger(__name__)

    @event_listener(Event.NEW_COVER)
    def log_new_cover(self, cover):
        self.logger.info(f"new cover - path: {cover['path']}")

    @event_listener(Event.NEW_TRACK)
    def log_new_track(self, track: Track):
        self.logger.info(f"new track - id: {track.id} title: {track.title}")

    @event_listener(Event.PROCESS_TRACK, "Log this track")
    def log_track(self, track: Track):
        self.logger.info(f"Track - id: {track.id} title: {track.title}")
