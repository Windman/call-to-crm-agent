"""Проверка доступа к HubSpot: ключ из .env, права на чтение контактов.

Запуск: uv run python scripts/check_hubspot.py
Ключ не печатается — только статус ответа и первые контакты.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("HUBSPOT_TOKEN", "")
if not token:
    raise SystemExit("HUBSPOT_TOKEN не найден в .env")

response = httpx.get(
    "https://api.hubapi.com/crm/v3/objects/contacts",
    params={"limit": 5, "properties": "firstname,lastname,phone,email,company"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)

print("HTTP status:", response.status_code)
if response.is_success:
    for contact in response.json().get("results", []):
        print(contact["id"], contact["properties"])
else:
    # 401 — неверный ключ; 403 — у ключа нет нужного scope (HubSpot перечислит какие)
    print(response.text)
