import json
import os
import queue
import threading
from collections.abc import Iterator
from datetime import date
from functools import cache
from typing import Annotated

import anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from call_to_crm_agent import build_system_prompt, fake_data
from call_to_crm_agent.agent import AgentRun, run_agent
from call_to_crm_agent.crm import CRM
from call_to_crm_agent.hubspot import HubSpotClient, HubSpotCRM

load_dotenv()
app = FastAPI(title="Call-to-CRM Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RuntimeError)
def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(anthropic.APIError)
def handle_llm_api_error(request: Request, exc: anthropic.APIError) -> JSONResponse:
    return JSONResponse(
        status_code=502, content={"detail": f"LLM API error: {exc.message!s}"}
    )


class RunRequest(BaseModel):
    transcript: str


@cache
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def get_crm() -> CRM:
    crm_type = os.environ.get("CRM", "hubspot")

    if crm_type == "fake":
        crm = fake_data.build_fake_crm()
    elif crm_type == "hubspot":
        crm = get_hubspot_crm()
    else:
        raise RuntimeError(f"Unknown CRM={crm_type!r}, expected 'fake' or 'hubspot'")

    return crm


@app.post("/runs")
def create_run(
    request: RunRequest,
    client: Annotated[anthropic.Anthropic, Depends(get_client)],
    crm: Annotated[CRM, Depends(get_crm)],
) -> AgentRun:
    return run_agent(client, crm, build_system_prompt(date.today()), request.transcript)


@cache
def get_hubspot_crm() -> HubSpotCRM:
    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        raise RuntimeError("HUBSPOT_TOKEN is not set")
    return HubSpotCRM(HubSpotClient(token=token))


def sse_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@app.post("/runs/stream")
def stream_run(
    request: RunRequest,
    client: Annotated[anthropic.Anthropic, Depends(get_client)],
    crm: Annotated[CRM, Depends(get_crm)],
) -> StreamingResponse:
    events: queue.Queue[str | None] = queue.Queue()

    def work() -> None:
        try:
            agent_run = run_agent(
                client,
                crm,
                build_system_prompt(date.today()),
                request.transcript,
                on_step=lambda step: events.put(
                    sse_event("step", step.model_dump_json())
                ),
            )
            events.put(sse_event("done", agent_run.model_dump_json()))

        except RuntimeError as err:
            events.put(sse_event("error", data=json.dumps({"detail": str(err)})))
        except anthropic.APIError as err:
            llm_error_message = f"LLM API error: {err.message!s}"
            events.put(
                sse_event("error", data=json.dumps({"detail": llm_error_message}))
            )
        finally:
            events.put(None)

    threading.Thread(target=work, daemon=True).start()

    def stream() -> Iterator[str]:
        while (event := events.get()) is not None:
            yield event

    return StreamingResponse(stream(), media_type="text/event-stream")
