"""PM adapter capabilities discovery tool."""


def register(mcp):
    @mcp.tool()
    async def pm_get_capabilities() -> dict:
        """Return the list of PM operations this adapter supports."""
        return {
            "adapter": "github",
            "adapter_mode": "hybrid",
            "capabilities": [
                "pm_sync",
                "pm_bulk_create",
                "pm_bulk_update",
                "pm_get_status",
                "pm_link_story_to_epic",
                "pm_bulk_rename",
                "pm_action_log",
                "pm_get_capabilities",
            ],
        }
