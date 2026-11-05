from dataclasses import dataclass

import httpx


@dataclass
class HubSpotCreateContactRequest:
    firstname: str
    lastname: str
    phone: str
    email: str
    company: str


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
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
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

    def create_contact(self, properties: HubSpotCreateContactRequest) -> dict:
        url = f"{self.base_url}/crm/v3/objects/contacts"
        payload = {"properties": properties}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
