import anthropic
from dotenv import load_dotenv

from .tools import TOOLS


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-5-5",
        tools=TOOLS,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Звонил John Doe из Acme, +995555123456, просит выставить счёт до пятницы. Найди этот контакт в CRM",
            }
        ],
    )

    print("stop_reason:", response.stop_reason)

    for block in response.content:
        print("type:", block.type)
        if block.type == "text":
            print("text:", block.text)
        elif block.type == "tool_use":
            print("tool_name:", block.name)
            print("tool_arguments:", block.input)
