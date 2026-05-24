"""Permission and identity domain models."""

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Authenticated user context resolved from IAM."""

    user_id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    module_permissions: list[str] = Field(default_factory=list)

    def has_permission(self, permission: str) -> bool:
        """Check if user holds a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        """Check if user holds at least one of the given permissions."""
        return bool(set(permissions) & set(self.permissions))

    def has_all_permissions(self, permissions: list[str]) -> bool:
        """Check if user holds all of the given permissions."""
        return set(permissions).issubset(set(self.permissions))
