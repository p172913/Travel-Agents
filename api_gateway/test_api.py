import datetime
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import Base, get_db
from shared.models import User, Trip
from main import app

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_list_trips_empty_by_default():
    response = client.get("/api/trips")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []


def test_get_trip_details_not_found():
    response = client.get("/api/trips/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 9999 not found"


def test_trip_endpoints_return_saved_trip():
    db = TestingSessionLocal()
    user = User(email="default@travelsouls.com", full_name="Default Traveler")
    db.add(user)
    db.commit()
    db.refresh(user)

    trip = Trip(
        user_id=user.id,
        title="Test Trip",
        destination="Goa",
        start_date=datetime.date(2026, 7, 1),
        end_date=datetime.date(2026, 7, 5),
        budget_limit=50000.0,
        status="planning",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    db.close()

    list_response = client.get("/api/trips")
    assert list_response.status_code == 200
    data = list_response.json()
    assert any(item["trip_id"] == trip.id for item in data)
    assert "share_token" in data[0]

    detail_response = client.get(f"/api/trips/{trip.id}")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["trip_id"] == trip.id
    assert detail_data["destination"] == "Goa"
    assert detail_data["plans"] == []
    assert "share_url" in detail_data
