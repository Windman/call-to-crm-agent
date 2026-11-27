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


def test_run_agent_returns_steps_and_report(crm):
    responses = [
        SimpleNamespace(
            stop_reason="tool_use",
            content=[
                SimpleNamespace(
                    type="tool_use",
                    id="t1",
                    name="find_contact",
                    input={"phone": "+995555123456"},
                )
            ],
        ),
        SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="Done.")],
        ),
    ]
    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kwargs: responses.pop(0))
    )

    run = run_agent(client, crm, system_prompt="test", transcript="test")  # type: ignore[arg-type]

    assert run.model_calls == 2
    assert run.report == "Done."
    assert [s.tool for s in run.steps] == ["find_contact"]
    assert run.steps[0].is_error is False


def test_run_agent_callback_steps(crm):
    received = []

    responses = [
        SimpleNamespace(
            stop_reason="tool_use",
            content=[
                SimpleNamespace(
                    type="tool_use",
                    id="t1",
                    name="find_contact",
                    input={"phone": "+995555123456"},
                )
            ],
        ),
        SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="Done.")],
        ),
    ]
    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kwargs: responses.pop(0))
    )

    run = run_agent(
        client,  # type: ignore[arg-type]
        crm,
        system_prompt="test",
        transcript="test",
        max_steps=10,
        on_step=received.append,
    )  # type: ignore[arg-type]

    assert received == run.steps
