# Logbook Backend API

Logbook is a comprehensive travel app backend that allows users to plan, track, and log their trips, including itinerary details, expenses, and memories.

## Tech Stack

*   **Framework:** FastAPI
*   **Database:** SQLite with SQLAlchemy ORM
*   **API Testing:** Bruno API Collection

## Current Implementation Status

### Implemented Features

*   **Trip Management:** Create and retrieve trips with date tracking
*   **Trip Day Planning:** Track daily itinerary details including places, transit, and notes
*   **Transit Tracking:** Support for multiple transit modes (flight, train, bus, car, boat, other)

### Data Models

#### Trip
*   Name
*   Start date (timestamp)
*   End date (timestamp)
*   Related trip days

#### TripDay
*   Associated trip
*   Date
*   Place/location
*   Timezone
*   Arrival/departure times
*   Transit mode and details
*   Notes

## API Endpoints

### Trips

*   `POST /trips/`: Create a new trip
    *   **Request Body:**
        ```json
        {
          "name": "string",
          "start_date_timestamp": 0,
          "end_date_timestamp": 0
        }
        ```
*   `GET /trips/`: Get a list of all trips (supports pagination via skip/limit)
*   `GET /trips/{trip_id}`: Get a specific trip by its ID

### Trip Days (Implementation Note: Router not yet registered in main.py)

*   `POST /trip_days/`: Create a new trip day
*   `GET /trip_days/`: Get a list of all trip days
*   `GET /trip_days/{trip_day_id}`: Get a specific trip day by its ID

## API Documentation

You can access the interactive API documentation when the server is running:

*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Project Structure

```
logbook/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   └── api/                 # API route handlers
│       ├── trips.py
│       └── trip_days.py
├── collection/              # Bruno API collection
├── scripts/                 # Utility scripts
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

*   Python 3.8+

### Setup and Installation

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```

    The server will start, and you can access the API at `http://127.0.0.1:8000`.

## Roadmap

See [PRD.md](./PRD.md) for detailed product requirements and planned features including:

*   Complete CRUD operations for all entities
*   Expense tracking and budgeting
*   Photo and memory management
*   Packing lists
*   Weather integration
*   Authentication and authorization
*   And more...
