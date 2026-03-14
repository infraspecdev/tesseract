"""Task CRUD endpoints — has intentional issues for Shield to find."""
from fastapi import APIRouter

router = APIRouter()

# In-memory store — no persistence
tasks: dict[str, dict] = {}
_counter = 0


@router.post("/")
async def create_task(task: dict):
    # No input validation — security reviewer should flag
    global _counter
    _counter += 1
    task_id = str(_counter)
    tasks[task_id] = {**task, "id": task_id, "status": "open"}
    return tasks[task_id]


@router.get("/")
async def list_tasks():
    return list(tasks.values())


@router.get("/{task_id}")
async def get_task(task_id: str):
    # No 404 handling — operations reviewer should flag
    return tasks[task_id]


@router.put("/{task_id}")
async def update_task(task_id: str, updates: dict):
    # No validation, no auth check
    tasks[task_id].update(updates)
    return tasks[task_id]


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    # No auth check — anyone can delete
    del tasks[task_id]
    return {"deleted": task_id}
