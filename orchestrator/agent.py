from .schemas import OrchestratorInput, MergedTripPlan
from .graph import run_langgraph_orchestration

# Re-export itinerary helpers for backward compatibility
from .itinerary import build_itinerary, days_between_dates, start_date_to_month  # noqa: F401


async def orchestrate_trip_plan(input_data: OrchestratorInput) -> MergedTripPlan:
    """Orchestrate a complete trip plan via LangGraph multi-agent workflow."""
    return await run_langgraph_orchestration(input_data)
