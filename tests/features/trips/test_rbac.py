"""
Role-based access control (RBAC) tests for trip resources.

Covers the authorization matrix enforced via check_trip_permission:
- reads require VIEWER, writes require EDITOR, trip delete requires OWNER
- trip members can access private trips they belong to
- non-members are denied (404 on lookup)

Uses the activities endpoint as a representative child resource.
"""

import pytest

from app.core.security import create_access_token
from app.features.trip_members import crud as member_crud
from app.shared.enums import MemberRole


def headers_for(user):
    """Build auth headers for an arbitrary user."""
    token = create_access_token(data={"sub": user.id})
    return {"Authorization": f"Bearer {token}"}


def add_member(db, trip_id, user_id, role):
    member_crud.create_member(db, trip_id, user_id, role)


def activity_payload(trip_id):
    return {
        "trip_id": trip_id,
        "activity_date": "2024-06-02",
        "name": "Test Activity",
        "activity_type": "sightseeing",
    }


# ── Read access (member-aware) ──────────────────────────────────────────

def test_non_member_cannot_read_private_trip(client, db, test_trip, test_other_user):
    """A user with no membership gets 404 for a private trip."""
    resp = client.get(f"/api/v1/trips/{test_trip.id}", headers=headers_for(test_other_user))
    assert resp.status_code == 404


def test_viewer_member_can_read_private_trip(client, db, test_trip, test_other_user):
    """A VIEWER member can read a private trip (regression: members were 404'd)."""
    add_member(db, test_trip.id, test_other_user.id, MemberRole.VIEWER)
    resp = client.get(f"/api/v1/trips/{test_trip.id}", headers=headers_for(test_other_user))
    assert resp.status_code == 200
    assert resp.json()["id"] == test_trip.id


# ── Write access (EDITOR) ───────────────────────────────────────────────

def test_owner_can_create_activity(client, auth_headers, test_trip):
    resp = client.post("/api/v1/activities/", json=activity_payload(test_trip.id), headers=auth_headers)
    assert resp.status_code == 201


def test_editor_member_can_create_activity(client, db, test_trip, test_other_user):
    add_member(db, test_trip.id, test_other_user.id, MemberRole.EDITOR)
    resp = client.post(
        "/api/v1/activities/", json=activity_payload(test_trip.id), headers=headers_for(test_other_user)
    )
    assert resp.status_code == 201


def test_viewer_member_cannot_create_activity(client, db, test_trip, test_other_user):
    """VIEWER can read but not write → 403."""
    add_member(db, test_trip.id, test_other_user.id, MemberRole.VIEWER)
    resp = client.post(
        "/api/v1/activities/", json=activity_payload(test_trip.id), headers=headers_for(test_other_user)
    )
    assert resp.status_code == 403


def test_non_member_cannot_create_activity(client, db, test_trip, test_other_user):
    """No membership on a private trip → 404 at lookup."""
    resp = client.post(
        "/api/v1/activities/", json=activity_payload(test_trip.id), headers=headers_for(test_other_user)
    )
    assert resp.status_code == 404


# ── Owner-only (DELETE trip) ────────────────────────────────────────────

def test_editor_cannot_delete_trip(client, db, test_trip, test_other_user):
    """EDITOR can edit content but not delete the trip → 403."""
    add_member(db, test_trip.id, test_other_user.id, MemberRole.EDITOR)
    resp = client.delete(f"/api/v1/trips/{test_trip.id}", headers=headers_for(test_other_user))
    assert resp.status_code == 403


def test_owner_can_delete_trip(client, auth_headers, test_trip):
    resp = client.delete(f"/api/v1/trips/{test_trip.id}", headers=auth_headers)
    assert resp.status_code == 200
