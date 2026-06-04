import asyncio

from orchestrator.agent import orchestrate_trip_plan
from orchestrator.schemas import OrchestratorInput


def test_orchestrate_trip_plan_returns_merged_plan():
    input_data = OrchestratorInput(
        trip_id=1,
        destination="Goa",
        start_date="2026-07-01",
        end_date="2026-07-04",
        total_budget=50000.0,
        travel_style="balanced",
        travelers=1
    )
    
    result = asyncio.run(orchestrate_trip_plan(input_data))
    
    assert result.trip_id == 1
    assert result.destination == "Goa"
    assert isinstance(result.itinerary, dict)
    assert "days" in result.itinerary
    assert len(result.flights) >= 1
    assert len(result.hotels) >= 1
    assert len(result.recommendations) >= 1
    assert result.execution_time_ms > 0
    # Ensure explainability metadata is present on itinerary items
    assert len(result.itinerary["days"]) >= 1
    for day in result.itinerary["days"]:
        assert "items" in day
        for item in day["items"]:
            assert "reason" in item
            assert isinstance(item["reason"], str)
            assert item["reason"].strip() != ""
