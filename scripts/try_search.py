import os
import time

from dotenv import load_dotenv

from call_to_crm_agent.hubspot import HubSpotClient
from call_to_crm_agent.phones import to_e164, to_search_key

load_dotenv()
token = os.environ.get("HUBSPOT_TOKEN", "")
if not token:
    raise SystemExit("HUBSPOT_TOKEN не найден в .env")

client = HubSpotClient(token)

phone_number_raw = "+995 599 000 999"

client.create_contact(
    {
        "firstname": "Test",
        "lastname": "User",
        "phone": to_e164(phone_number_raw),
        "email": "test.user@example.com",
        "company": "Test Company",
    }
)

time.sleep(10)  # Wait for the contact to be created

contact = client.search_contacts_by_phone(to_search_key(phone_number_raw))
print("contacts found:", contact)
