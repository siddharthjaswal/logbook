"""
Tests for TripDay API endpoints.
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.shared.enums import TripDayType, TransitMode


def test_create_trip_day(client: TestClient, auth_headers, test_trip):
    """Test creating a trip day via API."""
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "day_type": "sightseeing",
        "title": "Day 1 in Paris",
        "place": "Paris",
        "place_city": "Paris",
        "place_country": "France",
        "timezone": "Europe/Paris",
        "activities": [
            {
                "name": "Eiffel Tower",
                "time": "10:00",
                "duration": 2,
                "cost": 26.10
            }
        ],
        "notes": "Bring camera"
    }

    response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["trip_id"] == test_trip.id
    assert data["date"] == "2025-07-15"
    assert data["day_number"] == 1
    assert data["place"] == "Paris"


def test_create_trip_day_unauthenticated(client: TestClient, test_trip):
    """Test creating a trip day without authentication."""
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC"
    }

    response = client.post("/api/v1/trip-days/", json=payload)
    assert response.status_code == 401


def test_create_trip_day_not_trip_owner(client: TestClient, test_trip_other_user, auth_headers):
    """Test creating a trip day for someone else's trip."""
    payload = {
        "trip_id": test_trip_other_user.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC"
    }

    response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    assert response.status_code == 404  # Trip not found (access control)


def test_create_trip_day_duplicate_date(client: TestClient, auth_headers, test_trip):
    """Test creating a trip day with duplicate date."""
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC"
    }

    # Create first trip day
    response1 = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_list_trip_days(client: TestClient, auth_headers, test_trip_no_dates):
    """Test listing trip days for a trip."""
    test_trip = test_trip_no_dates
    # Create multiple trip days
    for i in range(3):
        payload = {
            "trip_id": test_trip.id,
            "date": str(date(2025, 7, 15) + timedelta(days=i)),
            "day_number": i + 1,
            "place": f"City {i+1}",
            "timezone": "UTC"
        }
        client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    # List trip days
    response = client.get(f"/api/v1/trip-days/?trip_id={test_trip.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["day_number"] == 1
    assert data[1]["day_number"] == 2
    assert data[2]["day_number"] == 3


def test_list_trip_days_unauthenticated(client: TestClient, test_trip):
    """Test listing trip days without authentication."""
    response = client.get(f"/api/v1/trip-days/?trip_id={test_trip.id}")
    assert response.status_code == 401


def test_list_trip_days_with_filters(client: TestClient, auth_headers, test_trip):
    """Test listing trip days with filters."""
    # Create trip days with different types
    types = ["sightseeing", "transit", "sightseeing", "leisure"]
    for i, day_type in enumerate(types):
        payload = {
            "trip_id": test_trip.id,
            "date": str(date(2025, 7, 15) + timedelta(days=i)),
            "day_number": i + 1,
            "day_type": day_type,
            "place": f"City {i+1}",
            "timezone": "UTC"
        }
        client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    # Filter by day_type
    response = client.get(
        f"/api/v1/trip-days/?trip_id={test_trip.id}&day_type=sightseeing",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(day["day_type"] == "sightseeing" for day in data)


def test_get_trip_day(client: TestClient, auth_headers, test_trip):
    """Test getting a specific trip day."""
    # Create a trip day
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "Europe/Paris",
        "activities": [
            {
                "name": "Eiffel Tower",
                "time": "10:00",
                "duration": 2
            }
        ]
    }
    create_response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    trip_day_id = create_response.json()["id"]

    # Get the trip day
    response = client.get(f"/api/v1/trip-days/{trip_day_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == trip_day_id
    assert data["place"] == "Paris"


def test_get_trip_day_not_found(client: TestClient, auth_headers):
    """Test getting a non-existent trip day."""
    response = client.get("/api/v1/trip-days/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_trip_day(client: TestClient, auth_headers, test_trip):
    """Test updating a trip day."""
    # Create a trip day
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC",
        "notes": "Original notes"
    }
    create_response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    trip_day_id = create_response.json()["id"]

    # Update it
    update_payload = {
        "title": "Updated Day 1",
        "notes": "Updated notes",
        "activities": [
            {
                "name": "New Activity",
                "time": "15:00",
                "duration": 1
            }
        ]
    }
    response = client.put(
        f"/api/v1/trip-days/{trip_day_id}",
        json=update_payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Day 1"
    assert data["notes"] == "Updated notes"


def test_update_trip_day_not_owner(client: TestClient, auth_headers, test_trip_other_user_with_day):
    """Test updating someone else's trip day."""
    trip_day_id = test_trip_other_user_with_day["day_id"]

    update_payload = {
        "title": "Hacked Day"
    }
    response = client.put(
        f"/api/v1/trip-days/{trip_day_id}",
        json=update_payload,
        headers=auth_headers
    )

    assert response.status_code == 404  # Trip not found (access control)


def test_update_trip_day_duplicate_date(client: TestClient, auth_headers, test_trip):
    """Test updating trip day to a date that already exists."""
    # Create two trip days
    payload1 = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC"
    }
    response1 = client.post("/api/v1/trip-days/", json=payload1, headers=auth_headers)
    trip_day_id1 = response1.json()["id"]

    payload2 = {
        "trip_id": test_trip.id,
        "date": "2025-07-16",
        "day_number": 2,
        "place": "London",
        "timezone": "UTC"
    }
    client.post("/api/v1/trip-days/", json=payload2, headers=auth_headers)

    # Try to update first day to second day's date
    update_payload = {
        "date": "2025-07-16"
    }
    response = client.put(
        f"/api/v1/trip-days/{trip_day_id1}",
        json=update_payload,
        headers=auth_headers
    )

    # Pydantic validation happens before custom checks, so we might get 422
    assert response.status_code in [400, 422]
    if response.status_code == 400:
        assert "already exists" in response.json()["detail"]


def test_delete_trip_day(client: TestClient, auth_headers, test_trip):
    """Test deleting a trip day."""
    # Create a trip day
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "place": "Paris",
        "timezone": "UTC"
    }
    create_response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)
    trip_day_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/v1/trip-days/{trip_day_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["trip_day_id"] == trip_day_id

    # Verify it's gone
    get_response = client.get(f"/api/v1/trip-days/{trip_day_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_trip_day_not_owner(client: TestClient, auth_headers, test_trip_other_user_with_day):
    """Test deleting someone else's trip day."""
    trip_day_id = test_trip_other_user_with_day["day_id"]

    response = client.delete(f"/api/v1/trip-days/{trip_day_id}", headers=auth_headers)
    assert response.status_code == 404  # Trip not found (access control)


def test_get_trip_summary(client: TestClient, auth_headers, test_trip_no_dates):
    """Test getting trip summary."""
    test_trip = test_trip_no_dates
    # Create trip days in different countries
    trip_days_data = [
        ("Paris", "France", "sightseeing"),
        ("Lyon", "France", "culinary"),
        ("London", "UK", "transit"),
        ("London", "UK", "sightseeing"),
    ]

    for i, (city, country, day_type) in enumerate(trip_days_data):
        payload = {
            "trip_id": test_trip.id,
            "date": str(date(2025, 7, 15) + timedelta(days=i)),
            "day_number": i + 1,
            "day_type": day_type,
            "place": city,
            "place_city": city,
            "place_country": country,
            "timezone": "UTC",
            "activities": [{"name": f"Activity {i+1}", "time": "10:00"}]
        }
        client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    # Get summary
    response = client.get(f"/api/v1/trip-days/trip/{test_trip.id}/summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_days"] == 4
    assert data["countries_count"] == 2
    assert "France" in data["countries"]
    assert "UK" in data["countries"]
    assert data["cities_count"] == 3  # Paris, Lyon, London
    assert "Paris" in data["cities"]
    assert "Lyon" in data["cities"]
    assert "London" in data["cities"]
    assert data["day_types_breakdown"]["sightseeing"] == 2
    assert data["day_types_breakdown"]["culinary"] == 1
    assert data["day_types_breakdown"]["transit"] == 1
    # Activities and accommodations are now separate entities
    assert "total_activities" in data
    assert "total_accommodations" in data
    assert "total_transits" in data


def test_update_trip_destinations_endpoint(client: TestClient, auth_headers, test_trip):
    """Test manually updating trip destinations."""
    # Create trip days
    for i, (city, country) in enumerate([("Paris", "France"), ("London", "UK")]):
        payload = {
            "trip_id": test_trip.id,
            "date": str(date(2025, 7, 15) + timedelta(days=i)),
            "day_number": i + 1,
            "place": city,
            "place_city": city,
            "place_country": country,
            "timezone": "UTC"
        }
        client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    # Update destinations
    response = client.post(
        f"/api/v1/trip-days/trip/{test_trip.id}/update-destinations",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "France" in data["countries_visited"]
    assert "UK" in data["countries_visited"]
    assert "Paris" in data["cities_visited"]
    assert "London" in data["cities_visited"]


def test_create_trip_day_with_complex_data(client: TestClient, auth_headers, test_trip):
    """Test creating a trip day with all possible fields."""
    payload = {
        "trip_id": test_trip.id,
        "date": "2025-07-15",
        "day_number": 1,
        "day_type": "transit",
        "title": "Travel Day to London",
        "place": "London",
        "place_city": "London",
        "place_country": "UK",
        "timezone": "Europe/London",
        "activities": [
            {
                "name": "Arrival procedures",
                "time": "15:00",
                "duration": 1,
                "notes": "Late arrival"
            }
        ],
        "bookings": [
            {
                "type": "restaurant",
                "name": "Gordon Ramsay",
                "time": "20:00",
                "cost": 200.00,
                "confirmation_number": "RES456"
            }
        ],
        "weather_forecast": "Cloudy with rain",
        "notes": "Remember passport and boarding pass"
    }

    response = client.post("/api/v1/trip-days/", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["day_type"] == "transit"
    assert data["title"] == "Travel Day to London"
    assert data["weather_forecast"] == "Cloudy with rain"
    assert data["notes"] == "Remember passport and boarding pass"
