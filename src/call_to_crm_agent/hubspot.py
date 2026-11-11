from datetime import date

import httpx

from call_to_crm_agent.crm import Contact, Note, Task
from call_to_crm_agent.phones import to_e164, to_search_key


def to_contact(result: dict) -> Contact:
    contact_id = result["id"]
    contact_url = result.get("url") or None
    properties = result["properties"]
    return Contact(
        id=contact_id,
        first_name=properties.get("firstname") or "",
        last_name=properties.get("lastname") or "",
        phone=properties.get("phone") or "",
        company=properties.get("company") or None,
        email=properties.get("email") or None,
        url=contact_url,
    )


class HubSpotClient:
    client: httpx.Client

    def __init__(self, token: str):
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
        }

        self.client = httpx.Client(
            base_url=self.base_url, headers=self.headers, timeout=10.0
        )

    def search_contacts_by_phone(self, phone: str) -> list[dict]:
        url = "/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "hs_searchable_calculated_phone_number",
                            "operator": "EQ",
                            "value": phone,
                        }
                    ]
                }
            ],
            "properties": ["firstname", "lastname", "phone", "email", "company"],
            "limit": 5,
        }

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("results", [])

    def create_contact(self, properties: dict[str, str]) -> dict:
        url = "/crm/v3/objects/contacts"
        payload = {"properties": properties}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


class HubSpotCRM:
    def __init__(self, client: HubSpotClient):
        self.client = client

    def find_contacts(self, phone: str) -> list[Contact]:
        phone_to_search = to_search_key(phone)
        results = self.client.search_contacts_by_phone(phone_to_search)
        return [to_contact(r) for r in results]

    def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str | None = None,
        company: str | None = None,
    ) -> Contact:
        properties = {
            "firstname": first_name,
            "lastname": last_name,
            "phone": to_e164(phone),
        }

        if email and email.strip():
            properties["email"] = email

        if company and company.strip():
            properties["company"] = company

        result = self.client.create_contact(properties)
        return to_contact(result)

    def log_call_note(self, contact_id: str, summary: str) -> Note:
        raise NotImplementedError

    def create_task(self, contact_id: str, title: str, due_date: date) -> Task:
        raise NotImplementedError
