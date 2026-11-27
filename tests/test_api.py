from types import SimpleNamespace

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from call_to_crm_agent.agent import AgentRun
from call_to_crm_agent.api import app, get_client, get_crm


def use_failing_client(error: Exception):
    def create(**kwargs):
        raise error

    app.dependency_overrides[get_client] = lambda: SimpleNamespace(
        messages=SimpleNamespace(create=create)
    )


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


def test_agent_failure_returns_json_500(api):
    use_failing_client(RuntimeError("A stopped: max_tokens"))
    response = api.post(
        "/runs",
        json={"transcript": "John called"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )
    assert response.json()["detail"] == "A stopped: max_tokens"


def test_llm_api_failure_returns_json_502(api):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    use_failing_client(anthropic.APIConnectionError(request=request))
    response = api.post(
        "/runs",
        json={"transcript": "John called"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )
    assert response.json()["detail"] == "LLM API error: Connection error."


def test_stream_sends_steps_then_done(api):
    response = api.post("/runs/stream", json={"transcript": "John called"})

    assert response.status_code == 200
    # Starlette дописывает "; charset=utf-8", поэтому startswith, а не ==
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.count("event: step") == 1
    assert response.text.index("event: step") < response.text.index("event: done")


def test_stream_reports_error_as_event(api):
    use_failing_client(RuntimeError("boom"))
    response = api.post("/runs/stream", json={"transcript": "John called"})

    assert response.status_code == 200
    assert 'event: error\ndata: {"detail": "boom"}' in response.text
