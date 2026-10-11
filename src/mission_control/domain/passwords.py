MIN_PASSWORD_LENGTH = 15


class PasswordTooShort(ValueError):
    pass


def validate_password(password: str) -> None:
    """Length is the only rule: no character-type requirements, so passphrases work."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShort(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
