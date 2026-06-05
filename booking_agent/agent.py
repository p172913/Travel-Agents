import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cache import cached_json
from .amadeus import generate_mock_booking, search_amadeus_flights, search_amadeus_hotels
from .schemas import BookingResult


async def run_booking_search(
    destination: str,
    start_date: str,
    end_date: str,
    travelers: int = 1,
    origin: str = "DEL",
) -> BookingResult:
    """Search flights and hotels via Amadeus API with Redis caching and mock fallback."""

    async def _fetch():
        flights = await search_amadeus_flights(origin, destination, start_date, travelers)
        hotels = await search_amadeus_hotels(destination, start_date, end_date)
        if flights or hotels:
            mock = generate_mock_booking(destination, start_date, end_date, travelers)
            return BookingResult(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                best_flights=flights or mock.best_flights,
                best_hotels=hotels or mock.best_hotels,
            )
        return generate_mock_booking(destination, start_date, end_date, travelers)

    payload = await cached_json(
        "booking",
        (destination, start_date, end_date, str(travelers)),
        ttl=1800,
        fetcher=_fetch,
    )
    return BookingResult(**payload)
