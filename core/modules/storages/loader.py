from core.loader import ModuleEntry
from typing import Any
from core.schemas import ServiceStatus, HealthStatus
from core.modules.storages.base import Storage
from dataclasses import dataclass


@dataclass(slots=True)
class StorageEntry(ModuleEntry[Storage]):
    id: str
    name: str


def load_storages(
    config: dict, storage_classes: dict[str, Any]
) -> tuple[list[StorageEntry], list[ServiceStatus]]:
    storages: dict = config.get("storage", {})
    active_storages: list[StorageEntry] = []
    errors = []
    for storage in storages:
        try:
            if storage.get("enabled", True):
                storage_tag = storage["tag"]
                instance_params = storage["params"]
                instance_params["id"] = storage["id"]
                instance_params["name"] = storage["name"]
                selected_storage = storage_classes[storage_tag]
                active_storages.append(
                    StorageEntry(
                        id=storage["id"],
                        name=storage["name"],
                        tag=storage_tag,
                        priority=storage["priority"],
                        params=storage["params"],
                        instance=selected_storage(instance_params),
                    )
                )
        except Exception as e:
            errors.append(
                ServiceStatus(
                    tag=storage.get("id", "Undefined"),
                    health=HealthStatus(ok=False, message=str(e)),
                )
            )
    active_storages.sort(key=lambda x: x.priority, reverse=True)
    return active_storages, errors
