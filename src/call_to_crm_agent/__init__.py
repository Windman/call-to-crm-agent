import anthropic
from dotenv import load_dotenv

from call_to_crm_agent.agent import run_agent


def main() -> None:
    load_dotenv()
    client: anthropic.Anthropic = anthropic.Anthropic()
    run_agent(
        client,
        "Anna Smirnova from Blue Sky called, +995 599 000 111. She’s interested in a plan for a team of 20 people. She asked us to send a commercial proposal and call her back on Thursday.",
    )
