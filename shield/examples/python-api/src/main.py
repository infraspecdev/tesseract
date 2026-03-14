"""Task management API — example for Shield pipeline walkthrough."""
from fastapi import FastAPI

app = FastAPI(title="Task Manager", version="0.1.0")

# No auth middleware — security reviewer should flag this
# No error handling middleware — operations reviewer should flag this


@app.get("/health")
async def health():
    return {"status": "ok"}


from src.routes.tasks import router as tasks_router
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
