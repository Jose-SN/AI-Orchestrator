"""IAM schema parsing and UserContext tests."""

from app.domain.auth.models import UserContext
from app.infrastructure.iam.schemas import parse_iam_profile


def test_parse_iam_profile_merges_permissions():
    profile = parse_iam_profile({
        "userId": "u1",
        "permissions": ["customers:read"],
        "modulePermissions": ["modules:read"],
        "allowedActions": ["customers:search"],
        "modules": [{"moduleId": "crm", "permissions": ["customers:list"]}],
    })
    user = UserContext.from_profile(profile)
    perms = user.effective_permissions
    assert "customers:read" in perms
    assert "customers:search" in perms
    assert "customers:list" in perms
    assert "modules:read" in perms


def test_has_module_access():
    profile = parse_iam_profile({
        "userId": "u1",
        "modules": [{"moduleId": "crm", "enabled": True, "permissions": []}],
    })
    user = UserContext.from_profile(profile)
    assert user.has_module_access("crm") is True
    assert user.has_module_access("billing") is False


def test_has_action():
    user = UserContext(user_id="u1", allowed_actions=["customers:create"])
    assert user.has_action("customers:create") is True
    assert user.has_action("customers:delete") is False
