from call_to_crm_agent.hubspot import to_contact


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
