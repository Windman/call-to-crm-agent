from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from call_to_crm_agent.agent import AgentRun
from call_to_crm_agent.api import app, get_client, get_crm


@pytest.fixture
def api(crm):
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
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kwargs: responses.pop(0))
    )
    app.dependency_overrides[get_client] = lambda: fake_client
    app.dependency_overrides[get_crm] = lambda: crm
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_post_runs_returns_agent_run(api):
    response = api.post("/runs", json={"transcript": "John called"})
    run = AgentRun.model_validate(response.json())
    assert response.status_code == 200
    assert run.model_calls == 2
    assert run.report == "Done."
    assert [s.tool for s in run.steps] == ["find_contact"]
    assert run.steps[0].is_error is False


def test_post_runs_without_transcript_returns_422(api):
    response = api.post("/runs", json={})
    assert response.status_code == 422
