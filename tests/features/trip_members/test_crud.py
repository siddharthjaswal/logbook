"""
Unit tests for TripMember CRUD operations.
"""

import pytest
from app.features.trip_members import crud
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.users import crud as users_crud
from app.features.users.schemas import UserCreate
from app.shared.enums import TripType, TripStatus, TripVisibility, MemberRole


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip with an owner."""
    trip_create = TripCreate(
        name="Collaboration Test Trip",
        primary_destination_country="France",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="EUR",
    )
    return trips_crud.create_trip(db, trip_create, user_id=test_user.id)


@pytest.fixture
def second_user(db):
    """Create a second test user."""
    user_create = UserCreate(
        google_id="test_google_id_456",
        email="second.user@example.com",
        first_name="Second",
        last_name="User",
        username="seconduser",
        email_verified=True
    )
    return users_crud.create_user(db, user_create)


@pytest.fixture
def third_user(db):
    """Create a third test user."""
    user_create = UserCreate(
        google_id="test_google_id_789",
        email="third.user@example.com",
        first_name="Third",
        last_name="User",
        username="thirduser",
        email_verified=True
    )
    return users_crud.create_user(db, user_create)


def test_trip_creator_is_auto_added_as_owner(db, test_trip, test_user):
    """Test that trip creator is automatically added as owner."""
    member = crud.get_member(db, test_trip.id, test_user.id)

    assert member is not None
    assert member.trip_id == test_trip.id
    assert member.user_id == test_user.id
    assert member.role == MemberRole.OWNER


def test_create_member(db, test_trip, second_user, test_user):
    """Test adding a new member to a trip."""
    member = crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR, test_user.id)

    assert member.id is not None
    assert member.trip_id == test_trip.id
    assert member.user_id == second_user.id
    assert member.role == MemberRole.EDITOR
    assert member.invited_by == test_user.id
    assert member.joined_at is not None


def test_create_duplicate_member_fails(db, test_trip, second_user, test_user):
    """Test that adding the same user twice fails."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    with pytest.raises(Exception):  # Should raise IntegrityError due to unique constraint
        crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)


def test_get_member(db, test_trip, second_user):
    """Test getting a member by trip and user ID."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    member = crud.get_member(db, test_trip.id, second_user.id)

    assert member is not None
    assert member.user_id == second_user.id


def test_get_member_not_found(db, test_trip, second_user):
    """Test getting a non-existent member returns None."""
    member = crud.get_member(db, test_trip.id, second_user.id)
    assert member is None


def test_get_trip_members(db, test_trip, second_user, third_user):
    """Test getting all members of a trip."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)
    crud.create_member(db, test_trip.id, third_user.id, MemberRole.VIEWER)

    members = crud.get_trip_members(db, test_trip.id)

    # Should include owner + 2 new members
    assert len(members) == 3

    roles = [m.role for m in members]
    assert MemberRole.OWNER in roles
    assert MemberRole.EDITOR in roles
    assert MemberRole.VIEWER in roles


def test_get_user_trips(db, test_trip, second_user):
    """Test getting all trips a user is a member of."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    # Create another trip
    trip2_create = TripCreate(
        name="Second Trip",
        primary_destination_country="Spain",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="EUR",
    )
    trip2 = trips_crud.create_trip(db, trip2_create, user_id=second_user.id)

    memberships = crud.get_user_trips(db, second_user.id)

    assert len(memberships) == 2
    trip_ids = [m.trip_id for m in memberships]
    assert test_trip.id in trip_ids
    assert trip2.id in trip_ids


def test_update_member_role(db, test_trip, second_user):
    """Test updating a member's role."""
    member = crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    updated_member = crud.update_member_role(db, member, MemberRole.EDITOR)

    assert updated_member.role == MemberRole.EDITOR


def test_remove_member(db, test_trip, second_user):
    """Test removing a member from a trip."""
    member = crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    crud.remove_member(db, member)

    # Member should no longer exist
    removed_member = crud.get_member(db, test_trip.id, second_user.id)
    assert removed_member is None


def test_is_trip_owner(db, test_trip, test_user, second_user):
    """Test checking if a user is a trip owner."""
    assert crud.is_trip_owner(db, test_trip.id, test_user.id) is True
    assert crud.is_trip_owner(db, test_trip.id, second_user.id) is False


def test_is_trip_member(db, test_trip, test_user, second_user):
    """Test checking if a user is a trip member."""
    assert crud.is_trip_member(db, test_trip.id, test_user.id) is True
    assert crud.is_trip_member(db, test_trip.id, second_user.id) is False

    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)
    assert crud.is_trip_member(db, test_trip.id, second_user.id) is True


def test_has_edit_permission(db, test_trip, second_user, third_user):
    """Test checking edit permissions."""
    # Create editor and viewer
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)
    crud.create_member(db, test_trip.id, third_user.id, MemberRole.VIEWER)

    assert crud.has_edit_permission(db, test_trip.id, second_user.id) is True
    assert crud.has_edit_permission(db, test_trip.id, third_user.id) is False


def test_has_view_permission(db, test_trip, second_user):
    """Test checking view permissions."""
    assert crud.has_view_permission(db, test_trip.id, second_user.id) is False

    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)
    assert crud.has_view_permission(db, test_trip.id, second_user.id) is True


def test_check_member_permission_viewer(db, test_trip, second_user):
    """Test permission checking for viewer role."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.VIEWER)

    # Viewer should have viewer permission
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.VIEWER) is True

    # Viewer should NOT have editor permission
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.EDITOR) is False

    # Viewer should NOT have owner permission
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.OWNER) is False


def test_check_member_permission_editor(db, test_trip, second_user):
    """Test permission checking for editor role."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)

    # Editor should have viewer and editor permissions
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.VIEWER) is True
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.EDITOR) is True

    # Editor should NOT have owner permission
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.OWNER) is False


def test_check_member_permission_owner(db, test_trip, test_user):
    """Test permission checking for owner role."""
    # Owner should have all permissions
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.VIEWER) is True
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.EDITOR) is True
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.OWNER) is True


def test_multiple_owners_scenario(db, test_trip, test_user, second_user):
    """Test having multiple owners in a trip."""
    # Add second owner
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.OWNER)

    # Both users should have owner permissions
    assert crud.is_trip_owner(db, test_trip.id, test_user.id) is True
    assert crud.is_trip_owner(db, test_trip.id, second_user.id) is True


def test_member_count_with_filters(db, test_trip, second_user, third_user):
    """Test counting members by role."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)
    crud.create_member(db, test_trip.id, third_user.id, MemberRole.VIEWER)

    # Get all members
    all_members = crud.get_trip_members(db, test_trip.id)
    assert len(all_members) == 3  # Owner + Editor + Viewer

    # Get members by role
    owners = crud.get_members_by_role(db, test_trip.id, MemberRole.OWNER)
    editors = crud.get_members_by_role(db, test_trip.id, MemberRole.EDITOR)
    viewers = crud.get_members_by_role(db, test_trip.id, MemberRole.VIEWER)

    assert len(owners) == 1
    assert len(editors) == 1
    assert len(viewers) == 1


def test_get_members_by_role(db, test_trip, second_user, third_user):
    """Test getting members filtered by role."""
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)
    crud.create_member(db, test_trip.id, third_user.id, MemberRole.VIEWER)

    editors = crud.get_members_by_role(db, test_trip.id, MemberRole.EDITOR)
    assert len(editors) == 1
    assert editors[0].user_id == second_user.id

    viewers = crud.get_members_by_role(db, test_trip.id, MemberRole.VIEWER)
    assert len(viewers) == 1
    assert viewers[0].user_id == third_user.id


def test_role_hierarchy_through_permissions(db, test_trip, test_user, second_user, third_user):
    """Test that role hierarchy works correctly through permission checks."""
    # Create members with different roles
    crud.create_member(db, test_trip.id, second_user.id, MemberRole.EDITOR)
    crud.create_member(db, test_trip.id, third_user.id, MemberRole.VIEWER)

    # Owner should have all permissions
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.VIEWER) is True
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.EDITOR) is True
    assert crud.check_member_permission(db, test_trip.id, test_user.id, MemberRole.OWNER) is True

    # Editor should have viewer + editor permissions
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.VIEWER) is True
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.EDITOR) is True
    assert crud.check_member_permission(db, test_trip.id, second_user.id, MemberRole.OWNER) is False

    # Viewer should only have viewer permission
    assert crud.check_member_permission(db, test_trip.id, third_user.id, MemberRole.VIEWER) is True
    assert crud.check_member_permission(db, test_trip.id, third_user.id, MemberRole.EDITOR) is False
    assert crud.check_member_permission(db, test_trip.id, third_user.id, MemberRole.OWNER) is False
