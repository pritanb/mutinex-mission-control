from collections.abc import Generator

import pytest
from cli_fakes import FakeApi, Mc


@pytest.fixture(autouse=True)
def _no_ambient_terminal_settings(monkeypatch):
    """The developer's own NO_COLOR, TERM or API URL must not change what the tests see."""
    for name in ("NO_COLOR", "TERM", "MC_API_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def api() -> Generator[FakeApi]:
    """The scripted API. Fails the test if it sent a response the real API couldn't."""
    fake = FakeApi()
    yield fake
    assert not fake.drift, "Fake responses don't match the real API:\n" + "\n".join(fake.drift)


@pytest.fixture
def mc(api, tmp_path) -> Mc:
    return Mc(api=api, config_dir=tmp_path / "config")
