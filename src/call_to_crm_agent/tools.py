FAKE_CONTACTS = [
    {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+995555123456",
        "company": "Example Inc.",
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+0987654321",
        "company": "Sample Co.",
    },
    {
        "id": 3,
        "name": "John Lord",
        "email": "jl@example.com",
        "phone": "+1111111111",
        "company": "Test Ltd.",
    },
    {
        "id": 4,
        "name": "Jonny Depp",
        "email": "jonny.depp@example.com",
        "phone": "+2222222222",
        "company": "Demo Corp.",
    },
]


def find_contact(query: str) -> dict | None:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return None

    for contact in FAKE_CONTACTS:
        if any(normalized_query in str(value).casefold() for value in contact.values()):
            return contact

    return None


TOOLS = [
    {
        "name": "find_contact",
        "description": "Search for contact information in the CRM based on a query string. When to use: Use this tool when you need to find contact before creating the contact information in the CRM based on a query string. What to pass - phone number is better then the name. What is returned - contact information in JSON format. contact or null if not found.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for contact information.",
                },
            },
            "required": ["query"],
        },
    }
]
