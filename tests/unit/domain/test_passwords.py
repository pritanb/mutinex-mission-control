import pytest

from mission_control.domain.passwords import (
    MIN_PASSWORD_LENGTH,
    PasswordTooShort,
    validate_password,
)


def test_p10_minimum_length_is_15():
    assert MIN_PASSWORD_LENGTH == 15


def test_p10_14_characters_is_rejected():
    with pytest.raises(PasswordTooShort):
        validate_password("a" * 14)


def test_p10_15_characters_is_accepted():
    validate_password("a" * 15)


def test_p10_all_lowercase_passphrase_with_spaces_is_accepted():
    validate_password("correct horse battery staple")


def test_p10_no_character_type_rules():
    validate_password("aaaaaaaaaaaaaaaaaaaa")  # no uppercase, digits or symbols


def test_p10_empty_password_is_rejected():
    with pytest.raises(PasswordTooShort):
        validate_password("")


def test_p10_password_too_short_is_a_value_error():
    with pytest.raises(ValueError):
        validate_password("short")
