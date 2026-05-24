"""Customer CRUD tools — call Customer microservice HTTP APIs."""

from pydantic import BaseModel, Field

from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.infrastructure.http.clients.microservices import CustomerServiceClient
from app.infrastructure.tools.base.api_tool import BaseAPITool
from app.infrastructure.tools.decorators import orchestrator_tool

_customer_api = BaseAPITool(CustomerServiceClient())
_customer_api.service_name = "customer-service"
_customer_api.resource_path = "/api/v1/customers"


# ── Input schemas (LLM-visible only — no auth context) ──────────────────────


class CreateCustomerInput(BaseModel):
    name: str = Field(description="Customer full name or company name")
    email: str = Field(description="Customer email address")
    phone: str | None = Field(default=None, description="Optional phone number")


class UpdateCustomerInput(BaseModel):
    customer_id: str = Field(description="ID of the customer to update")
    name: str | None = Field(default=None, description="Updated name")
    email: str | None = Field(default=None, description="Updated email")
    phone: str | None = Field(default=None, description="Updated phone")


class DeleteCustomerInput(BaseModel):
    customer_id: str = Field(description="ID of the customer to delete")


class GetCustomerInput(BaseModel):
    customer_id: str = Field(description="ID of the customer to retrieve")


class ListCustomersInput(BaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Maximum records to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class SearchCustomersInput(BaseModel):
    query: str = Field(description="Search term — name, email, or phone")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


# ── Tool handlers ────────────────────────────────────────────────────────────


@orchestrator_tool(
    name="create_customer",
    description="Create a new customer record. Use when the user wants to add or register a customer.",
    required_permissions=["customers:create"],
    service="customer-service",
    operation=ToolOperation.CREATE,
    category="customers",
    args_schema=CreateCustomerInput,
)
async def create_customer(
    ctx: ToolExecutionContext,
    name: str,
    email: str,
    phone: str | None = None,
):
    payload = {"name": name, "email": email}
    if phone:
        payload["phone"] = phone
    return await _customer_api.create(ctx, payload, tool_name="create_customer")


@orchestrator_tool(
    name="update_customer",
    description="Update an existing customer's details. Use when the user wants to modify customer information.",
    required_permissions=["customers:update"],
    service="customer-service",
    operation=ToolOperation.UPDATE,
    category="customers",
    args_schema=UpdateCustomerInput,
)
async def update_customer(
    ctx: ToolExecutionContext,
    customer_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
):
    payload = {k: v for k, v in {"name": name, "email": email, "phone": phone}.items() if v is not None}
    return await _customer_api.update(ctx, customer_id, payload, tool_name="update_customer")


@orchestrator_tool(
    name="delete_customer",
    description="Delete a customer record. Use when the user explicitly asks to remove a customer.",
    required_permissions=["customers:delete"],
    service="customer-service",
    operation=ToolOperation.DELETE,
    category="customers",
    args_schema=DeleteCustomerInput,
)
async def delete_customer(ctx: ToolExecutionContext, customer_id: str):
    return await _customer_api.delete(ctx, customer_id, tool_name="delete_customer")


@orchestrator_tool(
    name="get_customer",
    description="Retrieve a single customer by ID. Use when the user asks about a specific customer.",
    required_permissions=["customers:read"],
    service="customer-service",
    operation=ToolOperation.GET,
    category="customers",
    args_schema=GetCustomerInput,
)
async def get_customer(ctx: ToolExecutionContext, customer_id: str):
    return await _customer_api.get(ctx, customer_id, tool_name="get_customer")


@orchestrator_tool(
    name="list_customers",
    description="List customers with pagination. Use when the user wants to see all customers.",
    required_permissions=["customers:read", "customers:list"],
    service="customer-service",
    operation=ToolOperation.LIST,
    category="customers",
    args_schema=ListCustomersInput,
)
async def list_customers(ctx: ToolExecutionContext, limit: int = 20, offset: int = 0):
    return await _customer_api.list(
        ctx, tool_name="list_customers", params={"limit": limit, "offset": offset}
    )


@orchestrator_tool(
    name="search_customers",
    description="Search customers by name, email, or phone. Use when the user wants to find specific customers.",
    required_permissions=["customers:read", "customers:search"],
    service="customer-service",
    operation=ToolOperation.SEARCH,
    category="customers",
    args_schema=SearchCustomersInput,
)
async def search_customers(ctx: ToolExecutionContext, query: str, limit: int = 20):
    return await _customer_api.search(
        ctx, tool_name="search_customers", query=query, params={"limit": limit}
    )
