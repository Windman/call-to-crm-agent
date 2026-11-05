import phonenumbers


def to_e164(phone: str) -> str:
    return phonenumbers.format_number(
        _parse(phone), phonenumbers.PhoneNumberFormat.E164
    )


def to_search_key(phone: str) -> str:
    return str(_parse(phone).national_number)


def _parse(phone) -> phonenumbers.PhoneNumber:
    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(f"Invalid phone number: {phone}")
        return parsed
    except phonenumbers.NumberParseException:
        raise ValueError(f"Invalid phone number: {phone}")
