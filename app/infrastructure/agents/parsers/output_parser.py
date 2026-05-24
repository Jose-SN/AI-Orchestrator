"""Structured output parser for LangGraph agent results."""

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from app.domain.agents.result import AgentResult, ToolCallRecord
from app.domain.tools.response import ToolResponse


class AgentOutputParser:
    """Parses raw LangGraph message history into structured AgentResult."""

    def parse(
        self,
        raw_result: dict[str, Any],
        *,
        conversation_id: str,
        provider: str,
        model: str,
    ) -> AgentResult:
        messages: list[BaseMessage] = raw_result.get("messages", [])
        tool_calls = self._extract_tool_calls(messages)
        response_text = self._extract_final_response(messages)
        iterations = sum(1 for m in messages if isinstance(m, AIMessage) and getattr(m, "tool_calls", None))

        return AgentResult(
            response=response_text,
            tool_calls=tool_calls,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            iterations=iterations,
            used_tools=len(tool_calls) > 0,
            metadata={"message_count": len(messages)},
        )

    def _extract_tool_calls(self, messages: list[BaseMessage]) -> list[ToolCallRecord]:
        records: list[ToolCallRecord] = []
        tool_outputs: dict[str, str] = {}

        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_outputs[getattr(msg, "tool_call_id", "")] = str(msg.content)

        for msg in messages:
            if not isinstance(msg, AIMessage):
                continue
            for call in getattr(msg, "tool_calls", None) or []:
                call_id = call.get("id", "")
                raw_output = tool_outputs.get(call_id, "")
                success, output, error = self._parse_tool_output(raw_output)
                records.append(ToolCallRecord(
                    tool_name=call.get("name", "unknown"),
                    input=call.get("args", {}),
                    output=output,
                    success=success,
                    error=error,
                ))
        return records

    @staticmethod
    def _parse_tool_output(raw: str) -> tuple[bool, str | None, str | None]:
        if not raw:
            return True, None, None
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "success" in data:
                parsed = ToolResponse.model_validate(data)
                return parsed.success, raw, parsed.error
        except (json.JSONDecodeError, ValueError):
            pass
        return True, raw, None

    @staticmethod
    def _extract_final_response(messages: list[BaseMessage]) -> str:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                content = msg.content
                return content if isinstance(content, str) else str(content)

        if messages:
            last = messages[-1]
            content = getattr(last, "content", "")
            return content if isinstance(content, str) else str(content)
        return "I was unable to generate a response. Please try again."
