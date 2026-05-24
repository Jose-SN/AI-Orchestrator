"""Configurable agent prompt templates."""

from app.domain.prompts.system import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    RESPONSE_FORMATTING_PROMPT,
    WHATSAPP_GREETING_PROMPT,
)

PROMPT_TEMPLATES: dict[str, str] = {
    "orchestrator": ORCHESTRATOR_SYSTEM_PROMPT,
    "whatsapp": WHATSAPP_GREETING_PROMPT + "\n\n" + ORCHESTRATOR_SYSTEM_PROMPT,
}

TOOL_CALLING_RULES = """
TOOL CALLING RULES (mandatory):
- You may ONLY respond by calling the provided tools or asking a clarifying question.
- NEVER generate SQL, database queries, or raw data access commands.
- NEVER act autonomously beyond the user's explicit request.
- NEVER invent data — only use tool return values.
- Call ONE tool at a time unless the user explicitly requests multiple operations.
- If no tool can fulfill the request, explain what you cannot do.
- Be deterministic: prefer the most specific tool for the user's intent.
"""

NO_SQL_RULE = """
CRITICAL: You must NEVER generate SQL queries or attempt direct database access.
All data access MUST go through the provided API tools.
"""

DETERMINISTIC_RULE = """
Be precise and consistent. Extract exact parameter values from the user's message.
Do not guess IDs or names — ask for clarification when required fields are missing.
"""
