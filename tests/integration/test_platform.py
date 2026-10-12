"""Platform statements (design §2, §11): the organisation lookups and writes `mc-admin create-org`
makes before any tenant exists to scope by."""

from mission_control.infra import platform
from mission_control.infra.db import write_tx
from mission_control.infra.repositories import Repos


def test_t3_create_organisation_adds_a_tenant_with_the_default_approvals(conn):
    with write_tx(conn):
        org_id = platform.create_organisation(conn, "Orion Labs", "orion-labs")

    org = Repos(conn, org_id).organisation.get()
    assert (org.name, org.slug, org.required_approvals) == ("Orion Labs", "orion-labs", 1)


def test_t3_organisation_with_slug_finds_the_name_across_every_tenant(seeded_db):
    with write_tx(seeded_db):
        platform.create_organisation(seeded_db, "Orion Labs", "orion-labs")

    assert platform.organisation_with_slug(seeded_db, "orion-labs") == "Orion Labs"
    assert platform.organisation_with_slug(seeded_db, "helix") == "Helix Orbital"
    assert platform.organisation_with_slug(seeded_db, "nobody") is None
