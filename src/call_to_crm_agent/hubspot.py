import html
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from time import sleep as system_sleep
from zoneinfo import ZoneInfo

import httpx

from call_to_crm_agent.crm import Contact, Note, Task
from call_to_crm_agent.phones import to_e164, to_search_key

TASK_DUE_TIME = time(9)
DEFAULT_TIMEZONE = ZoneInfo("Asia/Tbilisi")
ASSOCIATIONTYPEID_NOTE = 202
ASSOCIATIONTYPEID_TASK = 204
MAX_ATTEMPTS = 3
MAX_RETRY_DELAY = 10.0


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


def to_note(result: dict, contact_id: str) -> Note:
    note_id = result["id"]
    properties = result["properties"]
    return Note(
        id=note_id,
        contact_id=contact_id,
        summary=from_hubspot_note_body(properties["hs_note_body"]),
    )


def to_task(result: dict, contact_id: str, timezone: ZoneInfo) -> Task:
    task_id = result["id"]
    properties = result["properties"]
    return Task(
        id=task_id,
        contact_id=contact_id,
        title=properties["hs_task_subject"],
        due_date=datetime.fromisoformat(properties["hs_timestamp"])
        .astimezone(timezone)
        .date(),
    )


class HubSpotClient:
    client: httpx.Client
    sleep: Callable[[float], None]

    def __init__(
        self,
        token: str,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = system_sleep,
    ):
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
        }

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=10.0,
            transport=transport,
        )

        self.sleep = sleep

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        try:
            return float(response.headers["Retry-After"])
        except KeyError, ValueError:
            return float(2**attempt)

    def _post(self, url: str, payload: dict) -> httpx.Response:
        response: httpx.Response | None = None

        for attempt in range(MAX_ATTEMPTS):
            response = self.client.post(url, json=payload)

            if response.status_code != 429:
                break

            if attempt < MAX_ATTEMPTS - 1:
                delay = self._retry_delay(response, attempt)
                if delay > MAX_RETRY_DELAY:
                    break
                self.sleep(delay)

        assert response is not None
        raise_for_hubspot_error(response)
        return response

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

        response = self._post(url, payload)
        return response.json().get("results", [])

    def create_contact(self, properties: dict[str, str]) -> dict:
        url = "/crm/v3/objects/contacts"
        payload = {"properties": properties}

        response = self._post(url, payload)
        return response.json()

    def create_call_note(self, contact_id: str, timestamp: str, note_body: str) -> dict:
        url = "/crm/v3/objects/notes"
        payload = {
            "properties": {"hs_note_body": note_body, "hs_timestamp": timestamp},
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": ASSOCIATIONTYPEID_NOTE,
                        }
                    ],
                }
            ],
        }
        response = self._post(url, payload)
        return response.json()

    def create_default_task(
        self, contact_id: str, timestamp: str, subject: str
    ) -> dict:
        url = "/crm/v3/objects/tasks"
        payload = {
            "properties": {
                "hs_task_subject": subject,
                "hs_timestamp": timestamp,
                "hs_task_status": "NOT_STARTED",
                "hs_task_type": "TODO",
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": ASSOCIATIONTYPEID_TASK,
                        }
                    ],
                }
            ],
        }
        response = self._post(url, payload)
        return response.json()


class HubSpotCRM:
    def __init__(self, client: HubSpotClient, timezone: ZoneInfo = DEFAULT_TIMEZONE):
        self.client = client
        self.timezone = timezone

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
        timestamp: str = to_hubspot_timestamp(datetime.now(UTC))
        result = self.client.create_call_note(
            contact_id, timestamp, to_hubspot_note_body(summary)
        )
        return to_note(result, contact_id)

    def create_task(self, contact_id: str, title: str, due_date: date) -> Task:
        timestamp: str = to_hubspot_task_timestamp(due_date, self.timezone)
        result = self.client.create_default_task(contact_id, timestamp, title)
        return to_task(result, contact_id, self.timezone)


class HubSpotError(Exception):
    status_code: int
    message: str

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HubSpot {status_code}: {message}")


def raise_for_hubspot_error(response: httpx.Response) -> None:
    if response.is_success:
        return

    try:
        data = response.json()
        if isinstance(data, dict) and "message" in data:
            error_msg = str(data["message"])
        else:
            error_msg = str(data)[:300]
    except ValueError:
        raw_text = response.text.strip()
        if len(raw_text) > 300:
            error_msg = raw_text[:300] + "..."
        else:
            error_msg = raw_text or "Empty response body"

    raise HubSpotError(status_code=response.status_code, message=error_msg)


def to_hubspot_timestamp(dt: datetime) -> str:
    return str(int(dt.timestamp() * 1000))


def to_hubspot_task_timestamp(dt: date, timezone: ZoneInfo) -> str:
    return to_hubspot_timestamp(datetime.combine(dt, TASK_DUE_TIME, tzinfo=timezone))


def to_hubspot_note_body(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def from_hubspot_note_body(text: str) -> str:
    return html.unescape(text.replace("<br>", "\n"))
