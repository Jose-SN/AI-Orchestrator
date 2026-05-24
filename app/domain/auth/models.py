"""Auth bounded context — identity and permissions."""

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    module_permissions: list[str] = Field(default_factory=list)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        return bool(set(permissions) & set(self.permissions))

    def has_all_permissions(self, permissions: list[str]) -> bool:
        return set(permissions).issubset(set(self.permissions))
