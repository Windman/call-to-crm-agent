import pytest

from call_to_crm_agent.phones import to_e164, to_search_key


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+995 599 000 999", "+995599000999"),  # Грузия, с пробелами
        ("+1 650-253-0000", "+16502530000"),  # США, с дефисами
        ("+995 555 12 34 56", "+995555123456"),
    ],
)
def test_to_e164(raw, expected):
    assert to_e164(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "abc",  # не номер
        "654-123-4567",  # нет кода страны
        "+800-123-4567",  # разбирается, но невалиден
        "+995 899 000 999",  # Грузия, но не мобильный формат
    ],
)
def test_invalid_numbers_raise(raw):
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_e164(raw)
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_search_key(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+995 555 123 456", "555123456"),
        ("+1 650-253-0000", "6502530000"),
    ],
)
def test_to_search_key(raw, expected):
    result = to_search_key(raw)
    assert result == expected


@pytest.mark.parametrize(
    "raw",
    [
        "abc",  # не номер
        "654-123-4567ss",  # нет кода страны
        "+800-123-4567ss",  # разбирается, но невалиден
        "+995 899 000 999",  # Грузия, но не мобильный формат
    ],
)
def test_to_search_key_invalid(raw):
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_search_key(raw)
