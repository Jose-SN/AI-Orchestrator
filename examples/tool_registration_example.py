"""
Example: registering a new modular tool with the orchestrator.

Copy this pattern when adding tools for a new microservice domain.
"""

from pydantic import BaseModel, Field

from app.domain.tools.context import ToolExecutionContext
from app.domain.tools.models import ToolOperation
from app.domain.tools.response import ToolResponse
from app.infrastructure.tools.decorators import orchestrator_tool


class GetInvoiceInput(BaseModel):
    invoice_id: str = Field(description="Invoice ID to retrieve")


# Step 1: Define input schema (LLM-visible fields only)
# Step 2: Decorate with @orchestrator_tool — declare IAM permissions + operation type
# Step 3: Handler calls existing HTTP API — never SQL, never direct DB access
# Step 4: Return ToolResponse for structured output (tracing + audit handled automatically)
# Step 5: Import module in app/infrastructure/tools/loader.py → load_all_tools()


@orchestrator_tool(
    name="get_invoice",
    description="Retrieve an invoice by ID. Use when the user asks about a specific invoice.",
    required_permissions=["invoices:read"],
    service="billing-service",
    operation=ToolOperation.GET,
    category="billing",
    args_schema=GetInvoiceInput,
)
async def get_invoice(ctx: ToolExecutionContext, invoice_id: str) -> ToolResponse:
    # In production, inject a BillingServiceClient via BaseAPITool
    return ToolResponse.ok(
        tool_name="get_invoice",
        operation=ToolOperation.GET,
        data={"invoice_id": invoice_id, "status": "example"},
        trace_id=ctx.trace_id,
    )
