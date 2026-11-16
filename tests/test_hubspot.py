from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from call_to_crm_agent.hubspot import (
    DEFAULT_TIMEZONE,
    from_hubspot_note_body,
    to_contact,
    to_hubspot_note_body,
    to_hubspot_task_timestamp,
    to_hubspot_timestamp,
    to_note,
    to_task,
)


def test_to_contact():
    hubspot_contact = {
        "id": "913573557440",
        "properties": {
            "company": None,
            "createdate": "2026-11-05T09:19:30.508Z",
            "email": None,
            "firstname": "Max",
            "hs_object_id": "913573557440",
            "lastmodifieddate": "2026-11-05T16:33:13.582Z",
            "lastname": "Smith",
            "phone": "+995599000999",
        },
        "createdAt": "2026-11-05T09:19:30.508Z",
        "updatedAt": "2026-11-05T16:33:13.582Z",
        "archived": False,
        "url": "https://app-eu1.hubspot.com/contacts/149704043/record/0-1/913573557440",
    }
    contact = to_contact(hubspot_contact)

    assert contact.first_name == "Max"
    assert contact.last_name == "Smith"
    assert contact.phone == "+995599000999"
    assert contact.id == "913573557440"
    assert contact.company is None
    assert contact.email is None


def test_to_contact_shrink():
    hubspot_contact = {
        "id": "913573557440",
        "properties": {
            "createdate": "2026-11-05T09:19:30.508Z",
            "firstname": "Max",
            "hs_object_id": "913573557440",
            "lastmodifieddate": "2026-11-05T16:33:13.582Z",
            "lastname": "Smith",
            "phone": "+995599000999",
        },
        "createdAt": "2026-11-05T09:19:30.508Z",
        "updatedAt": "2026-11-05T16:33:13.582Z",
        "archived": False,
    }
    contact = to_contact(hubspot_contact)

    assert contact.first_name == "Max"
    assert contact.last_name == "Smith"
    assert contact.phone == "+995599000999"
    assert contact.id == "913573557440"
    assert contact.company is None
    assert contact.email is None


def test_to_note():
    note_body = "Call date: 2026-11-12. Contact: John Doe. Company stated on call..."
    result = {
        "id": "543038495984",
        "properties": {
            "hs_createdate": "2026-11-12T11:26:04.121Z",
            "hs_note_body": note_body,
            "hs_object_id": "543038495984",
        },
        "createdAt": "2026-11-12T11:26:04.121Z",
        "updatedAt": "2026-11-12T11:26:04.121Z",
    }
    note = to_note(result, "912481268979")
    assert note.id == "543038495984"
    assert note.contact_id == "912481268979"
    assert note.summary == note_body


def test_to_task():
    result = {
        "id": "543091446976",
        "properties": {
            "hs_createdate": "2026-11-12T11:26:06.708Z",
            "hs_object_id": "543091446976",
            "hs_task_subject": "Send invoice for 10-seat annual plan to John Doe (Acme)",
            "hs_timestamp": "2026-11-13T05:00:00Z",
        },
        "createdAt": "2026-11-12T11:26:06.708Z",
        "updatedAt": "2026-11-12T11:26:06.708Z",
    }
    task = to_task(result, "912481268979", DEFAULT_TIMEZONE)
    assert task.id == "543091446976"
    assert task.contact_id == "912481268979"
    assert task.title == "Send invoice for 10-seat annual plan to John Doe (Acme)"
    assert task.due_date == date(2026, 11, 13)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (UTC, "1794477660000"),
        (ZoneInfo("Asia/Tbilisi"), "1794463260000"),
        (ZoneInfo("America/New_York"), "1794495660000"),
    ],
)
def test_to_hubspot_timestamp(raw, expected):
    assert to_hubspot_timestamp(datetime(2026, 11, 12, 10, 1, tzinfo=raw)) == expected


def test_to_hubspot_task_timestamp():
    assert (
        to_hubspot_task_timestamp(date(2026, 11, 13), DEFAULT_TIMEZONE)
        == "1794546000000"
    )


def test_to_hubspot_note_body():
    assert to_hubspot_note_body("R&D <5\nok") == "R&amp;D &lt;5<br>ok"


def test_from_hubspot_note():
    assert (
        from_hubspot_note_body("Plan suitable for a 20-person team.<br>Pain points:")
        == "Plan suitable for a 20-person team.\nPain points:"
    )


def test_note_body_round_trip():
    text = (
        "R&D team: <5 users\n"
        "Use </br> or <br> tags?\n"
        "\"Quotes\" & 'apostrophes'\n"
        "Анна, Blue Sky"
    )

    assert from_hubspot_note_body(to_hubspot_note_body(text)) == text
