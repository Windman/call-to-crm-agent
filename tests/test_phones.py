import pytest

from call_to_crm_agent.phones import to_e164, to_search_key


def test_to_e164():
    result = to_e164("+995 599 000 999")
    assert result == "+995599000999"


def test_to_e164_2():
    result = to_e164("+1 650-253-0000")
    assert result == "+16502530000"


def test_to_e164_invalid():
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_e164("+800-123-4567ss")


def test_to_e164_invalid2():
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_e164("654-123-4567ss")


def test_to_e164_invalid3():
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_e164("+995 899 000 999")


def test_to_search_key():
    result = to_search_key("+1 650-253-0000")
    assert result == "6502530000"


def test_to_search_key_invalid():
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_search_key("abc")


def test_to_search_key_invalid2():
    with pytest.raises(ValueError, match="Invalid phone number"):
        to_search_key("+800-123-4567ss")


def test_to_search_key_valid():
    result = to_search_key("+995 555 123 456")
    assert result == "555123456"
