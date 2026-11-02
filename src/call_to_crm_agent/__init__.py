import anthropic
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=200,
        messages=[
            {"role": "user", "content": "Ответь одним предложением: что такое CRM?"}
        ],
    )

    print(response.content[0].text)
    print("stop_reason:", response.stop_reason)
    print(response.model_dump_json(indent=2))