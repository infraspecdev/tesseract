"""GitHub REST + GraphQL API wrapper using httpx.AsyncClient."""

from __future__ import annotations

from typing import Any

import httpx


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API {status_code}: {message}")


class GitHubClient:
    """Async wrapper around GitHub REST v3 and GraphQL v4 APIs."""

    REST_BASE = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._client = httpx.AsyncClient(
            base_url=self.REST_BASE,
            headers=headers,
            timeout=30.0,
        )

    async def close(self):
        await self._client.aclose()

    # -- low-level REST -------------------------------------------------------

    async def _rest(
        self, method: str, path: str, json: dict | None = None, params: dict | None = None
    ) -> Any:
        resp = await self._client.request(method, path, json=json, params=params)
        if resp.status_code >= 400:
            body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
            raise GitHubAPIError(resp.status_code, body.get("message", resp.text[:200]))
        return resp.json() if resp.content else {}

    # -- low-level GraphQL ----------------------------------------------------

    async def _graphql(self, query: str, variables: dict | None = None) -> dict:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await self._client.post(self.GRAPHQL_URL, json=payload)
        if resp.status_code >= 400:
            raise GitHubAPIError(resp.status_code, resp.text[:200])
        data = resp.json()
        if "errors" in data:
            raise GitHubAPIError(422, str(data["errors"]))
        return data.get("data", {})

    # -- issues ---------------------------------------------------------------

    async def get_repo_issues(self, *, state: str = "open", per_page: int = 100) -> list[dict]:
        """Fetch all issues in the repo (auto-paginated)."""
        all_issues: list[dict] = []
        page = 1
        while True:
            batch = await self._rest(
                "GET",
                f"/repos/{self.owner}/{self.repo}/issues",
                params={"state": state, "per_page": per_page, "page": page},
            )
            all_issues.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return all_issues

    async def get_sub_issues(self, parent_number: int) -> list[dict]:
        """Fetch all sub-issues of an issue."""
        return await self._rest(
            "GET", f"/repos/{self.owner}/{self.repo}/issues/{parent_number}/sub_issues"
        )

    async def create_issue(
        self,
        title: str,
        body: str = "",
        assignees: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        """Create a GitHub issue. Returns the created issue object."""
        payload: dict = {"title": title, "body": body}
        if assignees:
            payload["assignees"] = assignees
        if labels:
            payload["labels"] = labels
        return await self._rest("POST", f"/repos/{self.owner}/{self.repo}/issues", json=payload)

    async def update_issue(self, issue_number: int, updates: dict) -> dict:
        """Update a GitHub issue."""
        return await self._rest(
            "PATCH", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", json=updates
        )

    async def add_sub_issue(self, parent_number: int, sub_issue_number: int) -> dict:
        """Link an issue as a sub-issue of a parent."""
        return await self._rest(
            "POST",
            f"/repos/{self.owner}/{self.repo}/issues/{parent_number}/sub_issues",
            json={"sub_issue_id": sub_issue_number},
        )

    # -- Projects v2 (GraphQL) ------------------------------------------------

    async def get_project_id(self, project_number: int) -> tuple[str, str]:
        """Get the node ID of a Projects v2 project. Tries org first, then user.

        Returns (project_node_id, owner_type).
        """
        query_org = """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) { id }
          }
        }
        """
        try:
            data = await self._graphql(query_org, {"owner": self.owner, "number": project_number})
            project_id = data["organization"]["projectV2"]["id"]
            return project_id, "org"
        except (GitHubAPIError, KeyError, TypeError):
            pass

        query_user = """
        query($owner: String!, $number: Int!) {
          user(login: $owner) {
            projectV2(number: $number) { id }
          }
        }
        """
        data = await self._graphql(query_user, {"owner": self.owner, "number": project_number})
        project_id = data["user"]["projectV2"]["id"]
        return project_id, "user"

    async def get_project_iteration_field(
        self, project_id: str
    ) -> tuple[str, list[dict]]:
        """Get the iteration field ID and available iterations for a project.

        Returns (field_id, [{"id": ..., "title": ..., "startDate": ...}]).
        """
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2IterationField {
                    id
                    name
                    configuration {
                      iterations { id title startDate }
                    }
                  }
                }
              }
            }
          }
        }
        """
        data = await self._graphql(query, {"projectId": project_id})
        fields = data.get("node", {}).get("fields", {}).get("nodes", [])
        for field in fields:
            if field and "configuration" in field:
                iterations = field["configuration"].get("iterations", [])
                return field["id"], iterations
        return "", []

    async def add_issue_to_project(self, project_id: str, issue_node_id: str) -> str:
        """Add an issue to a Projects v2 project. Returns the project item ID."""
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """
        data = await self._graphql(
            mutation, {"projectId": project_id, "contentId": issue_node_id}
        )
        return data["addProjectV2ItemById"]["item"]["id"]

    async def set_project_item_iteration(
        self, project_id: str, item_id: str, field_id: str, iteration_id: str
    ) -> None:
        """Set the iteration field on a project item."""
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $iterationId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: { iterationId: $iterationId }
          }) {
            projectV2Item { id }
          }
        }
        """
        await self._graphql(
            mutation,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "iterationId": iteration_id,
            },
        )

    async def get_project_items(self, project_id: str) -> list[dict]:
        """Fetch all items in a Projects v2 project with issue details."""
        query = """
        query($projectId: ID!, $cursor: String) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 100, after: $cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  content {
                    ... on Issue {
                      number title state
                      assignees(first: 5) { nodes { login } }
                      parent { number }
                    }
                  }
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldIterationValue {
                        iterationId title
                        field { ... on ProjectV2IterationField { name } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        all_items: list[dict] = []
        cursor = None
        while True:
            data = await self._graphql(query, {"projectId": project_id, "cursor": cursor})
            page = data.get("node", {}).get("items", {})
            nodes = page.get("nodes", [])
            all_items.extend(n for n in nodes if n and n.get("content"))
            page_info = page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info["endCursor"]
        return all_items
