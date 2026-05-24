"""Auth bounded context — identity and permissions."""

from pydantic import BaseModel, Field


class ModuleAccess(BaseModel):
    module_id: str
    module_name: str | None = None
    permissions: list[str] = Field(default_factory=list)
    enabled: bool = True


class IAMUserProfile(BaseModel):
    """Domain representation of IAM user permissions."""

    user_id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    module_permissions: list[str] = Field(default_factory=list)
    modules: list[ModuleAccess] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)


class UserContext(BaseModel):
    user_id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    module_permissions: list[str] = Field(default_factory=list)
    modules: list[ModuleAccess] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)

    @classmethod
    def from_profile(cls, profile: IAMUserProfile) -> "UserContext":
        return cls(**profile.model_dump())

    @property
    def effective_permissions(self) -> list[str]:
        merged = set(self.permissions) | set(self.module_permissions) | set(self.allowed_actions)
        for mod in self.modules:
            if mod.enabled:
                merged.update(mod.permissions)
        return sorted(merged)

    def has_permission(self, permission: str) -> bool:
        return permission in self.effective_permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        return bool(set(permissions) & set(self.effective_permissions))

    def has_all_permissions(self, permissions: list[str]) -> bool:
        return set(permissions).issubset(set(self.effective_permissions))

    def has_module_access(self, module_id: str) -> bool:
        return any(m.module_id == module_id and m.enabled for m in self.modules)

    def has_action(self, action: str) -> bool:
        return action in self.allowed_actions or action in self.effective_permissions
