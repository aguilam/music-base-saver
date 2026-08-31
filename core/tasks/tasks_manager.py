from core.tasks.schemas import TaskStorage
from concurrent.futures import ThreadPoolExecutor


class _TasksManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.task_queue: TaskStorage = TaskStorage()


TasksManager = _TasksManager()
