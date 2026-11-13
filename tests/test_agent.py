from types import SimpleNamespace

import pytest

from call_to_crm_agent.agent import run_agent


def test_run_agent_stops_on_max_tokens(crm):
    response = SimpleNamespace(
        stop_reason="max_tokens",
        content=[
            SimpleNamespace(
                type="tool_use",
                id="t1",
                name="log_call_note",
                input={"contact_id": "1", "summary": "cut off"},
            )
        ],
    )
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: response))

    with pytest.raises(RuntimeError, match="max tokens"):
        run_agent(client, crm, system_prompt="test", transcript="test")  # type: ignore[arg-type]

    assert crm.notes == []
