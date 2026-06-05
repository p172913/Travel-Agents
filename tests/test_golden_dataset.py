"""Golden dataset validation for AI travel prompts."""

import asyncio
import pytest

from orchestrator.agent import orchestrate_trip_plan
from orchestrator.schemas import OrchestratorInput

GOLDEN_PROMPTS = [
    {"destination": "Goa", "start_date": "2026-07-01", "end_date": "2026-07-05", "total_budget": 50000, "travel_style": "balanced"},
    {"destination": "Tokyo", "start_date": "2026-04-10", "end_date": "2026-04-17", "total_budget": 150000, "travel_style": "luxury"},
    {"destination": "Dubai", "start_date": "2026-12-01", "end_date": "2026-12-06", "total_budget": 80000, "travel_style": "family"},
    {"destination": "Paris", "start_date": "2026-06-15", "end_date": "2026-06-20", "total_budget": 120000, "travel_style": "balanced"},
    {"destination": "Bali", "start_date": "2026-08-01", "end_date": "2026-08-08", "total_budget": 60000, "travel_style": "adventure"},
]


@pytest.mark.parametrize("prompt", GOLDEN_PROMPTS)
def test_golden_prompt_produces_valid_plan(prompt):
    input_data = OrchestratorInput(trip_id=1, travelers=2, **prompt)
    result = asyncio.run(orchestrate_trip_plan(input_data))

    assert result.destination == prompt["destination"]
    assert isinstance(result.itinerary, dict)
    assert "days" in result.itinerary
    assert len(result.itinerary["days"]) >= 1
    assert len(result.flights) >= 1
    assert len(result.hotels) >= 1
    assert len(result.recommendations) >= 1
    assert result.execution_time_ms > 0

    budget = result.budget_breakdown
    total = sum(budget.get(k, 0) for k in ["flights", "accommodation", "food", "activities", "misc"])
    assert abs(total - prompt["total_budget"]) < 1.0

    for day in result.itinerary["days"]:
        for item in day.get("items", []):
            assert "reason" in item
            assert item["reason"].strip()

    assert "structured" in result.explanations or "research" in result.explanations
