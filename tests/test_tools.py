from call_to_crm_agent.tools import execute_tool


def test_unknown_tool_returns_error():
    result = execute_tool("no_such_tool", {})
    assert result.is_error
    assert "no_such_tool" in result.text
