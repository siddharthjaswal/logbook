# Phase 2: Trip Collaboration & Sharing - Implementation Plan

## Overview
Enable multiple users to collaborate on trip planning with role-based permissions, invitations, and activity tracking.

## Core Features

### 1. Trip Members & Permissions

**Roles:**
- `owner` - Full control (creator of the trip)
- `editor` - Can view and modify trip details
- `viewer` - Read-only access

**Permissions Matrix:**
| Action | Owner | Editor | Viewer |
|--------|-------|--------|--------|
| View trip | ✅ | ✅ | ✅ |
| Edit trip details | ✅ | ✅ | ❌ |
| Delete trip | ✅ | ❌ | ❌ |
| Invite members | ✅ | ✅ | ❌ |
| Remove members | ✅ | ❌ | ❌ |
| Change member roles | ✅ | ❌ | ❌ |
| Add/edit trip days | ✅ | ✅ | ❌ |
| Add/edit accommodations | ✅ | ✅ | ❌ |
| Add/edit expenses | ✅ | ✅ | ❌ |
| Add comments | ✅ | ✅ | ✅ |

### 2. Trip Invitations

**Invitation Flow:**
1. Owner/Editor sends invitation via email
2. Invitee receives email with accept/decline link
3. Upon acceptance, user becomes trip member
4. Invitations expire after 7 days

**Invitation States:**
- `pending` - Sent but not yet responded
- `accepted` - User joined the trip
- `declined` - User declined invitation
- `expired` - Invitation expired (7 days)
- `cancelled` - Sender cancelled invitation

### 3. Activity Feed

**Activity Types:**
- Trip created/updated/deleted
- Member added/removed
- Trip day added/updated
- Accommodation booked/modified
- Expense added
- Comment posted
- Checklist item completed

**Feed Features:**
- Chronological activity log
- Filter by activity type
- Pagination
- Real-time updates (future: WebSocket)

### 4. Comments

**Comment System:**
- Comments on trips
- Comments on specific trip days
- Comments on accommodations/transits/activities
- Nested replies (optional for v1)
- Edit/delete own comments
- Mentions (@username)

## Data Models

### TripMember
```python
class TripMember(Base):
    id: int (PK)
    trip_id: int (FK -> trips.id)
    user_id: int (FK -> users.id)
    role: Enum(owner, editor, viewer)
    joined_at: datetime
    invited_by: int (FK -> users.id, nullable)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trip: Trip
    user: User
    inviter: User
    
    # Constraints
    unique(trip_id, user_id)
```

### TripInvitation
```python
class TripInvitation(Base):
    id: int (PK)
    trip_id: int (FK -> trips.id)
    inviter_id: int (FK -> users.id)
    invitee_email: str
    invitee_id: int (FK -> users.id, nullable)
    role: Enum(editor, viewer)
    status: Enum(pending, accepted, declined, expired, cancelled)
    token: str (unique, for accept/decline links)
    message: text (optional)
    expires_at: datetime
    responded_at: datetime (nullable)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trip: Trip
    inviter: User
    invitee: User (nullable if not registered)
```

### ActivityLog
```python
class ActivityLog(Base):
    id: int (PK)
    trip_id: int (FK -> trips.id)
    user_id: int (FK -> users.id)
    activity_type: Enum(trip_updated, member_added, day_added, expense_added, etc.)
    entity_type: str (trip, trip_day, accommodation, expense, etc.)
    entity_id: int (nullable)
    description: text (auto-generated)
    metadata: jsonb (additional context)
    created_at: datetime
    
    # Relationships
    trip: Trip
    user: User
```

### Comment
```python
class Comment(Base):
    id: int (PK)
    trip_id: int (FK -> trips.id)
    user_id: int (FK -> users.id)
    entity_type: str (trip, trip_day, accommodation, transit, activity, expense)
    entity_id: int (nullable, null means general trip comment)
    parent_id: int (FK -> comments.id, nullable for nested replies)
    content: text
    mentions: list[int] (user_ids mentioned)
    is_edited: bool
    edited_at: datetime (nullable)
    deleted_at: datetime (nullable, soft delete)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trip: Trip
    user: User
    parent: Comment
    replies: list[Comment]
```

## API Endpoints

### Trip Members
- `GET /api/v1/trips/{trip_id}/members` - List trip members
- `POST /api/v1/trips/{trip_id}/members` - Add member directly (owner only)
- `PUT /api/v1/trips/{trip_id}/members/{user_id}` - Update member role (owner only)
- `DELETE /api/v1/trips/{trip_id}/members/{user_id}` - Remove member (owner only)
- `POST /api/v1/trips/{trip_id}/leave` - Leave trip (non-owners)

### Invitations
- `POST /api/v1/trips/{trip_id}/invitations` - Send invitation
- `GET /api/v1/trips/{trip_id}/invitations` - List trip invitations
- `DELETE /api/v1/trips/{trip_id}/invitations/{invitation_id}` - Cancel invitation
- `POST /api/v1/invitations/{token}/accept` - Accept invitation (public)
- `POST /api/v1/invitations/{token}/decline` - Decline invitation (public)
- `GET /api/v1/users/me/invitations` - My pending invitations

### Activity Feed
- `GET /api/v1/trips/{trip_id}/activity` - Get activity feed
  - Query params: `activity_type`, `skip`, `limit`

### Comments
- `POST /api/v1/trips/{trip_id}/comments` - Add comment
- `GET /api/v1/trips/{trip_id}/comments` - List comments
  - Query params: `entity_type`, `entity_id`, `skip`, `limit`
- `PUT /api/v1/comments/{comment_id}` - Edit comment
- `DELETE /api/v1/comments/{comment_id}` - Delete comment (soft)

## Implementation Phases

### Phase 2.1: Trip Members (Priority 1)
1. Create TripMember model and migration
2. Automatically create owner member on trip creation
3. Implement member CRUD operations
4. Add permission decorator for route protection
5. Update existing endpoints with permission checks

### Phase 2.2: Invitations (Priority 2)
1. Create TripInvitation model and migration
2. Implement invitation sending (with email template)
3. Create public accept/decline endpoints
4. Add invitation expiry logic
5. Implement "My Invitations" endpoint

### Phase 2.3: Activity Feed (Priority 3)
1. Create ActivityLog model and migration
2. Add activity logging to key operations
3. Implement activity feed endpoint
4. Add filtering and pagination

### Phase 2.4: Comments (Priority 4)
1. Create Comment model and migration
2. Implement comment CRUD operations
3. Add mention detection (@username)
4. Implement nested replies (optional)

## Security Considerations

1. **Authorization**: Every endpoint must check user permissions
2. **Invitation Tokens**: Use cryptographically secure tokens
3. **Email Validation**: Validate email format for invitations
4. **Rate Limiting**: Limit invitation sending to prevent spam
5. **Data Access**: Users can only see trips they're members of
6. **Soft Deletes**: Comments should be soft-deleted

## Migration Strategy

1. Backfill existing trips with owner members
2. Update trip visibility logic to account for members
3. Gradually roll out permission checks
4. Maintain backward compatibility

## Testing Strategy

1. Unit tests for permission checks
2. Integration tests for member CRUD
3. End-to-end tests for invitation flow
4. Permission matrix verification tests
5. Activity logging tests

## Future Enhancements

- Real-time collaboration (WebSocket)
- Conflict resolution for concurrent edits
- Trip templates from shared trips
- Group invitations
- Email notifications for activity
- Push notifications (mobile)
