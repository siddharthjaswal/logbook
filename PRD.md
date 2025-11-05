# Product Requirements Document (PRD)
## Logbook - Travel Planning & Tracking Backend API

**Version:** 1.0
**Last Updated:** 2025-11-05
**Status:** In Development

---

## 1. Executive Summary

Logbook is a comprehensive travel management backend API that enables users to plan, track, and document their trips. The system provides structured itinerary management, expense tracking, memory preservation through photos and notes, and travel logistics coordination.

### Vision
To create the most intuitive and comprehensive travel tracking system that helps travelers organize every aspect of their journey, from initial planning through post-trip memories.

---

## 2. Target Users

### Primary Users
- **Solo Travelers**: Individuals planning personal trips who need organized itineraries and expense tracking
- **Travel Enthusiasts**: People who take frequent trips and want to maintain a travel log/journal
- **Digital Nomads**: Remote workers traveling while working who need detailed trip organization
- **Family Coordinators**: People organizing family vacations with multiple travelers

### Secondary Users
- **Travel Bloggers**: Content creators documenting their journeys
- **Business Travelers**: Professionals tracking work-related travel expenses
- **Group Trip Organizers**: People coordinating trips for friends or organizations

---

## 3. Goals & Objectives

### Primary Goals
1. **Trip Organization**: Provide comprehensive trip planning and day-by-day itinerary management
2. **Expense Management**: Enable detailed expense tracking with categorization and budget monitoring
3. **Memory Preservation**: Allow users to document experiences through photos, notes, and ratings
4. **Travel Logistics**: Simplify transit tracking, accommodation management, and packing coordination

### Success Metrics
- API response time < 200ms for 95th percentile
- 99.9% uptime
- Support for 1000+ concurrent users
- Data consistency and integrity across all operations
- Scalable architecture supporting future mobile/web clients

---

## 4. Current Implementation Status

### Completed Features (v0.1)
- [x] Trip creation and retrieval
- [x] Trip day structure with transit modes
- [x] Basic CRUD operations for trips
- [x] SQLite database with SQLAlchemy ORM
- [x] FastAPI framework setup
- [x] Interactive API documentation

### Known Issues
- [ ] Trip days router not registered in main.py
- [ ] Missing UPDATE and DELETE operations
- [ ] No authentication/authorization
- [ ] Incomplete requirements.txt (missing SQLAlchemy, Uvicorn)
- [ ] No database migrations system
- [ ] No input validation for foreign keys
- [ ] No error handling beyond basic 404s

---

## 5. Core Features & Requirements

### 5.1 Trip Management

#### Trip Entity
**Fields:**
- `id`: Unique identifier (BigInteger, auto-increment)
- `user_id`: Foreign key to User (to be implemented)
- `name`: Trip name/title (String, required)
- `description`: Detailed trip description (Text, optional)
- `start_date_timestamp`: Trip start date (BigInteger, required)
- `end_date_timestamp`: Trip end date (BigInteger, required)
- `destination_country`: Primary country (String, optional)
- `destination_city`: Primary city (String, optional)
- `status`: Trip status (Enum: planning, ongoing, completed, cancelled)
- `budget_total`: Total budget (Decimal, optional)
- `currency`: Budget currency (String, default: USD)
- `cover_photo_url`: Trip cover image (String, optional)
- `is_private`: Privacy setting (Boolean, default: False)
- `created_at`: Timestamp (auto)
- `updated_at`: Timestamp (auto)

**Operations:**
- `POST /trips/`: Create new trip
- `GET /trips/`: List all trips (with filters: status, date range, destination)
- `GET /trips/{trip_id}`: Get specific trip with related data
- `PUT /trips/{trip_id}`: Update trip details
- `DELETE /trips/{trip_id}`: Delete trip (soft delete)
- `GET /trips/{trip_id}/summary`: Get trip summary with stats

**Business Rules:**
- End date must be after start date
- Trip name required, max 200 characters
- User can only access their own trips
- Deleting a trip should cascade or block based on related data

---

### 5.2 Trip Day / Itinerary Management

#### TripDay Entity (Enhanced)
**Current Fields:**
- `id`, `trip_id`, `date`, `place`, `timezone`
- `arrival_time`, `departure_time`, `transit_mode`, `transit_details`, `notes`

**Additional Fields:**
- `day_number`: Sequential day number in trip (Integer, auto-calculated)
- `title`: Day title/summary (String, optional)
- `accommodation_name`: Hotel/stay name (String, optional)
- `accommodation_address`: Full address (String, optional)
- `accommodation_checkin`: Check-in time (BigInteger, optional)
- `accommodation_checkout`: Check-out time (BigInteger, optional)
- `weather_expected`: Expected weather (String, optional)
- `activities`: JSON array of planned activities (JSON, optional)
- `booking_references`: JSON object for booking confirmations (JSON, optional)

**Operations:**
- `POST /trip_days/`: Create trip day
- `GET /trip_days/`: List all trip days (filter by trip_id)
- `GET /trips/{trip_id}/days`: Get all days for a trip (ordered)
- `GET /trip_days/{trip_day_id}`: Get specific day
- `PUT /trip_days/{trip_day_id}`: Update day details
- `DELETE /trip_days/{trip_day_id}`: Delete day
- `POST /trip_days/{trip_day_id}/reorder`: Reorder days

**Business Rules:**
- Day date must fall between trip start and end dates
- Day number auto-calculated based on date sequence
- Cannot have multiple days with same date for same trip
- Transit details required if transit_mode specified

---

### 5.3 Expense Tracking

#### Expense Entity (New)
**Fields:**
- `id`: Unique identifier
- `trip_id`: Foreign key to Trip
- `trip_day_id`: Foreign key to TripDay (optional)
- `category`: Expense category (Enum: accommodation, food, transport, activities, shopping, other)
- `subcategory`: Detailed category (String, optional)
- `amount`: Expense amount (Decimal, required)
- `currency`: Currency code (String, default: USD)
- `amount_in_base_currency`: Converted amount (Decimal, auto-calculated)
- `description`: Expense description (String, required)
- `merchant`: Merchant/vendor name (String, optional)
- `payment_method`: Payment method (Enum: cash, credit_card, debit_card, digital_wallet)
- `expense_date`: Date of expense (BigInteger, required)
- `receipt_url`: Receipt image URL (String, optional)
- `notes`: Additional notes (Text, optional)
- `is_reimbursable`: Reimbursement flag (Boolean, default: False)
- `created_at`: Timestamp (auto)

**Operations:**
- `POST /expenses/`: Create expense
- `GET /expenses/`: List expenses (filter by trip, category, date range)
- `GET /trips/{trip_id}/expenses`: Get all trip expenses
- `GET /expenses/{expense_id}`: Get specific expense
- `PUT /expenses/{expense_id}`: Update expense
- `DELETE /expenses/{expense_id}`: Delete expense
- `GET /trips/{trip_id}/expenses/summary`: Get expense summary and analytics

**Business Rules:**
- Amount must be positive
- Expense date should be within trip date range (warning if outside)
- Currency conversion rates fetched from external API
- Support for split expenses in future phase

---

### 5.4 Photo & Memory Management

#### Photo Entity (New)
**Fields:**
- `id`: Unique identifier
- `trip_id`: Foreign key to Trip
- `trip_day_id`: Foreign key to TripDay (optional)
- `file_url`: Photo storage URL (String, required)
- `thumbnail_url`: Thumbnail URL (String, auto-generated)
- `title`: Photo title (String, optional)
- `description`: Photo description (Text, optional)
- `taken_at`: Photo timestamp (BigInteger, optional)
- `location_lat`: Latitude (Float, optional)
- `location_lng`: Longitude (Float, optional)
- `location_name`: Location name (String, optional)
- `is_cover_photo`: Cover photo flag (Boolean, default: False)
- `order`: Display order (Integer)
- `file_size`: File size in bytes (BigInteger)
- `mime_type`: File MIME type (String)
- `created_at`: Timestamp (auto)

**Operations:**
- `POST /photos/`: Upload photo
- `GET /photos/`: List photos (filter by trip, day)
- `GET /trips/{trip_id}/photos`: Get all trip photos
- `GET /photos/{photo_id}`: Get specific photo
- `PUT /photos/{photo_id}`: Update photo metadata
- `DELETE /photos/{photo_id}`: Delete photo
- `POST /photos/batch`: Batch upload photos
- `PUT /trips/{trip_id}/photos/reorder`: Reorder photos

**Business Rules:**
- Supported formats: JPEG, PNG, HEIC
- Max file size: 10MB per photo
- Automatic thumbnail generation (200x200px)
- Photo storage in S3/CloudStorage
- EXIF data extraction for timestamp and location

---

### 5.5 Notes & Journal

#### Note Entity (New)
**Fields:**
- `id`: Unique identifier
- `trip_id`: Foreign key to Trip
- `trip_day_id`: Foreign key to TripDay (optional)
- `title`: Note title (String, optional)
- `content`: Note content (Text, required)
- `note_type`: Type (Enum: general, highlight, tip, warning, memory)
- `is_pinned`: Pin to top (Boolean, default: False)
- `rating`: Day/experience rating (Integer, 1-5, optional)
- `mood`: Mood emoji/text (String, optional)
- `created_at`: Timestamp (auto)
- `updated_at`: Timestamp (auto)

**Operations:**
- `POST /notes/`: Create note
- `GET /notes/`: List notes (filter by trip, day, type)
- `GET /trips/{trip_id}/notes`: Get all trip notes
- `GET /notes/{note_id}`: Get specific note
- `PUT /notes/{note_id}`: Update note
- `DELETE /notes/{note_id}`: Delete note

---

### 5.6 Packing Lists

#### PackingList Entity (New)
**Fields:**
- `id`: Unique identifier
- `trip_id`: Foreign key to Trip
- `name`: List name (String, default: "Main Packing List")

#### PackingItem Entity (New)
**Fields:**
- `id`: Unique identifier
- `packing_list_id`: Foreign key to PackingList
- `item_name`: Item name (String, required)
- `category`: Category (Enum: clothing, electronics, documents, toiletries, other)
- `quantity`: Quantity (Integer, default: 1)
- `is_packed`: Packed status (Boolean, default: False)
- `notes`: Additional notes (String, optional)
- `priority`: Priority level (Enum: low, medium, high)

**Operations:**
- `POST /trips/{trip_id}/packing_lists`: Create packing list
- `GET /trips/{trip_id}/packing_lists`: Get trip packing lists
- `POST /packing_lists/{list_id}/items`: Add packing item
- `PUT /packing_items/{item_id}`: Update item (including pack status)
- `DELETE /packing_items/{item_id}`: Remove item
- `GET /packing_lists/{list_id}/summary`: Get packing progress

---

### 5.7 User Management & Authentication

#### User Entity (New)
**Fields:**
- `id`: Unique identifier
- `email`: Email address (String, unique, required)
- `username`: Username (String, unique, optional)
- `password_hash`: Hashed password (String, required)
- `first_name`: First name (String, optional)
- `last_name`: Last name (String, optional)
- `profile_photo_url`: Profile photo (String, optional)
- `default_currency`: Preferred currency (String, default: USD)
- `date_format`: Date format preference (String)
- `timezone`: User timezone (String)
- `is_active`: Account active status (Boolean, default: True)
- `is_verified`: Email verification status (Boolean, default: False)
- `created_at`: Timestamp (auto)
- `last_login_at`: Timestamp

**Operations:**
- `POST /auth/register`: Register new user
- `POST /auth/login`: Login user (return JWT token)
- `POST /auth/logout`: Logout user
- `POST /auth/refresh`: Refresh access token
- `POST /auth/forgot-password`: Initiate password reset
- `POST /auth/reset-password`: Reset password with token
- `GET /users/me`: Get current user profile
- `PUT /users/me`: Update user profile
- `POST /auth/verify-email`: Verify email address

**Security Requirements:**
- JWT-based authentication
- Password hashing with bcrypt
- Refresh token rotation
- Rate limiting on auth endpoints
- Email verification for new accounts
- Password strength requirements

---

## 6. Technical Architecture

### 6.1 Technology Stack

**Backend Framework:**
- FastAPI (Python 3.8+)
- Pydantic for data validation
- SQLAlchemy 2.0 ORM

**Database:**
- **Development**: SQLite
- **Production**: PostgreSQL (recommended)
- Alembic for migrations

**Authentication:**
- python-jose for JWT
- passlib for password hashing
- python-multipart for file uploads

**Storage:**
- AWS S3 / CloudFlare R2 for photos and receipts
- Local storage for development

**Additional Services:**
- Redis for caching and rate limiting
- Celery for background tasks (photo processing, email)
- Email service (SendGrid/AWS SES)

### 6.2 API Design Principles

**REST Conventions:**
- Resource-based URLs
- HTTP methods: GET, POST, PUT, DELETE
- Proper status codes (200, 201, 400, 401, 404, 500)
- Consistent error response format

**Response Format:**
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": 1730819200
}
```

**Error Format:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {}
  },
  "timestamp": 1730819200
}
```

**Pagination:**
- Query params: `skip`, `limit`
- Response includes: `total`, `page`, `page_size`, `items`

**Filtering:**
- Query params for filters: `?status=ongoing&destination=Paris`
- Date ranges: `?start_date=...&end_date=...`

---

## 7. Data Models Summary

### Relationships Overview

```
User (1) ──────< (N) Trip
Trip (1) ──────< (N) TripDay
Trip (1) ──────< (N) Expense
Trip (1) ──────< (N) Photo
Trip (1) ──────< (N) Note
Trip (1) ──────< (N) PackingList

TripDay (1) ──────< (N) Expense
TripDay (1) ──────< (N) Photo
TripDay (1) ──────< (N) Note

PackingList (1) ──────< (N) PackingItem
```

### Database Indexes

**Critical Indexes:**
- `trips.user_id`
- `trip_days.trip_id, trip_days.date`
- `expenses.trip_id, expenses.expense_date`
- `photos.trip_id, photos.trip_day_id`
- `notes.trip_id, notes.trip_day_id`
- `packing_items.packing_list_id`

---

## 8. Non-Functional Requirements

### 8.1 Performance
- API response time: < 200ms (95th percentile)
- Support 1000+ concurrent users
- Photo upload: < 5 seconds for 10MB file
- Database query optimization for large datasets

### 8.2 Security
- HTTPS only in production
- JWT token expiry: 1 hour (access), 7 days (refresh)
- Rate limiting: 100 requests/minute per user
- SQL injection prevention (parameterized queries)
- XSS protection
- CORS configuration
- File upload validation and sanitization

### 8.3 Scalability
- Horizontal scaling capability
- Database connection pooling
- Caching strategy for frequently accessed data
- CDN for photo delivery
- Background job processing for heavy operations

### 8.4 Reliability
- 99.9% uptime SLA
- Automated backups (daily database backups)
- Error logging and monitoring (Sentry/CloudWatch)
- Health check endpoints
- Graceful degradation

### 8.5 Maintainability
- Comprehensive API documentation
- Code coverage > 80%
- Type hints throughout codebase
- Linting and formatting (Black, Ruff)
- Git workflow with PR reviews

---

## 9. Development Roadmap

### Phase 1: Foundation (Current - Week 4)
**Goal:** Complete core trip and itinerary management

**Tasks:**
- [ ] Fix trip_days router registration
- [ ] Implement UPDATE and DELETE for trips and trip_days
- [ ] Add proper error handling and validation
- [ ] Complete requirements.txt with all dependencies
- [ ] Set up Alembic for database migrations
- [ ] Add comprehensive unit tests
- [ ] Implement foreign key validation
- [ ] Add filtering and pagination
- [ ] Update Bruno API collection with all endpoints

**Deliverables:**
- Fully functional trip and trip day CRUD
- Database migration system
- Test coverage > 50%

---

### Phase 2: User Authentication (Week 5-6)
**Goal:** Implement secure user authentication

**Tasks:**
- [ ] Create User model and schema
- [ ] Implement JWT authentication
- [ ] Add registration and login endpoints
- [ ] Email verification system
- [ ] Password reset functionality
- [ ] Protect all existing endpoints with auth
- [ ] Add user context to all operations
- [ ] Implement rate limiting

**Deliverables:**
- Complete authentication system
- Protected API endpoints
- User management capabilities

---

### Phase 3: Expense Tracking (Week 7-8)
**Goal:** Enable comprehensive expense management

**Tasks:**
- [ ] Create Expense model and relationships
- [ ] Implement expense CRUD operations
- [ ] Add expense categorization
- [ ] Currency conversion integration
- [ ] Expense summary and analytics endpoints
- [ ] Receipt upload functionality
- [ ] Budget tracking and alerts

**Deliverables:**
- Full expense tracking system
- Budget monitoring
- Expense analytics and reports

---

### Phase 4: Photos & Memories (Week 9-10)
**Goal:** Photo management and trip memories

**Tasks:**
- [ ] Create Photo model
- [ ] Implement file upload to cloud storage
- [ ] EXIF data extraction
- [ ] Thumbnail generation
- [ ] Photo CRUD operations
- [ ] Batch upload support
- [ ] Create Note model for journaling
- [ ] Implement note CRUD operations

**Deliverables:**
- Photo upload and management
- Trip journaling system
- Memory preservation features

---

### Phase 5: Packing Lists & Additional Features (Week 11-12)
**Goal:** Complete trip planning features

**Tasks:**
- [ ] Create PackingList and PackingItem models
- [ ] Implement packing list CRUD
- [ ] Packing progress tracking
- [ ] Template packing lists
- [ ] Export functionality (PDF, Excel)
- [ ] Trip sharing capabilities
- [ ] Trip cloning/templates

**Deliverables:**
- Packing list management
- Trip templates
- Export features

---

### Phase 6: Polish & Production Ready (Week 13-14)
**Goal:** Production deployment

**Tasks:**
- [ ] Performance optimization
- [ ] Security audit
- [ ] Complete API documentation
- [ ] Migration to PostgreSQL
- [ ] Set up Redis caching
- [ ] Implement background jobs (Celery)
- [ ] Monitoring and logging setup
- [ ] Load testing
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Production deployment

**Deliverables:**
- Production-ready API
- Complete documentation
- Deployed and monitored system

---

## 10. API Endpoint Summary

### Authentication
```
POST   /auth/register
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
POST   /auth/verify-email
POST   /auth/forgot-password
POST   /auth/reset-password
```

### Users
```
GET    /users/me
PUT    /users/me
DELETE /users/me
```

### Trips
```
POST   /trips/
GET    /trips/
GET    /trips/{trip_id}
PUT    /trips/{trip_id}
DELETE /trips/{trip_id}
GET    /trips/{trip_id}/summary
```

### Trip Days
```
POST   /trip_days/
GET    /trip_days/
GET    /trips/{trip_id}/days
GET    /trip_days/{trip_day_id}
PUT    /trip_days/{trip_day_id}
DELETE /trip_days/{trip_day_id}
POST   /trip_days/{trip_day_id}/reorder
```

### Expenses
```
POST   /expenses/
GET    /expenses/
GET    /trips/{trip_id}/expenses
GET    /expenses/{expense_id}
PUT    /expenses/{expense_id}
DELETE /expenses/{expense_id}
GET    /trips/{trip_id}/expenses/summary
```

### Photos
```
POST   /photos/
POST   /photos/batch
GET    /photos/
GET    /trips/{trip_id}/photos
GET    /photos/{photo_id}
PUT    /photos/{photo_id}
DELETE /photos/{photo_id}
PUT    /trips/{trip_id}/photos/reorder
```

### Notes
```
POST   /notes/
GET    /notes/
GET    /trips/{trip_id}/notes
GET    /notes/{note_id}
PUT    /notes/{note_id}
DELETE /notes/{note_id}
```

### Packing Lists
```
POST   /trips/{trip_id}/packing_lists
GET    /trips/{trip_id}/packing_lists
GET    /packing_lists/{list_id}
PUT    /packing_lists/{list_id}
DELETE /packing_lists/{list_id}
POST   /packing_lists/{list_id}/items
GET    /packing_lists/{list_id}/items
PUT    /packing_items/{item_id}
DELETE /packing_items/{item_id}
GET    /packing_lists/{list_id}/summary
```

---

## 11. Future Considerations

### Post-MVP Features
- **Social Features**: Share trips publicly, follow other travelers
- **Collaboration**: Multi-user trip planning and editing
- **Weather Integration**: Real-time weather data for destinations
- **Flight/Hotel APIs**: Integration with booking platforms
- **Maps Integration**: Interactive maps showing trip routes
- **Travel Recommendations**: AI-powered suggestions based on preferences
- **Travel Documents**: Passport/visa tracking and reminders
- **Emergency Contacts**: Emergency information management
- **Offline Mode**: Mobile app with offline capability
- **Travel Statistics**: Personal travel analytics (countries visited, etc.)
- **Budget Optimization**: Smart budget recommendations
- **Calendar Integration**: Sync with Google/Apple Calendar

### Technical Improvements
- GraphQL API alternative
- WebSocket support for real-time collaboration
- Mobile push notifications
- Advanced search with Elasticsearch
- Machine learning for expense categorization
- Multi-language support (i18n)
- Data export in multiple formats
- API versioning strategy

---

## 12. Success Criteria

### Technical Success
- [ ] All CRUD operations implemented for all entities
- [ ] 95%+ API uptime
- [ ] < 200ms average response time
- [ ] 80%+ test coverage
- [ ] Zero critical security vulnerabilities
- [ ] Successful load test with 1000+ concurrent users

### Product Success
- [ ] Complete trip planning workflow from creation to completion
- [ ] Comprehensive expense tracking with analytics
- [ ] Photo and memory management system
- [ ] User authentication and authorization
- [ ] Packing list functionality
- [ ] Mobile-ready API design

---

## 13. Risks & Mitigations

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Database performance with large datasets | High | Implement indexing, caching, pagination |
| File storage costs | Medium | Image compression, storage tiers, cleanup policies |
| Third-party API dependencies | Medium | Fallback mechanisms, caching, rate limiting |
| Security vulnerabilities | High | Regular audits, dependency updates, security best practices |

### Project Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Phased development, strict MVP definition |
| Timeline delays | Medium | Buffer time in schedule, prioritize features |
| Technical debt | Medium | Code reviews, refactoring sprints, documentation |

---

## 14. Appendix

### A. Glossary
- **Trip**: A planned or completed travel journey
- **Trip Day**: A single day within a trip's itinerary
- **Transit Mode**: Method of transportation between locations
- **Expense Category**: Classification of spending (accommodation, food, etc.)
- **Packing List**: Checklist of items to bring on a trip

### B. References
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- REST API Best Practices: https://restfulapi.net/

### C. Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-05 | 1.0 | Initial PRD creation | - |

---

## Contact & Feedback

For questions or suggestions about this PRD, please contact the development team or create an issue in the project repository.
