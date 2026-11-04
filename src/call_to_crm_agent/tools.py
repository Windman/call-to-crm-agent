import json
from dataclasses import dataclass
from datetime import date

"""
Описание инструмента:
что делает (ищет существующий контакт в CRM);
когда вызывать (до создания контакта, чтобы не завести дубль);
что передавать (лучше телефон: он уникальнее имени);
что вернёт (контакт или null, если не найден).
"""


@dataclass
class ToolResult:
    text: str
    is_error: bool = False


def find_contact(query: str) -> dict | None:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return None

    for contact in FAKE_CONTACTS:
        if any(normalized_query in str(value).casefold() for value in contact.values()):
            return contact

    return None


def create_contact(
    name: str, phone: str, email: str | None = None, company: str | None = None
) -> dict:
    new_contact = {
        "id": len(FAKE_CONTACTS) + 1,
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
    }
    FAKE_CONTACTS.append(new_contact)
    return new_contact


def log_call_note(contact_id: int, summary: str) -> dict:
    call_note = {
        "id": len(FAKE_NOTES) + 1,
        "contact_id": contact_id,
        "summary": summary,
    }
    FAKE_NOTES.append(call_note)
    return call_note


def create_task(contact_id: int, title: str, due_date: str) -> dict:
    date.fromisoformat(due_date)
    task = {
        "id": len(FAKE_TASKS) + 1,
        "contact_id": contact_id,
        "title": title,
        "due_date": due_date,
    }
    FAKE_TASKS.append(task)
    return task


def execute_tool(name: str, args: dict) -> ToolResult:
    if name in TOOL_FUNCTIONS:
        try:
            print(f"Executing tool: '{name}' with args: '{args}'\r\n")
            result = TOOL_FUNCTIONS[name](**args)
            print(f"Tool '{name}' succeeded with result: '{result}'\r\n")
            return ToolResult(text=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            print(f"Tool '{name}' execution failed: {e!s}\r\n")
            return ToolResult(
                text=f"Tool '{name}' execution failed: {e!s}", is_error=True
            )
    else:
        print(f"Tool '{name}' is unknown\r\n")
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
        "description": "Search for contact information in the CRM based on a query string. When to use: Use this tool when you need to find contact before creating the contact information in the CRM based on a query string. What to pass - phone number is better then the name. What is returned - contact information in JSON format. contact or null if not found.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for contact information.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_contact",
        "description": "Create a new contact in the CRM only if the find_contact return null. When to use: Use this tool when you need to create a new contact in the CRM. What to pass - name and phone number are required, email and company are optional. What is returned - the created contact information in JSON format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the contact to create.",
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
            "required": ["name", "phone"],
        },
    },
    {
        "name": "log_call_note",
        "description": "Log a call note in the CRM. When to use: Use this tool when you need to log a call in the CRM. What to pass - contact_id and summary are required. What is returned - the logged call note information in JSON format with the id",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "integer",
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
                    "type": "integer",
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

FAKE_CONTACTS = [
    {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+995555123456",
        "company": "Example Inc.",
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+0987654321",
        "company": "Sample Co.",
    },
    {
        "id": 3,
        "name": "John Lord",
        "email": "jl@example.com",
        "phone": "+1111111111",
        "company": "Test Ltd.",
    },
    {
        "id": 4,
        "name": "Jonny Depp",
        "email": "jonny.depp@example.com",
        "phone": "+2222222222",
        "company": "Demo Corp.",
    },
]

FAKE_NOTES = []
FAKE_TASKS = []
