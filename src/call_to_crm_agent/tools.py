import json
from dataclasses import asdict, dataclass
from datetime import date

from call_to_crm_agent.crm import CRM


@dataclass
class ToolResult:
    text: str
    is_error: bool = False


def find_contact(crm: CRM, phone: str) -> list[dict]:
    return [asdict(c) for c in crm.find_contacts(phone)]


def create_contact(
    crm: CRM,
    first_name: str,
    last_name: str,
    phone: str,
    email: str | None = None,
    company: str | None = None,
) -> dict:
    return asdict(crm.create_contact(first_name, last_name, phone, email, company))


def log_call_note(crm: CRM, contact_id: str, summary: str) -> dict:
    return asdict(crm.log_call_note(contact_id, summary))


def create_task(crm: CRM, contact_id: str, title: str, due_date: str) -> dict:
    return asdict(crm.create_task(contact_id, title, date.fromisoformat(due_date)))


def execute_tool(crm: CRM, name: str, args: dict) -> ToolResult:
    if name in TOOL_FUNCTIONS:
        try:
            result = TOOL_FUNCTIONS[name](crm, **args)
            print(f"Tool '{name}' succeeded with result: '{result}'")
            return ToolResult(text=json.dumps(result, ensure_ascii=False, default=str))
        except Exception as e:
            message = f"Tool '{name}' execution failed: {type(e).__name__}: {e}"
            print(message)
            return ToolResult(text=message, is_error=True)

    else:
        print(f"Tool '{name}' is unknown")
        return ToolResult(text=f"Unknown tool: '{name}'", is_error=True)


TOOL_FUNCTIONS = {
    "find_contact": find_contact,
    "create_contact": create_contact,
    "log_call_note": log_call_note,
    "create_task": create_task,
}

TOOLS = [
    {
        "name": "find_contact",
        "description": "Find existing CRM contacts by phone number. Call this first, before create_contact, to avoid duplicates. Pass the phone number from the call, ideally with country code. Returns a JSON list of matching contacts; empty list if none",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Phone number in any format, e.g. +995 555 12 34 56.",
                },
            },
            "required": ["phone"],
        },
    },
    {
        "name": "create_contact",
        "description": "Create a new CRM contact. Call only if find_contact returned an empty list. first_name, last_name and phone are required; email and company are optional. Returns the created contact as JSON, including its id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "Given name, in Latin script.",
                },
                "last_name": {
                    "type": "string",
                    "description": "Family name, in Latin script.",
                },
                "email": {
                    "type": "string",
                    "description": "The email address of the contact to create.",
                },
                "phone": {
                    "type": "string",
                    "description": "The phone number of the contact to create.",
                },
                "company": {
                    "type": "string",
                    "description": "The company of the contact to create.",
                },
            },
            "required": ["first_name", "last_name", "phone"],
        },
    },
    {
        "name": "log_call_note",
        "description": "Log a call note in the CRM. When to use: Use this tool when you need to log a call in the CRM. What to pass - contact_id and summary are required. What is returned - the logged call note information in JSON format with the id",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "The ID of the contact to log the call note for.",
                },
                "summary": {
                    "type": "string",
                    "description": "The summary of the call note to log.",
                },
            },
            "required": ["contact_id", "summary"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task in the CRM. When to use: Use this tool when you need to create a new task in the CRM. What to pass - contact_id, title and due_date are required. What is returned - the created task information in JSON format with the id",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "The ID of the contact to create the task for.",
                },
                "title": {
                    "type": "string",
                    "description": "The title of the task to create.",
                },
                "due_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Due date in YYYY-MM-DD format, e.g. 2026-11-05.",
                },
            },
            "required": ["contact_id", "title", "due_date"],
        },
    },
]
