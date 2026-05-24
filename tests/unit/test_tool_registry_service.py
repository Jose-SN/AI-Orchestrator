"""Tool registry service tests."""

import pytest

from app.application.tools.service import ToolRegistryService
from app.domain.auth.models import UserContext
from app.infrastructure.tools.loader import load_all_tools


@pytest.fixture(autouse=True)
def _load_tools():
    load_all_tools()


@pytest.fixture
def service() -> ToolRegistryService:
    return ToolRegistryService()


@pytest.fixture
def admin_user() -> UserContext:
    return UserContext(
        user_id="admin-1",
        permissions=[
            "users:read", "users:list",
            "modules:read", "permissions:read",
            "customers:read", "customers:list", "customers:create",
            "customers:update", "customers:delete", "customers:search",
        ],
    )


@pytest.fixture
def limited_user() -> UserContext:
    return UserContext(user_id="user-1", permissions=["customers:read"])


def test_snapshot_groups_by_operation(service, admin_user):
    snapshot = service.get_snapshot(admin_user)
    assert snapshot.allowed_count >= 6
    assert "create" in snapshot.tools_by_operation
    assert "customers" in snapshot.tools_by_category


def test_permission_filtering_excludes_write_tools(service, limited_user):
    snapshot = service.get_snapshot(limited_user)
    assert "create_customer" not in snapshot.allowed_tools
    assert "delete_customer" not in snapshot.allowed_tools


def test_load_langchain_tools_only_allowed(service, limited_user):
    tools = service.load_langchain_tools(limited_user, token="test-token")
    tool_names = {t.name for t in tools}
    assert "get_customer" in tool_names or "list_customers" not in tool_names
    assert "create_customer" not in tool_names
    assert "delete_customer" not in tool_names


def test_customer_crud_tools_registered(service, admin_user):
    snapshot = service.get_snapshot(admin_user)
    customer_ops = snapshot.tools_by_category.get("customers", [])
    assert "create_customer" in customer_ops
    assert "search_customers" in customer_ops
