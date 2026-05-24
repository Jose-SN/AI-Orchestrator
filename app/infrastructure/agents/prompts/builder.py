"""Builds system prompts from configurable templates."""

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.infrastructure.agents.prompts.templates import (
    DETERMINISTIC_RULE,
    NO_SQL_RULE,
    PROMPT_TEMPLATES,
    TOOL_CALLING_RULES,
)


class PromptBuilder:
    """Constructs agent prompts with configurable templates and context."""

    def __init__(self, template_key: str = "orchestrator") -> None:
        self._template_key = template_key

    def build_system_prompt(
        self,
        *,
        user_display_name: str | None = None,
        available_tools: list[str] | None = None,
        extra_instructions: str | None = None,
    ) -> str:
        base = PROMPT_TEMPLATES.get(self._template_key, PROMPT_TEMPLATES["orchestrator"])
        parts = [base, TOOL_CALLING_RULES, NO_SQL_RULE, DETERMINISTIC_RULE]

        if user_display_name:
            parts.append(f"You are assisting: {user_display_name}.")

        if available_tools:
            tool_list = ", ".join(sorted(available_tools))
            parts.append(f"Available tools for this session: {tool_list}")

        if extra_instructions:
            parts.append(extra_instructions)

        return "\n\n".join(parts)

    def build_messages(
        self,
        user_message: str,
        *,
        system_prompt: str,
        history: list[BaseMessage] | None = None,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=user_message))
        return messages
