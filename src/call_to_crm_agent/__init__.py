import json

import anthropic
from anthropic.types import Message
from dotenv import load_dotenv

from .tools import TOOLS, find_contact


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    messages_history = []
    tool_results = []

    initial_message = {
        "role": "user",
        "content": "Звонил John Doe из Acme, +995555123456, просит выставить счёт до пятницы. Найди этот контакт в CRM",
    }

    messages_history.append(initial_message)

    model_response = call_to_crm_agent(client, messages_history)

    messages_history.append({"role": "assistant", "content": model_response.content})

    for block in model_response.content:
        print("type:", block.type)
        if block.type == "text":
            print("text:", block.text)
        elif block.type == "tool_use":
            print("tool_name:", block.name)
            print("tool_arguments:", block.input)

            tool_result = get_tool_result(block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": tool_result}
            )

    messages_history.append({"role": "user", "content": tool_results})
    final_response = call_to_crm_agent(client, messages_history)

    print_json_response(final_response)


def call_to_crm_agent(client: anthropic.Anthropic, messages: list) -> Message:
    model_response = client.messages.create(
        model="claude-sonnet-5-5", tools=TOOLS, max_tokens=1024, messages=messages
    )

    return model_response


def get_tool_result(tool_name: str, tool_arguments: dict) -> str:
    if tool_name == "find_contact":
        tool_result = find_contact(**tool_arguments)
        print(f"Tool {tool_name} result:\r\n {tool_result}")

    return json.dumps(tool_result)


def print_json_response(response: anthropic.Response) -> None:
    content_json = json.dumps(
        [block.model_dump(mode="json") for block in response.content],
        ensure_ascii=False,
        indent=2,
    )
    print("json:", content_json)
