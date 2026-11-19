from call_to_crm_agent.crm import Contact, FakeCRM


def build_fake_crm() -> FakeCRM:
    return FakeCRM(
        [
            Contact(
                id="1",
                first_name="John",
                last_name="Doe",
                phone="+995555123456",
                email="john.doe@example.com",
                company="Example Inc.",
            )
        ]
    )
