import pytest

from call_to_crm_agent.crm import Contact, FakeCRM


@pytest.fixture
def crm() -> FakeCRM:
    return FakeCRM(
        [
            Contact(
                id="1",
                first_name="John",
                last_name="Doe",
                phone="+995555123456",
                company="Example Inc.",
            )
        ]
    )
