from dataclasses import dataclass
from datetime import date
from typing import Protocol

from call_to_crm_agent.phones import to_e164, to_search_key


@dataclass
class Contact:
    id: str
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    company: str | None = None
    url: str | None = None


@dataclass
class Note:
    id: str
    contact_id: str
    summary: str


@dataclass
class Task:
    id: str
    contact_id: str
    title: str
    due_date: date


class CRM(Protocol):
    def find_contacts(self, phone: str) -> list[Contact]: ...

    def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str | None = None,
        company: str | None = None,
    ) -> Contact: ...

    def log_call_note(self, contact_id: str, summary: str) -> Note: ...

    def create_task(self, contact_id: str, title: str, due_date: date) -> Task: ...


class FakeCRM:
    def __init__(self, contacts: list[Contact] | None = None):
        self.contacts = list(contacts or [])
        self.notes: list[Note] = []
        self.tasks: list[Task] = []

    def find_contacts(self, phone: str) -> list[Contact]:
        search_key = to_search_key(phone)
        return [
            contact
            for contact in self.contacts
            if to_search_key(contact.phone) == search_key
        ]

    def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str | None = None,
        company: str | None = None,
    ) -> Contact:
        contact = Contact(
            id=str(len(self.contacts) + 1),
            first_name=first_name,
            last_name=last_name,
            phone=str(to_e164(phone)),
            email=email,
            company=company,
        )

        self.contacts.append(contact)

        return contact

    def log_call_note(self, contact_id: str, summary: str) -> Note:
        note = Note(
            id=str(len(self.notes) + 1),
            contact_id=contact_id,
            summary=summary,
        )

        self.notes.append(note)

        return note

    def create_task(self, contact_id: str, title: str, due_date: date) -> Task:
        task = Task(
            id=str(len(self.tasks) + 1),
            contact_id=contact_id,
            title=title,
            due_date=due_date,
        )

        self.tasks.append(task)

        return task
