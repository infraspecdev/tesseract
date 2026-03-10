"""ClickUp REST API wrapper using httpx.AsyncClient."""

from __future__ import annotations

from typing import Any

import httpx


class ClickUpAPIError(Exception):
    """Raised when the ClickUp API returns a non-2xx response."""

    def __init__(self, status_code: int, ecode: str | None, message: str):
        self.status_code = status_code
        self.ecode = ecode
        self.message = message
        super().__init__(f"ClickUp API {status_code}: {ecode or ''} — {message}")


class ClickUpClient:
    """Thin async wrapper around the ClickUp v2 REST API."""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_token: str):
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": api_token, "Content-Type": "application/json"},
            timeout=30.0,
        )

    async def close(self):
        await self._client.aclose()

    # -- low-level --------------------------------------------------------

    async def _request(
        self, method: str, path: str, json: dict | None = None, params: dict | None = None
    ) -> dict:
        resp = await self._client.request(method, path, json=json, params=params)
        if resp.status_code >= 400:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            raise ClickUpAPIError(
                status_code=resp.status_code,
                ecode=body.get("ECODE"),
                message=body.get("err", resp.text[:200]),
            )
        return resp.json() if resp.content else {}

    # -- tasks -------------------------------------------------------------

    async def create_task(self, list_id: str, task_data: dict) -> dict:
        """Create a task in a list. Returns the created task object."""
        return await self._request("POST", f"/list/{list_id}/task", json=task_data)

    async def update_task(self, task_id: str, updates: dict) -> dict:
        """Update a task. Returns the updated task object."""
        return await self._request("PUT", f"/task/{task_id}", json=updates)

    async def delete_task(self, task_id: str) -> dict:
        """Delete a task."""
        return await self._request("DELETE", f"/task/{task_id}")

    async def get_task(self, task_id: str) -> dict:
        """Get a single task by ID."""
        return await self._request("GET", f"/task/{task_id}")

    async def get_tasks_by_list(
        self, list_id: str, *, include_closed: bool = False
    ) -> list[dict]:
        """Get all tasks in a list with auto-pagination. Returns the full tasks array."""
        all_tasks: list[dict] = []
        page = 0
        while True:
            params: dict[str, Any] = {"page": page}
            if include_closed:
                params["include_closed"] = "true"
            result = await self._request("GET", f"/list/{list_id}/task", params=params)
            tasks = result.get("tasks", [])
            all_tasks.extend(tasks)
            if len(tasks) < 100:
                break
            page += 1
        return all_tasks

    # -- custom fields (relationship fields) --------------------------------

    async def set_custom_field(self, task_id: str, field_id: str, value: Any) -> dict:
        """Set a custom field value using the direct endpoint.

        This is the endpoint that ACTUALLY WORKS for list_relationship fields,
        unlike the update_task endpoint which silently drops them.
        """
        return await self._request(
            "POST", f"/task/{task_id}/field/{field_id}", json={"value": value}
        )

    async def set_relationship_field(
        self,
        task_id: str,
        field_id: str,
        linked_task_ids: list[str],
        *,
        action: str = "add",
    ) -> dict:
        """Set a list_relationship custom field.

        Args:
            task_id: The task to set the relationship on.
            field_id: The relationship field UUID.
            linked_task_ids: Task IDs to link.
            action: "add" or "remove".
        """
        value = {"add": linked_task_ids} if action == "add" else {"rem": linked_task_ids}
        return await self.set_custom_field(task_id, field_id, value)
