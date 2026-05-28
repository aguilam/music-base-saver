from tool.base import Tool
from structlog import get_logger
from structlog.stdlib import BoundLogger


class LoggerTool(Tool):
    NAME = "LoggerTool"

    def __init__(self):
        self.logger: BoundLogger = get_logger(__name__)

    def METHODS(self):
        return {
            "ON_NEW_COVER": self.log_new_cover,
        }

    def log_new_cover(self, cover):
        self.logger.info(cover["path"])
