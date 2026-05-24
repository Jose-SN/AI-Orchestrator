"""Agent output parser tests."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.infrastructure.agents.parsers.output_parser import AgentOutputParser


def test_parse_tool_calls_and_response():
    parser = AgentOutputParser()
    raw = {
        "messages": [
            HumanMessage(content="List customers"),
            AIMessage(content="", tool_calls=[{
                "id": "c1", "name": "list_customers", "args": {"limit": 10}
            }]),
            ToolMessage(
                content='{"success":true,"tool_name":"list_customers","data":[]}',
                tool_call_id="c1",
            ),
            AIMessage(content="No customers found."),
        ]
    }
    result = parser.parse(raw, conversation_id="conv-1", provider="ollama", model="qwen2.5:7b")

    assert result.response == "No customers found."
    assert result.used_tools is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "list_customers"
    assert result.tool_calls[0].success is True


def test_parse_no_tools_used():
    parser = AgentOutputParser()
    raw = {"messages": [HumanMessage(content="Hello"), AIMessage(content="Hi there!")]}
    result = parser.parse(raw, conversation_id="c2", provider="ollama", model="qwen2.5:7b")
    assert result.used_tools is False
    assert result.response == "Hi there!"
