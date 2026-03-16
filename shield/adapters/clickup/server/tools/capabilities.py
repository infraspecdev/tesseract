"""PM adapter capabilities discovery tool."""


def register(mcp):
    """Register the pm_get_capabilities tool."""

    @mcp.tool()
    async def pm_get_capabilities() -> dict:
        """Return the list of PM operations this adapter supports.

        Skills call this once at the start of a PM interaction to discover
        which operations are available. Unsupported operations should be
        skipped gracefully.
        """
        return {
            "adapter": "clickup",
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
