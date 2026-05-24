"""Dedicated audit logging for compliance and security review."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from app.core.config import settings

_audit_logger = structlog.get_logger("audit")


class AuditAction(str, Enum):
    CHAT_REQUEST = "chat.request"
    CHAT_RESPONSE = "chat.response"
    TOOL_INVOKED = "tool.invoked"
    PERMISSION_DENIED = "permission.denied"
    AGENT_EXECUTION = "agent.execution"
    AUTH_FAILURE = "auth.failure"


def audit_log(
    action: AuditAction,
    *,
    user_id: str | None = None,
    conversation_id: str | None = None,
    resource: str | None = None,
    outcome: str = "success",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a structured audit event. Separate from operational logs."""
    if not settings.audit_enabled:
        return

    _audit_logger.info(
        "audit_event",
        audit=True,
        action=action.value,
        user_id=user_id,
        conversation_id=conversation_id,
        resource=resource,
        outcome=outcome,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=metadata or {},
    )
