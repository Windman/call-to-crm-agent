import os
from datetime import date
from functools import cache
from typing import Annotated

import anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from call_to_crm_agent import build_system_prompt, fake_data
from call_to_crm_agent.agent import AgentRun, run_agent
from call_to_crm_agent.crm import CRM
from call_to_crm_agent.hubspot import HubSpotClient, HubSpotCRM

load_dotenv()
app = FastAPI(title="Call-to-CRM Agent")


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
