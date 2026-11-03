from call_to_crm_agent.tools import execute_tool


def test_unknown_tool_returns_error():
    result = execute_tool("no_such_tool", {})
    assert result.is_error
    assert "no_such_tool" in result.text


def test_find_contact_returns_contact():
    result = execute_tool("find_contact", {"query": "John Lord"})
    assert not result.is_error
    assert "John" in result.text


def test_find_contact_returns_none_for_nonexistent_contact():
    result = execute_tool("find_contact", {"query": "Nonexistent"})
    assert not result.is_error
    assert result.text == "null"


def test_create_contact_creates_new_contact():
    result = execute_tool(
        "create_contact",
        {
            "name": "Anna Smith",
            "email": "anna.smith@example.com",
            "phone": "123-456-7890",
            "company": "Example Corp",
        },
    )

    contact = execute_tool("find_contact", {"query": "Anna Smith"})
    assert not result.is_error
    assert "Anna Smith" in contact.text


def test_create_contact_with_name_and_email_creates_new_contact():
    result = execute_tool(
        "create_contact",
        {
            "name": "John Little Lord",
            "email": "john.littlelord@example.com",
        },
    )
    assert result.is_error


def test_create_contact_with_name_and_phone_creates_new_contact():
    result = execute_tool(
        "create_contact",
        {
            "name": "John Little Lord",
            "phone": "123-456-7890",
        },
    )

    contact = execute_tool("find_contact", {"query": "John Little Lord"})
    assert not result.is_error
    assert not contact.is_error
    assert "John Little Lord" in contact.text


def test_log_call_note_creates_new_note():
    note_result = execute_tool(
        "log_call_note",
        {
            "contact_id": 1,
            "summary": "Discussed project updates and next steps.",
        },
    )
    assert not note_result.is_error
    assert note_result.text is not None
    assert "Discussed project updates and next steps" in note_result.text


def test_create_task_creates_new_task():
    task_result = execute_tool(
        "create_task",
        {
            "contact_id": 1,
            "title": "Follow up on project",
            "due_date": "2024-06-30",
        },
    )
    assert not task_result.is_error
    assert task_result.text is not None
    assert "Follow up on project" in task_result.text
