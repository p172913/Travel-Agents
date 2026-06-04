import asyncio

from booking_agent.agent import run_booking_search


def test_run_booking_search_returns_structure():
    result = asyncio.get_event_loop().run_until_complete(
        run_booking_search("Goa", "2026-07-01", "2026-07-04", travelers=1)
    )

    assert result.destination == "Goa"
    assert isinstance(result.best_flights, list)
    assert isinstance(result.best_hotels, list)
    assert len(result.best_flights) >= 1
    assert len(result.best_hotels) >= 1
