import json

import anthropic
from dotenv import load_dotenv

from call_to_crm_agent.agent import run_agent


def main() -> None:
    load_dotenv()
    client: anthropic.Anthropic = anthropic.Anthropic()
    run_agent(
        client,
        "Звонила Анна Смирнова, +995 599 000 111",
    )
