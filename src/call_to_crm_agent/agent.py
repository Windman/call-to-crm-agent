import anthropic
from anthropic.types import Message

from call_to_crm_agent.crm import CRM
from call_to_crm_agent.tools import TOOLS, execute_tool

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 4096


def run_agent(
    client: anthropic.Anthropic,
    crm: CRM,
    system_prompt: str,
    transcript: str,
    max_steps: int = 10,
) -> list:
    messages_history = [{"role": "user", "content": transcript}]

    for step in range(max_steps):
        tool_results = []
        model_response = call_to_crm_agent(client, system_prompt, messages_history)

        if model_response.stop_reason == "max_tokens":
            raise RuntimeError(
                f"The max tokens threshold has been reached on step: {step}. Maximum limin is: {MAX_TOKENS}, "
            )

        messages_history.append(
            {"role": "assistant", "content": model_response.content}
        )

        for block in model_response.content:
            if block.type == "text":
                print("text:", block.text)
                print()
            if block.type == "tool_use":
                print(f"Executing tool: '{block.name}' with args: '{block.input}'")
                tool_result = execute_tool(crm, block.name, block.input)
                tool_error = tool_result.is_error
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result.text,
                        "is_error": tool_error,
                    }
                )

        print(f"step {step}: stop_reason={model_response.stop_reason}")

        if model_response.stop_reason != "tool_use":
            return messages_history

        messages_history.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent did not finish in {max_steps} steps")


def call_to_crm_agent(
    client: anthropic.Anthropic, system_prompt: str, messages: list
) -> Message:
    model_response = client.messages.create(
        model=MODEL,
        tools=TOOLS,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    return model_response
