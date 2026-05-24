"""Tool registry unit tests."""

import pytest

from app.infrastructure.tools.loader import load_all_tools
from app.infrastructure.tools.registry import tool_registry


@pytest.fixture(autouse=True)
def _load_tools():
    load_all_tools()


def test_tools_registered():
    definitions = tool_registry.get_all_definitions()
    assert len(definitions) >= 10
    names = {d.name for d in definitions}
    assert "create_customer" in names
    assert "search_customers" in names


def test_permission_filtering():
    allowed = tool_registry.get_allowed_definitions(["users:read"])
    allowed_names = {t.name for t in allowed}
    assert "get_user_profile" in allowed_names
    assert "list_users" not in allowed_names
