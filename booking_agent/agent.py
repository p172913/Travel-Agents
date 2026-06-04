from datetime import date
from typing import List
from .schemas import BookingResult, Flight, Hotel


async def run_booking_search(destination: str, start_date: str, end_date: str, travelers: int = 1) -> BookingResult:
    """Prototype booking search that returns mocked flight and hotel options.

    This function is a stand-in for real API integrations (Amadeus, Skyscanner).
    It returns deterministic sample data suitable for local development and tests.
    """
    # For prototype, return simple deterministic mock results
    flights: List[Flight] = [
        Flight(
            provider="MockAir",
            flight_number="MA123",
            depart_time="2026-07-01T09:00:00",
            arrive_time="2026-07-01T12:00:00",
            duration_minutes=180,
            price=150.0 * travelers,
            currency="USD"
        ),
        Flight(
            provider="MockSky",
            flight_number="MS456",
            depart_time="2026-07-01T14:00:00",
            arrive_time="2026-07-01T17:30:00",
            duration_minutes=210,
            price=175.0 * travelers,
            currency="USD"
        )
    ]

    hotels: List[Hotel] = [
        Hotel(
            provider="MockHotels",
            hotel_name="Seaside Resort",
            check_in=start_date,
            check_out=end_date,
            nightly_rate=75.0,
            total_price=75.0 * 3,
            rating=4.3
        ),
        Hotel(
            provider="BudgetStay",
            hotel_name="City Inn",
            check_in=start_date,
            check_out=end_date,
            nightly_rate=45.0,
            total_price=45.0 * 3,
            rating=3.8
        )
    ]

    return BookingResult(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        best_flights=flights,
        best_hotels=hotels
    )
