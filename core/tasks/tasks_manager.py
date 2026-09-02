from core.errors import NotFoundError, BaseError
from concurrent.futures import ThreadPoolExecutor
from typing import Literal
from uuid import uuid4
from core.tasks.schemas import TaskStorage, Task

QueueName = Literal["download", "sync", "importing"]


class _TasksManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.task_queue: TaskStorage = TaskStorage()

    def post_task(
        self, func, queue_name: QueueName, task_id: str | None = None, *args, **kwargs
    ) -> str:
        task_id = str(uuid4())[:8] if task_id is None else task_id
        task_body = self.executor.submit(func, task_id, *args, **kwargs)
        target = getattr(self.task_queue, queue_name)
        target[task_id] = Task(task=task_body)
        return task_id

    def cancel_task(self, queue_name: QueueName, task_id) -> bool | BaseError:
        queue = getattr(self.task_queue, queue_name)
        task: Task | None = queue.get(task_id)
        if task is None:
            return NotFoundError()
        return task.task.cancel()

    def get_task[T](self, queue_name: QueueName, task_id) -> Task[T] | BaseError:
        queue = getattr(self.task_queue, queue_name)
        task = queue.get(task_id, NotFoundError())
        return task


TasksManager = _TasksManager()
