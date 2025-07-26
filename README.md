# Logbook

Logbook will be a comprehensive travel app that allows users to plan, track, and log their trips, including itinerary details, expenses, and memories.

## Features

*   **Create Trips:** Add new trips with a name and start/end dates.
*   **View Trips:** Retrieve a list of all trips or a single trip by its ID.

## API Endpoints

The following API endpoints are currently available:

*   `POST /trips/`: Create a new trip.
    *   **Request Body:**
        ```json
        {
          "name": "string",
          "start_date_timestamp": 0,
          "end_date_timestamp": 0
        }
        ```
*   `GET /trips/`: Get a list of all trips.
*   `GET /trips/{trip_id}`: Get a specific trip by its ID.

## API Documentation

You can access the interactive API documentation when the server is running:

*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

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
    The server will start, and you can access the API at `http://127.0.0.1:8000`.
    ```bash
    uvicorn app.main:app --reload
    ```
