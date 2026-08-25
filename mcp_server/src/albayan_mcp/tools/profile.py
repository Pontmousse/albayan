from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from albayan_mcp.api_client import api_get_object


class ProfileResult(BaseModel):
    id: str
    email: str
    full_name: str | None
    affiliation: str | None


def register_profile_tools(server: MCPServer) -> None:
    @server.tool(
        name="get_my_profile",
        title="ملفي الشخصي",
        description="قراءة الملف الشخصي للمستخدم الحالي من مجلة البيان.",
    )
    async def get_my_profile() -> ProfileResult:
        profile = await api_get_object("/api/v1/users/me")
        return ProfileResult(
            id=profile["id"],
            email=profile["email"],
            full_name=profile.get("full_name"),
            affiliation=profile.get("affiliation"),
        )
