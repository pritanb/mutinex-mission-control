"""M16: the credentials file. Kept at mode 0600, replaced atomically, and treated as logged out
when missing or unreadable (design §8)."""

import stat

from mission_control.cli.config import (
    DEFAULT_API_URL,
    Credentials,
    CredentialStore,
    api_url,
    default_config_dir,
)


def test_m16_credentials_live_under_the_users_config_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    assert default_config_dir() == tmp_path / ".config" / "mission-control"
    assert CredentialStore(default_config_dir()).path == (
        tmp_path / ".config" / "mission-control" / "credentials.json"
    )


def test_m16_credentials_file_is_readable_only_by_the_user(tmp_path):
    store = CredentialStore(tmp_path / "cfg")

    store.save(Credentials(token="secret", email="lee@aurora.example", expires_at=None))

    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700
    assert store.load() == Credentials("secret", "lee@aurora.example", None)


def test_m16_saving_tightens_a_file_that_was_left_readable(tmp_path):
    store = CredentialStore(tmp_path)
    store.path.write_text("{}")
    store.path.chmod(0o644)

    store.save(Credentials(token="secret", email="lee@aurora.example"))

    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert not list(tmp_path.glob("*.tmp"))


def test_m16_missing_or_corrupt_credentials_mean_logged_out(tmp_path):
    store = CredentialStore(tmp_path)
    assert store.load() is None

    store.path.write_text("not json")
    assert store.load() is None

    store.path.write_text('{"email": "lee@aurora.example"}')
    assert store.load() is None


def test_m16_clearing_is_safe_when_already_logged_out(tmp_path):
    store = CredentialStore(tmp_path)
    store.clear()
    store.save(Credentials(token="secret", email="lee@aurora.example"))

    store.clear()

    assert not store.path.exists()


def test_m16_api_url_defaults_to_the_local_server(monkeypatch):
    monkeypatch.delenv("MC_API_URL", raising=False)
    assert api_url() == DEFAULT_API_URL == "http://127.0.0.1:8000"

    monkeypatch.setenv("MC_API_URL", "http://127.0.0.1:8016/")
    assert api_url() == "http://127.0.0.1:8016"
