# Logbook Backend - Implementation Plan

## Overview

This implementation plan breaks down the Logbook backend development into **6 phases**, prioritized for incremental deployment and testing. Each phase builds on the previous one and can be deployed, tested via Bruno/Postman, and validated before moving forward.

**Priority Strategy:**
- ✅ Start with core trip planning functionality
- ✅ Authentication early (Google OAuth)
- ✅ Deploy and test incrementally
- ⏸️ Photo/receipt storage - LOWEST PRIORITY (Phase 6)

---

## Testing Strategy

We'll use **two complementary testing approaches**:

### 1. Bruno Collection (Manual Testing)
- **What:** Plain-text API request files (`.bru`) stored in `collection/` folder
- **When:** Create Bruno files **immediately after** implementing each endpoint
- **Purpose:** Manual testing during development, debugging, API exploration
- **Tool Required:** Yes, install [Bruno desktop app](https://www.usebruno.com/) (free, open source)
- **Git:** ✅ All `.bru` files are committed to Git

### 2. Pytest (Automated Testing)
- **What:** Python test files (`test_*.py`) in `tests/` folder
- **When:** Write tests **alongside** each feature implementation
- **Purpose:** Automated regression testing, CI/CD pipeline
- **Tool Required:** `pytest` package (installed via pip)
- **Git:** ✅ All test files are committed to Git

### Workflow for Each Endpoint:
```
1. Implement API endpoint (e.g., POST /trips/)
2. Create Bruno request file (e.g., collection/trips/create-trip.bru)
3. Test manually in Bruno app (click Send, verify response)
4. Write pytest test (e.g., tests/test_trips.py::test_create_trip)
5. Run pytest to verify (pytest tests/test_trips.py)
6. Commit code + Bruno file + test file together
```

---

## Phase 1: Foundation & Core Trip Management
**Goal:** Get basic trip CRUD working with authentication
**Deploy & Test:** After this phase, you can create/manage trips

### Tasks

#### 1.1 Project Setup & Database
- [ ] Set up PostgreSQL database (replace SQLite)
- [ ] Update database.py for PostgreSQL connection
- [ ] Create environment variables (.env file) for database config
- [ ] Test database connection
- [ ] **Bruno:** Create collection folder structure
  - [ ] Create `collection/` folder
  - [ ] Create `collection/bruno.json` (collection config)
  - [ ] Create `collection/environments/local.bru` (localhost:8000)
  - [ ] Create `collection/environments/production.bru` (production URL)
- [ ] **Pytest:** Set up test infrastructure
  - [ ] Create `tests/` folder
  - [ ] Create `tests/conftest.py` (pytest fixtures)
  - [ ] Create `tests/test_database.py` (test DB connection)
  - [ ] Install pytest, pytest-asyncio
  - [ ] Add pytest configuration to pyproject.toml or pytest.ini

#### 1.2 Update Models (SQLAlchemy)
- [ ] Update User model (add google_id, remove password fields)
- [ ] Update Trip model (add all new fields: timezones, flexible dates, destinations, visibility)
- [ ] Update TripDay model (add trip_day_type, timezone, location fields)
- [ ] Create database migration (Alembic setup)
- [ ] Run migration and verify tables
- [ ] **Pytest:** Write model tests
  - [ ] Create `tests/test_models.py`
  - [ ] Test User model creation and validation
  - [ ] Test Trip model with all field variations
  - [ ] Test TripDay model relationships

#### 1.3 Google OAuth Authentication
- [ ] Install OAuth dependencies (google-auth, google-auth-oauthlib, PyJWT)
- [ ] Set up Google Cloud Console project
- [ ] Get Google OAuth credentials (CLIENT_ID, CLIENT_SECRET)
- [ ] Create auth router (app/api/auth.py)
- [ ] Implement `/auth/google` redirect endpoint
  - [ ] **Bruno:** Create `collection/auth/google-login.bru`
- [ ] Implement `/auth/google/callback` endpoint
  - [ ] **Bruno:** Create `collection/auth/google-callback.bru`
- [ ] Implement JWT token generation (access + refresh)
- [ ] Implement `/auth/refresh` endpoint (refresh access token)
  - [ ] **Bruno:** Create `collection/auth/refresh-token.bru`
- [ ] Create authentication middleware/dependency (get_current_user)
- [ ] **Bruno:** Test OAuth flow manually (login → get tokens)
- [ ] **Pytest:** Write auth tests
  - [ ] Create `tests/test_auth.py`
  - [ ] Test JWT token generation and validation
  - [ ] Test token refresh flow
  - [ ] Mock Google OAuth for testing

#### 1.4 Trip CRUD Operations
- [ ] Update trips.py router with new schema fields
- [ ] Implement POST /trips/ (create trip)
  - [ ] **Bruno:** Create `collection/trips/create-trip.bru` with sample data
  - [ ] Sample: Exact dates trip, Flexible dates trip, Multi-destination trip
  - [ ] **Pytest:** Add `test_create_trip()` to `tests/test_trips.py`
- [ ] Implement GET /trips/ (list user's trips with pagination)
  - [ ] **Bruno:** Create `collection/trips/list-trips.bru`
  - [ ] Test pagination (skip=0, limit=10)
  - [ ] **Pytest:** Add `test_list_trips()`, `test_list_trips_pagination()`
- [ ] Implement GET /trips/{trip_id} (get single trip)
  - [ ] **Bruno:** Create `collection/trips/get-trip.bru`
  - [ ] **Pytest:** Add `test_get_trip()`, `test_get_trip_not_found()`
- [ ] Implement PUT /trips/{trip_id} (update trip)
  - [ ] **Bruno:** Create `collection/trips/update-trip.bru`
  - [ ] Test updating different field combinations
  - [ ] **Pytest:** Add `test_update_trip()`, `test_update_trip_forbidden()`
- [ ] Implement DELETE /trips/{trip_id} (soft delete)
  - [ ] **Bruno:** Create `collection/trips/delete-trip.bru`
  - [ ] **Pytest:** Add `test_delete_trip()`, `test_delete_trip_forbidden()`
- [ ] Add authentication to all trip endpoints (require JWT token)
- [ ] **Pytest:** Add authentication tests
  - [ ] Test endpoints without token (expect 401)
  - [ ] Test endpoints with invalid token (expect 401)
  - [ ] Test endpoints with valid token (expect 200/201)

#### 1.5 Testing & Validation
- [ ] **Bruno:** Manual end-to-end testing
  - [ ] Test OAuth login flow (get access token)
  - [ ] Test creating trip with exact dates
  - [ ] Test creating trip with flexible dates ("5 days in January")
  - [ ] Test creating multi-destination trip
  - [ ] Test listing all trips
  - [ ] Test updating trip details
  - [ ] Test deleting trip
  - [ ] Test authentication (remove token, expect 401)
- [ ] **Pytest:** Run full test suite
  - [ ] Run `pytest tests/test_trips.py -v`
  - [ ] Run `pytest tests/test_auth.py -v`
  - [ ] Verify all tests pass
  - [ ] Check test coverage: `pytest --cov=app tests/`
- [ ] **Database:** Verify data integrity
  - [ ] Check trips table for correct data
  - [ ] Check soft delete works (deleted_at is set)
  - [ ] Check user associations are correct
- [ ] **Documentation:** Add README section for Bruno setup
  - [ ] How to install Bruno
  - [ ] How to import collection
  - [ ] How to set environment variables
  - [ ] How to run requests

**Deliverable:** Working trip management API with Google OAuth authentication

---

## Phase 2: Trip Collaboration & Sharing
**Goal:** Multi-user trips and public trip discovery
**Deploy & Test:** Create collaborative trips, invite users, browse public trips

### Tasks

#### 2.1 Trip Collaborators
- [ ] Create TripCollaborator model
- [ ] Create trip_collaborators CRUD operations
- [ ] Implement POST /trips/{trip_id}/collaborators (invite user)
  - [ ] **Bruno:** Create `collection/trips/collaborators/invite-collaborator.bru`
  - [ ] **Pytest:** Add `test_invite_collaborator()` to `tests/test_collaborators.py`
- [ ] Implement GET /trips/{trip_id}/collaborators (list collaborators)
  - [ ] **Bruno:** Create `collection/trips/collaborators/list-collaborators.bru`
  - [ ] **Pytest:** Add `test_list_collaborators()`
- [ ] Implement PUT /trips/{trip_id}/collaborators/{user_id} (update role)
  - [ ] **Bruno:** Create `collection/trips/collaborators/update-role.bru`
  - [ ] **Pytest:** Add `test_update_collaborator_role()`
- [ ] Implement DELETE /trips/{trip_id}/collaborators/{user_id} (remove collaborator)
  - [ ] **Bruno:** Create `collection/trips/collaborators/remove-collaborator.bru`
  - [ ] **Pytest:** Add `test_remove_collaborator()`
- [ ] Add permission checks (only owner can invite, only owner/editor can edit)
  - [ ] **Pytest:** Add `test_collaborator_permissions()`
  - [ ] Test viewer cannot edit (expect 403)
  - [ ] Test editor cannot invite (expect 403)
  - [ ] Test owner can do everything

#### 2.2 Public Trip Discovery
- [ ] Implement GET /trips/public (browse public trips)
  - [ ] **Bruno:** Create `collection/trips/public/browse-public-trips.bru`
  - [ ] Add query params: country, city, tags, sort_by, skip, limit
  - [ ] **Pytest:** Add `test_browse_public_trips()` to `tests/test_public_trips.py`
- [ ] Add filtering by country, city, dates, tags
  - [ ] **Bruno:** Add examples for each filter in bruno file
  - [ ] **Pytest:** Add `test_filter_by_country()`, `test_filter_by_city()`, etc.
- [ ] Add pagination and sorting
  - [ ] **Pytest:** Add `test_public_trips_pagination()`, `test_public_trips_sorting()`
- [ ] Implement trip engagement tracking (views, likes, clones)
  - [ ] Auto-increment views on GET /trips/{trip_id}
  - [ ] **Pytest:** Add `test_trip_view_count()`
- [ ] Implement POST /trips/{trip_id}/like
  - [ ] **Bruno:** Create `collection/trips/public/like-trip.bru`
  - [ ] **Pytest:** Add `test_like_trip()`, `test_unlike_trip()`
- [ ] Implement POST /trips/{trip_id}/clone (fork a public trip)
  - [ ] **Bruno:** Create `collection/trips/public/clone-trip.bru`
  - [ ] **Pytest:** Add `test_clone_trip()`, `test_clone_private_trip_forbidden()`
- [ ] Add indexes for search performance (countries_visited, cities_visited, tags)
- [ ] **Pytest:** Add performance tests (optional)

#### 2.3 Testing & Validation
- [ ] **Bruno:** End-to-end collaboration testing
  - [ ] Create trip as User A
  - [ ] Invite User B as editor
  - [ ] Login as User B, edit trip
  - [ ] Invite User C as viewer
  - [ ] Login as User C, try to edit (expect 403)
- [ ] **Bruno:** Public trip testing
  - [ ] Make trip public
  - [ ] Browse public trips (no auth required)
  - [ ] Clone public trip
  - [ ] Like public trip
- [ ] **Pytest:** Run full test suite
  - [ ] Run `pytest tests/test_collaborators.py -v`
  - [ ] Run `pytest tests/test_public_trips.py -v`
  - [ ] Verify all tests pass

**Deliverable:** Collaborative trips with public sharing and discovery

---

## Phase 3: Trip Days & Itinerary Planning
**Goal:** Detailed day-by-day itinerary planning
**Deploy & Test:** Create trip days, plan activities, track transit

### Tasks

#### 3.1 Trip Days CRUD
- [ ] Register trip_days router in main.py (currently missing!)
- [ ] Update TripDay schema with all new fields
- [ ] Implement POST /trip_days/ (create day)
  - [ ] **Bruno:** Create `collection/trip-days/create-trip-day.bru`
  - [ ] Sample: Transit day, Sightseeing day, Leisure day
  - [ ] **Pytest:** Add `test_create_trip_day()` to `tests/test_trip_days.py`
- [ ] Implement GET /trip_days/?trip_id={id} (list days for trip)
  - [ ] **Bruno:** Create `collection/trip-days/list-trip-days.bru`
  - [ ] **Pytest:** Add `test_list_trip_days()`
- [ ] Implement GET /trip_days/{day_id} (get single day)
  - [ ] **Bruno:** Create `collection/trip-days/get-trip-day.bru`
  - [ ] **Pytest:** Add `test_get_trip_day()`
- [ ] Implement PUT /trip_days/{day_id} (update day)
  - [ ] **Bruno:** Create `collection/trip-days/update-trip-day.bru`
  - [ ] **Pytest:** Add `test_update_trip_day()`
- [ ] Implement DELETE /trip_days/{day_id} (delete day)
  - [ ] **Bruno:** Create `collection/trip-days/delete-trip-day.bru`
  - [ ] **Pytest:** Add `test_delete_trip_day()`
- [ ] Add authentication and permission checks (check trip collaborator role)
  - [ ] **Pytest:** Add `test_trip_day_permissions()`

#### 3.2 Activities & Bookings
- [ ] Design JSONB structure for activities
  ```json
  {
    "activities": [
      {"name": "Eiffel Tower", "time": "10:00", "duration": 2, "notes": "Book tickets online"}
    ]
  }
  ```
- [ ] Implement activity CRUD within trip days
  - [ ] Add activities to POST/PUT /trip_days/
  - [ ] **Bruno:** Update `create-trip-day.bru` with activities examples
  - [ ] **Pytest:** Add `test_trip_day_with_activities()`
- [ ] Design JSONB structure for bookings
  ```json
  {
    "bookings": [
      {"type": "tour", "name": "Paris Walking Tour", "confirmation": "ABC123", "cost": 50}
    ]
  }
  ```
- [ ] Implement booking CRUD within trip days
  - [ ] **Bruno:** Add bookings examples to trip day requests
  - [ ] **Pytest:** Add `test_trip_day_with_bookings()`
- [ ] Add validation for activity/booking data (Pydantic schemas)

#### 3.3 Accommodation Tracking
- [ ] Add accommodation fields to TripDay schema
- [ ] Implement accommodation in trip day endpoints
  - [ ] **Bruno:** Update trip day requests with accommodation examples
  - [ ] Example: Hotel check-in/out times, confirmation numbers
  - [ ] **Pytest:** Add `test_trip_day_with_accommodation()`

#### 3.4 Trip Statistics & Auto-calculation
- [ ] Implement POST /trips/{trip_id}/calculate-destinations (auto-calculate from trip_days)
  - [ ] **Bruno:** Create `collection/trips/calculate-destinations.bru`
  - [ ] **Pytest:** Add `test_calculate_destinations()`
- [ ] Implement GET /trips/{trip_id}/summary (trip statistics)
  - [ ] **Bruno:** Create `collection/trips/trip-summary.bru`
  - [ ] Return: total days, countries count, cities count, budget vs actual
  - [ ] **Pytest:** Add `test_trip_summary()`
- [ ] Auto-update trip dates from trip_days (optional background job)
  - [ ] **Pytest:** Add `test_auto_update_trip_dates()`

#### 3.5 Testing & Validation
- [ ] **Bruno:** End-to-end itinerary testing
  - [ ] Create trip "Europe Trip"
  - [ ] Add Day 1: Transit (flight to Paris)
  - [ ] Add Day 2: Sightseeing (Eiffel Tower, Louvre)
  - [ ] Add Day 3: Leisure (rest day)
  - [ ] Add Day 4: Transit (train to London, timezone change)
  - [ ] Calculate destinations (should show France, UK)
  - [ ] Get trip summary
- [ ] **Pytest:** Run full trip days test suite
  - [ ] Run `pytest tests/test_trip_days.py -v`
  - [ ] Test different day types
  - [ ] Test timezone changes
  - [ ] Test activities and bookings
  - [ ] Verify all tests pass

**Deliverable:** Complete itinerary planning with day-by-day details

---

## Phase 4: Expenses & Budget Tracking
**Goal:** Track trip expenses and manage budget
**Deploy & Test:** Add expenses, categorize, track against budget

### Tasks

#### 4.1 Expense Model & CRUD
- [ ] Create Expense model (amount, category, date, description, etc.)
- [ ] Create expenses CRUD operations
- [ ] Implement POST /expenses/ (create expense)
  - [ ] **Bruno:** Create `collection/expenses/create-expense.bru`
  - [ ] Examples: Hotel, restaurant, flight, activity
  - [ ] **Pytest:** Add `test_create_expense()` to `tests/test_expenses.py`
- [ ] Implement GET /expenses/?trip_id={id} (list expenses for trip)
  - [ ] **Bruno:** Create `collection/expenses/list-expenses.bru`
  - [ ] **Pytest:** Add `test_list_expenses()`
- [ ] Implement GET /expenses/{expense_id} (get single expense)
  - [ ] **Bruno:** Create `collection/expenses/get-expense.bru`
  - [ ] **Pytest:** Add `test_get_expense()`
- [ ] Implement PUT /expenses/{expense_id} (update expense)
  - [ ] **Bruno:** Create `collection/expenses/update-expense.bru`
  - [ ] **Pytest:** Add `test_update_expense()`
- [ ] Implement DELETE /expenses/{expense_id} (delete expense)
  - [ ] **Bruno:** Create `collection/expenses/delete-expense.bru`
  - [ ] **Pytest:** Add `test_delete_expense()`
- [ ] Add expense categories enum (accommodation, food, transport, activities, shopping, other)
  - [ ] **Pytest:** Add `test_expense_categories()`
- [ ] Add split expense functionality (for collaborative trips)
  - [ ] **Bruno:** Create `collection/expenses/split-expense.bru`
  - [ ] **Pytest:** Add `test_split_expense()`

#### 4.2 Budget Management
- [ ] Add budget fields to Trip model (already in design)
- [ ] Implement GET /trips/{trip_id}/budget (budget summary)
  - [ ] **Bruno:** Create `collection/trips/budget-summary.bru`
  - [ ] Return: total budget, total spent, remaining, percent used
  - [ ] **Pytest:** Add `test_budget_summary()` to `tests/test_expenses.py`
- [ ] Implement GET /expenses/analytics?trip_id={id} (expense analytics)
  - [ ] **Bruno:** Create `collection/expenses/expense-analytics.bru`
  - [ ] Group by: category, day, user
  - [ ] **Pytest:** Add `test_expense_analytics()`
- [ ] Add currency conversion support (basic, use fixed rates or API)
  - [ ] **Pytest:** Add `test_currency_conversion()` (if implemented)

#### 4.3 Testing & Validation
- [ ] **Bruno:** End-to-end expense testing
  - [ ] Add expenses to a trip (hotel, meals, transport)
  - [ ] Test split expense with collaborators
  - [ ] Get budget summary (check remaining budget)
  - [ ] Get expense analytics (by category, by day)
- [ ] **Pytest:** Run expenses test suite
  - [ ] Run `pytest tests/test_expenses.py -v`
  - [ ] Test all CRUD operations
  - [ ] Test budget calculations
  - [ ] Test split expense logic
  - [ ] Verify all tests pass

**Deliverable:** Complete expense tracking and budget management

---

## Phase 5: Notes, Packing Lists & Additional Features
**Goal:** Travel preparation and memory keeping
**Deploy & Test:** Create packing lists, take notes, track weather

### Tasks

#### 5.1 Notes System
- [ ] Create Note model (linked to trip or trip_day)
- [ ] Create notes CRUD operations
- [ ] Implement POST /notes/ (create note)
  - [ ] **Bruno:** Create `collection/notes/create-note.bru`
  - [ ] **Pytest:** Add `test_create_note()` to `tests/test_notes.py`
- [ ] Implement GET /notes/?trip_id={id} (list notes for trip)
  - [ ] **Bruno:** Create `collection/notes/list-notes.bru`
  - [ ] **Pytest:** Add `test_list_notes()`
- [ ] Implement GET /notes/{note_id}, PUT /notes/{note_id}, DELETE /notes/{note_id}
  - [ ] **Bruno:** Create corresponding .bru files
  - [ ] **Pytest:** Add corresponding tests
- [ ] Add rich text notes (markdown support)
  - [ ] **Pytest:** Add `test_markdown_rendering()`
- [ ] Add note categories (general, tips, memories, etc.)
  - [ ] **Pytest:** Add `test_note_categories()`

#### 5.2 Packing Lists
- [ ] Create PackingList model
- [ ] Create PackingItem model
- [ ] Implement POST /packing-lists/ (create packing list)
  - [ ] **Bruno:** Create `collection/packing-lists/create-packing-list.bru`
  - [ ] **Pytest:** Add `test_create_packing_list()` to `tests/test_packing.py`
- [ ] Implement POST /packing-lists/{list_id}/items (add item)
  - [ ] **Bruno:** Create `collection/packing-lists/add-item.bru`
  - [ ] **Pytest:** Add `test_add_packing_item()`
- [ ] Implement PUT /packing-lists/{list_id}/items/{item_id} (mark as packed)
  - [ ] **Bruno:** Create `collection/packing-lists/update-item-status.bru`
  - [ ] **Pytest:** Add `test_update_item_status()`
- [ ] Add packing categories (clothing, electronics, documents, toiletries, etc.)
  - [ ] **Pytest:** Add `test_packing_categories()`
- [ ] Implement GET /packing-lists/?trip_id={id} (get packing list for trip)
  - [ ] **Bruno:** Create `collection/packing-lists/get-packing-list.bru`
  - [ ] **Pytest:** Add `test_get_packing_list()`

#### 5.3 Weather Integration (Optional)
- [ ] Research weather API (OpenWeatherMap, WeatherAPI, etc.)
- [ ] Add weather forecast to trip_days
- [ ] Implement GET /trip_days/{day_id}/weather (fetch weather)
  - [ ] **Bruno:** Create `collection/trip-days/get-weather.bru`
  - [ ] **Pytest:** Add `test_fetch_weather()` (mock API response)
- [ ] Implement weather caching (Redis or database)
  - [ ] **Pytest:** Add `test_weather_caching()`

#### 5.4 Tags & Search
- [ ] Implement tag management (add/remove tags from trips)
  - [ ] **Bruno:** Add tags to `create-trip.bru` and `update-trip.bru`
  - [ ] **Pytest:** Add `test_trip_tags()`
- [ ] Implement GET /trips/search?q={query} (search trips)
  - [ ] **Bruno:** Create `collection/trips/search-trips.bru`
  - [ ] Search by: name, description, tags, location
  - [ ] **Pytest:** Add `test_search_trips()`
- [ ] Add filters to GET /trips/ (by status, dates, location)
  - [ ] **Bruno:** Update `list-trips.bru` with filter examples
  - [ ] **Pytest:** Add `test_filter_trips()`

#### 5.5 Testing & Validation
- [ ] **Bruno:** End-to-end testing of Phase 5 features
  - [ ] Create notes for a trip
  - [ ] Create packing list and mark items as packed
  - [ ] Fetch weather for trip days
  - [ ] Search trips by keyword
  - [ ] Filter trips by tags and location
- [ ] **Pytest:** Run Phase 5 test suite
  - [ ] Run `pytest tests/test_notes.py -v`
  - [ ] Run `pytest tests/test_packing.py -v`
  - [ ] Run `pytest tests/test_search.py -v`
  - [ ] Verify all tests pass

**Deliverable:** Travel preparation tools and note-taking

---

## Phase 6: Media Storage (LOWEST PRIORITY)
**Goal:** Photo and receipt uploads
**Deploy & Test:** Upload photos and receipts, attach to trips/days

### Tasks

#### 6.1 File Upload Infrastructure
- [ ] Choose storage solution (AWS S3, Cloudinary, or local for dev)
- [ ] Set up storage bucket/configuration
- [ ] Install dependencies (boto3 for S3, cloudinary SDK, or python-multipart for local)
- [ ] Create file upload utility functions (app/utils/storage.py)
  - [ ] **Pytest:** Add `test_file_upload()` to `tests/test_storage.py`
- [ ] Add file validation (type, size, mimetype)
  - [ ] **Pytest:** Add `test_file_validation()`
- [ ] Implement file compression for photos (Pillow library)
  - [ ] **Pytest:** Add `test_image_compression()`

#### 6.2 Photos Model & API
- [ ] Create Photo model
- [ ] Implement POST /photos/ (upload photo)
  - [ ] **Bruno:** Create `collection/photos/upload-photo.bru`
  - [ ] Note: Bruno supports file uploads (multipart/form-data)
  - [ ] **Pytest:** Add `test_upload_photo()` to `tests/test_photos.py`
- [ ] Implement GET /photos/?trip_id={id} (list photos)
  - [ ] **Bruno:** Create `collection/photos/list-photos.bru`
  - [ ] **Pytest:** Add `test_list_photos()`
- [ ] Implement DELETE /photos/{photo_id} (delete photo)
  - [ ] **Bruno:** Create `collection/photos/delete-photo.bru`
  - [ ] **Pytest:** Add `test_delete_photo()`
- [ ] Link photos to trips and trip_days
  - [ ] **Pytest:** Add `test_photo_associations()`
- [ ] Generate thumbnails (Pillow library)
  - [ ] **Pytest:** Add `test_thumbnail_generation()`

#### 6.3 Receipts/Documents
- [ ] Create Receipt model
- [ ] Implement POST /receipts/ (upload receipt, linked to expense)
  - [ ] **Bruno:** Create `collection/receipts/upload-receipt.bru`
  - [ ] **Pytest:** Add `test_upload_receipt()` to `tests/test_receipts.py`
- [ ] Implement GET /receipts/?expense_id={id} (get receipt for expense)
  - [ ] **Bruno:** Create `collection/receipts/get-receipt.bru`
  - [ ] **Pytest:** Add `test_get_receipt()`
- [ ] Add OCR for receipt parsing (optional, advanced - Tesseract, Google Vision API)
  - [ ] **Pytest:** Add `test_ocr_receipt_parsing()` (if implemented)

#### 6.4 Testing & Validation
- [ ] **Bruno:** End-to-end media testing
  - [ ] Upload photo to trip
  - [ ] Upload multiple photos to trip day
  - [ ] Upload receipt for expense
  - [ ] Test file size limit (expect 413 error)
  - [ ] Test invalid file type (expect 400 error)
- [ ] **Pytest:** Run media test suite
  - [ ] Run `pytest tests/test_photos.py -v`
  - [ ] Run `pytest tests/test_receipts.py -v`
  - [ ] Run `pytest tests/test_storage.py -v`
  - [ ] Verify all tests pass

**Deliverable:** Complete media storage functionality

---

## Cross-Cutting Concerns (Throughout All Phases)

### Testing Strategy
This is now integrated into each phase! Every feature includes:
- ✅ Bruno collection files (manual testing)
- ✅ Pytest test cases (automated testing)
- ✅ End-to-end validation

### Documentation
This is now integrated into each phase! Tasks include:
- ✅ Creating Bruno .bru files with sample data
- ✅ Adding request/response examples
- ✅ Updating README.md with testing instructions

### Deployment
- [ ] Set up deployment environment (Heroku, AWS, Railway, etc.)
- [ ] Configure production database
- [ ] Set up environment variables
- [ ] Configure CORS for frontend
- [ ] Set up logging and monitoring
- [ ] Deploy after each phase

### Security
- [ ] Validate all input data (Pydantic schemas)
- [ ] Implement rate limiting
- [ ] Add CORS configuration
- [ ] Secure environment variables
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention

---

## Recommended Priority Order

Based on "start with less and most important parts":

### **HIGH PRIORITY** (Start Here)
1. **Phase 1** - Foundation & Core Trip Management ⭐⭐⭐
2. **Phase 3** - Trip Days & Itinerary Planning ⭐⭐⭐
3. **Phase 2** - Trip Collaboration & Sharing ⭐⭐

### **MEDIUM PRIORITY** (After Core)
4. **Phase 4** - Expenses & Budget Tracking ⭐⭐
5. **Phase 5** - Notes, Packing Lists ⭐

### **LOW PRIORITY** (Last)
6. **Phase 6** - Media Storage ⏸️

---

## Suggested Starting Point

**My Recommendation:** Start with this minimal viable product (MVP):

### MVP Scope (2-3 weeks)
1. **Phase 1** - Get trips working with Google OAuth
2. **Phase 3.1-3.3** - Basic trip days (skip statistics for now)
3. **Skip everything else initially**

This gives you:
- ✅ Authentication
- ✅ Create/edit trips with flexible dates
- ✅ Plan day-by-day itinerary
- ✅ Track locations and timezones
- ✅ Add activities and accommodations
- ✅ Deploy and test with Bruno

Then add:
- **Phase 2** for collaboration (if needed)
- **Phase 4** for expenses (high user value)
- **Phase 5** for notes/packing (nice to have)
- **Phase 6** dead last (photos are low priority as you mentioned)

---

## Next Steps

1. **Review this plan** and let me know priority changes
2. **Choose starting scope** (I suggest MVP above)
3. **Set up development environment** (PostgreSQL, Google OAuth)
4. **Start with Phase 1, Task 1.1** 🚀

Let me know what you think!
