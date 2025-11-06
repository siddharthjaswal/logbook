# TripCollaborator Entity

## Overview
The TripCollaborator entity represents the many-to-many relationship between Users and Trips, enabling collaborative trip planning. Each collaborator has a specific role (owner, editor, viewer) that determines their permissions.

## Database Table: `trip_collaborators`

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique collaborator record identifier |
| `trip_id` | BIGINT | FOREIGN KEY (trips.id), NOT NULL, ON DELETE CASCADE | Associated trip |
| `user_id` | BIGINT | FOREIGN KEY (users.id), NOT NULL, ON DELETE CASCADE | Associated user |
| `role` | collaborator_role | NOT NULL, DEFAULT 'viewer' | User's role for this trip |
| `invited_by` | BIGINT | FOREIGN KEY (users.id), NULLABLE, ON DELETE SET NULL | User who sent the invitation |
| `invited_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When invitation was sent |
| `accepted_at` | TIMESTAMP | NULLABLE | When invitation was accepted |
| `invitation_status` | VARCHAR(20) | DEFAULT 'accepted' | Status: 'pending', 'accepted', 'declined', 'removed' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

### Enums

```sql
CREATE TYPE collaborator_role AS ENUM (
    'owner',    -- Full control: can delete trip, manage collaborators, edit everything
    'editor',   -- Can edit trip details, days, expenses (cannot manage collaborators)
    'viewer'    -- Read-only access to trip
);
```

### Constraints

```sql
-- Unique: One user can only have one role per trip
ALTER TABLE trip_collaborators
    ADD CONSTRAINT unique_trip_user UNIQUE (trip_id, user_id);

-- At least one owner required (enforced by application logic)
```

### Indexes

```sql
-- Lookup user's trips
CREATE INDEX idx_trip_collaborators_user_id ON trip_collaborators(user_id);

-- Lookup trip's collaborators
CREATE INDEX idx_trip_collaborators_trip_id ON trip_collaborators(trip_id);

-- Role-based queries
CREATE INDEX idx_trip_collaborators_role ON trip_collaborators(trip_id, role);

-- Pending invitations
CREATE INDEX idx_trip_collaborators_pending ON trip_collaborators(user_id, invitation_status)
    WHERE invitation_status = 'pending';
```

## Relationships

- **trip**: Many-to-One with Trip (CASCADE on delete)
- **user**: Many-to-One with User (CASCADE on delete)
- **invited_by**: Many-to-One with User (SET NULL on delete)

## Business Rules

### Role Permissions

#### Owner
- ✅ View trip
- ✅ Edit trip details
- ✅ Create/edit/delete trip days
- ✅ Create/edit/delete expenses
- ✅ Upload/delete photos
- ✅ Invite collaborators
- ✅ Change collaborator roles
- ✅ Remove collaborators
- ✅ Delete trip
- ✅ Change trip visibility

#### Editor
- ✅ View trip
- ✅ Edit trip details
- ✅ Create/edit/delete trip days
- ✅ Create/edit/delete expenses
- ✅ Upload photos
- ❌ Invite collaborators
- ❌ Change collaborator roles
- ❌ Remove collaborators
- ❌ Delete trip
- ⚠️ Change trip visibility (only from private to unlisted)

#### Viewer
- ✅ View trip
- ❌ Edit anything
- ❌ Create/delete anything
- ❌ Manage collaborators

### Collaboration Rules

1. **Trip Creator**: Automatically becomes first owner
2. **Multiple Owners**: A trip can have multiple owners
3. **One Owner Minimum**: At least one owner must exist at all times
4. **Last Owner Protection**: Cannot remove last owner
5. **Self-Demotion**: Owners can demote themselves if other owners exist
6. **Invitation Flow**:
   - Only owners can invite collaborators
   - Invitations can be pending, accepted, or declined
   - Pending invitations can be cancelled

### User Deletion Impact

When a user is deleted:
1. **Created Trips**:
   - If public/unlisted: `created_by = NULL`, trip persists
   - If private: Check remaining owners
     - If other owners exist: Trip persists
     - If no other owners: Trip is deleted (CASCADE)

2. **Collaborator Records**: All records CASCADE deleted

3. **Owner Promotion**:
   - If deleted user was sole owner of public trip
   - First editor is automatically promoted to owner
   - If no editors, first viewer promoted to owner

## API Endpoints

### Collaborator Management
- `POST /trips/{trip_id}/collaborators` - Invite user to trip
- `GET /trips/{trip_id}/collaborators` - List trip collaborators
- `GET /users/me/collaborations` - List my collaborative trips
- `PUT /trips/{trip_id}/collaborators/{user_id}` - Update collaborator role
- `DELETE /trips/{trip_id}/collaborators/{user_id}` - Remove collaborator

### Invitation Management
- `GET /users/me/invitations` - List pending invitations
- `POST /invitations/{invitation_id}/accept` - Accept invitation
- `POST /invitations/{invitation_id}/decline` - Decline invitation

## Pydantic Schemas

### TripCollaboratorBase
```python
class TripCollaboratorBase(BaseModel):
    trip_id: int
    user_id: int
    role: str = "viewer"
```

### TripCollaboratorInvite
```python
class TripCollaboratorInvite(BaseModel):
    user_email: str  # Or user_id
    role: str = "viewer"
    message: Optional[str] = None  # Optional invitation message
```

### TripCollaboratorUpdate
```python
class TripCollaboratorUpdate(BaseModel):
    role: str  # Only field that can be updated
```

### TripCollaboratorResponse
```python
class TripCollaboratorResponse(TripCollaboratorBase):
    id: int
    invited_by: Optional[int]
    invited_at: datetime
    accepted_at: Optional[datetime]
    invitation_status: str
    created_at: datetime

    # Include user details
    user: UserBasicResponse

    class Config:
        from_attributes = True
```

### UserBasicResponse
```python
class UserBasicResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    profile_photo_url: Optional[str]
```

## Permission Check Helpers

```python
def check_trip_permission(trip_id: int, user_id: int, required_role: str) -> bool:
    """
    Check if user has required permission for trip.

    Hierarchy: owner > editor > viewer
    """
    collaborator = get_collaborator(trip_id, user_id)
    if not collaborator:
        return False

    role_hierarchy = {
        'viewer': 0,
        'editor': 1,
        'owner': 2
    }

    user_level = role_hierarchy[collaborator.role]
    required_level = role_hierarchy[required_role]

    return user_level >= required_level

def is_trip_owner(trip_id: int, user_id: int) -> bool:
    """Check if user is owner of trip."""
    return check_trip_permission(trip_id, user_id, 'owner')

def can_edit_trip(trip_id: int, user_id: int) -> bool:
    """Check if user can edit trip."""
    return check_trip_permission(trip_id, user_id, 'editor')

def can_view_trip(trip_id: int, user_id: int) -> bool:
    """Check if user can view trip."""
    # Public trips are viewable by anyone
    trip = get_trip(trip_id)
    if trip.visibility == 'public':
        return True

    # Otherwise check collaboration
    return check_trip_permission(trip_id, user_id, 'viewer')
```

## Use Cases

### Use Case 1: Family Trip
```
- User A creates trip (becomes owner)
- User A invites User B (partner) as owner
- User A invites User C (child) as editor
- User A invites User D (grandparent) as viewer
```

### Use Case 2: Group Tour
```
- User A creates trip (tour organizer - owner)
- User A invites User B, C, D as editors (can add activities)
- User A invites User E, F as viewers (just following itinerary)
```

### Use Case 3: Public Trip Collaboration
```
- User A creates public trip
- User B clones trip (becomes owner of clone)
- User B invites friends to collaborate on their version
```

## Security Considerations

1. **Email Validation**: Verify email exists before sending invitation
2. **Spam Protection**: Limit invitations per user per day
3. **Privacy**: Don't expose collaborator emails in public trip views
4. **Authorization**: Always verify role before allowing actions
5. **Last Owner Protection**: Prevent removing/demoting last owner

## Validation Rules

### Role Validation
```python
@validator('role')
def valid_role(cls, v):
    if v not in ['owner', 'editor', 'viewer']:
        raise ValueError('Invalid role')
    return v
```

### Self-Invitation Prevention
```python
def validate_invitation(user_id: int, invitee_email: str):
    invitee = get_user_by_email(invitee_email)
    if invitee.id == user_id:
        raise ValueError('Cannot invite yourself')
```

### Last Owner Protection
```python
def validate_role_change(trip_id: int, user_id: int, new_role: str):
    if new_role != 'owner':
        owners = count_trip_owners(trip_id)
        if owners == 1 and is_trip_owner(trip_id, user_id):
            raise ValueError('Cannot demote last owner')
```

## Notification Integration (Future)

When collaboration events occur:
- User invited → Send email notification
- Invitation accepted → Notify inviter
- Role changed → Notify user
- Removed from trip → Notify user

## Migration Notes

### Phase 1
- Not included (solo trip management only)

### Phase 2
- Full implementation of collaborative features
- Invitation system
- Role-based permissions

### Future Enhancements
- Real-time collaboration (WebSocket)
- Activity log (who changed what)
- @mentions in notes
- Collaborative editing with conflict resolution
