import json

from call_to_crm_agent.tools import execute_tool


def test_unknown_tool_returns_error(crm):
    result = execute_tool(crm, "no_such_tool", {})
    assert result.is_error
    assert "no_such_tool" in result.text


def test_find_contact_returns_contact(crm):
    result = execute_tool(crm, "find_contact", {"phone": "+995 555 12 34 56"})
    assert not result.is_error
    assert "John" in result.text


def test_find_contact_invalid_phone_returns_error(crm):
    result = execute_tool(crm, "find_contact", {"phone": "Nonexistent"})
    assert result.is_error


def test_find_contact_valid_phone_returns_error(crm):
    result = execute_tool(crm, "find_contact", {"phone": "+1 650-253-0000"})
    assert json.loads(result.text) == []


def test_create_contact_creates_new_contact(crm):
    result = execute_tool(
        crm,
        "create_contact",
        {
            "first_name": "Anna",
            "last_name": "Smith",
            "email": "anna.smith@example.com",
            "phone": "+15875302271",
            "company": "Example Corp",
        },
    )

    contact = execute_tool(crm, "find_contact", {"phone": "+15875302271"})
    assert not result.is_error
    assert "Smith" in contact.text
    assert crm.contacts[-1].phone == "+15875302271"


def test_create_contact_without_phone_returns_error(crm):
    result = execute_tool(
        crm,
        "create_contact",
        {
            "first_name": "John",
            "last_name": "Little Lord",
            "email": "john.littlelord@example.com",
        },
    )
    assert result.is_error


def test_create_contact_with_name_and_phone_creates_new_contact(crm):
    result = execute_tool(
        crm,
        "create_contact",
        {
            "first_name": "John",
            "last_name": "Little Lord",
            "phone": "+15875302271",
        },
    )

    contact = execute_tool(crm, "find_contact", {"phone": "+1 587 530 2271"})
    assert not result.is_error
    assert not contact.is_error
    assert "Little" in contact.text


def test_log_call_note_creates_new_note(crm):
    note_result = execute_tool(
        crm,
        "log_call_note",
        {
            "contact_id": "1",
            "summary": "Discussed project updates and next steps.",
        },
    )
    assert not note_result.is_error
    assert note_result.text is not None
    assert "Discussed project updates and next steps" in note_result.text


def test_create_task_creates_new_task(crm):
    task_result = execute_tool(
        crm,
        "create_task",
        {
            "contact_id": "1",
            "title": "Follow up on project",
            "due_date": "2024-06-30",
        },
    )
    assert not task_result.is_error
    assert task_result.text is not None
    assert "Follow up on project" in task_result.text


def test_create_task_with_bad_due_date(crm):
    task_result = execute_tool(
        crm,
        "create_task",
        {
            "contact_id": "1",
            "title": "Follow up on project",
            "due_date": "Thursday",
        },
    )
    assert task_result.is_error
    assert crm.tasks == []
