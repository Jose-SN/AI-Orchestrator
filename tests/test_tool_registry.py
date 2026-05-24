"""Tool registry tests."""

import pytest

from app.infrastructure.tools.loader import load_all_tools
from app.infrastructure.tools.registry import tool_registry


@pytest.fixture(autouse=True)
def _load_tools():
    load_all_tools()


def test_tools_registered():
    definitions = tool_registry.get_all_definitions()
    assert len(definitions) >= 4
    names = {d.name for d in definitions}
    assert "get_user_profile" in names
    assert "list_modules" in names


def test_permission_filtering():
    load_all_tools()
    allowed = tool_registry.get_allowed_definitions(["users:read"])
    allowed_names = {t.name for t in allowed}
    assert "get_user_profile" in allowed_names
    assert "list_users" not in allowed_names  # requires users:list too


def test_all_permissions_grants_all_tools():
    all_perms = [
        "users:read",
        "users:list",
        "modules:read",
        "permissions:read",
    ]
    allowed = tool_registry.get_allowed_definitions(all_perms)
    assert len(allowed) == len(tool_registry.get_all_definitions())
