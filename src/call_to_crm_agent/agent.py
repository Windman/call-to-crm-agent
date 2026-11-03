import anthropic
from anthropic.types import Message

from call_to_crm_agent.tools import TOOLS, execute_tool


def run_agent(
    client: anthropic.Anthropic, transcript: str, max_steps: int = 10
) -> list:
    messages_history = [{"role": "user", "content": transcript}]

    for step in range(max_steps):
        tool_results = []
        model_response = call_to_crm_agent(client, messages_history)
        messages_history.append(
            {"role": "assistant", "content": model_response.content}
        )

        for block in model_response.content:
            if block.type == "text":
                print("text:", block.text)
            if block.type == "tool_use":
                tool_result = execute_tool(block.name, block.input)
                tool_error = tool_result.is_error
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result.text,
                        "is_error": tool_error,
                    }
                )

        if model_response.stop_reason != "tool_use":
            return messages_history

        messages_history.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent did not finish in {max_steps} steps")


def call_to_crm_agent(client: anthropic.Anthropic, messages: list) -> Message:
    model_response = client.messages.create(
        model="claude-sonnet-5-5", tools=TOOLS, max_tokens=1024, messages=messages
    )

    return model_response
