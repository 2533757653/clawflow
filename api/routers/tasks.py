from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import Task, Priority, ExecutionMode
from api.services import StorageService

router = APIRouter()


def get_task_storage(org_id: str) -> StorageService[Task]:
    return StorageService[Task](f"data/organizations/{org_id}/tasks", Task)


@router.get("/{org_id}/tasks", response_model=List[Task])
async def list_tasks(org_id: str):
    storage = get_task_storage(org_id)
    return storage.list()


@router.post("/{org_id}/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(org_id: str, task: Task):
    task.organization_id = org_id
    task.priority = task.priority or Priority.MEDIUM
    task.execution_mode = task.execution_mode or ExecutionMode.SEQUENTIAL
    storage = get_task_storage(org_id)
    return storage.save(task)


@router.get("/{org_id}/tasks/{task_id}", response_model=Task)
async def get_task(org_id: str, task_id: str):
    storage = get_task_storage(org_id)
    task = storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{org_id}/tasks/{task_id}", response_model=Task)
async def update_task(org_id: str, task_id: str, task: Task):
    storage = get_task_storage(org_id)
    existing = storage.get(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    task.id = task_id
    task.organization_id = org_id
    return storage.save(task)


@router.delete("/{org_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(org_id: str, task_id: str):
    storage = get_task_storage(org_id)
    if not storage.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/{org_id}/tasks/{task_id}/dependencies")
async def get_task_dependencies(org_id: str, task_id: str):
    storage = get_task_storage(org_id)
    task = storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    all_tasks = storage.list()
    task_map = {t.id: t for t in all_tasks}

    def get_dependency_chain(t: Task, visited: set = None) -> dict:
        if visited is None:
            visited = set()
        if t.id in visited:
            return {"id": t.id, "name": t.name, "circular_reference": True}
        visited.add(t.id)

        deps = [task_map.get(dep_id) for dep_id in t.dependencies if dep_id in task_map]
        return {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "priority": t.priority,
            "execution_mode": t.execution_mode,
            "dependencies": [get_dependency_chain(dep, visited.copy()) for dep in deps if dep]
        }

    return get_dependency_chain(task)
