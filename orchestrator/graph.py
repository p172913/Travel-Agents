"""LangGraph workflow for multi-agent trip orchestration."""

import time
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from budget_agent.agent import run_budget_analysis
from booking_agent.agent import run_booking_search
from recommendation_agent.agent import run_recommendation_engine
from research_agent.agent import run_research
from shared.explainability import build_plan_explanations

from .itinerary import build_itinerary, days_between_dates, start_date_to_month
from .schemas import MergedTripPlan, OrchestratorInput


class OrchestratorState(TypedDict):
    input: OrchestratorInput
    research: Optional[Any]
    budget: Optional[Any]
    booking: Optional[Any]
    recommendation: Optional[Any]
    error: Optional[str]
    merged_plan: Optional[MergedTripPlan]
    start_time: float


async def run_parallel_agents(state: OrchestratorState) -> Dict[str, Any]:
    """Fan-in node: run all four agents concurrently."""
    inp = state["input"]
    month = start_date_to_month(inp.start_date)
    duration_days = max(days_between_dates(inp.start_date, inp.end_date), 1)
    try:
        import asyncio
        research, budget, booking, recommendation = await asyncio.gather(
            run_research(inp.destination, month),
            run_budget_analysis(inp.destination, inp.total_budget, duration_days, inp.travel_style),
            run_booking_search(inp.destination, inp.start_date, inp.end_date, inp.travelers),
            run_recommendation_engine(inp.destination, inp.travel_style, interests=["sightseeing", "food", "culture"], user_id=1),
            return_exceptions=True,
        )
        errors = []
        for name, result in [("research", research), ("budget", budget), ("booking", booking), ("recommendation", recommendation)]:
            if isinstance(result, Exception):
                errors.append(f"{name}: {result}")
        if len(errors) == 4:
            return {"error": "; ".join(errors)}
        return {
            "research": research if not isinstance(research, Exception) else None,
            "budget": budget if not isinstance(budget, Exception) else None,
            "booking": booking if not isinstance(booking, Exception) else None,
            "recommendation": recommendation if not isinstance(recommendation, Exception) else None,
            "error": "; ".join(errors) if errors else None,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def merge_results(state: OrchestratorState) -> Dict[str, Any]:
    """Merge agent outputs into a final trip plan with explainability."""
    inp = state["input"]
    research = state.get("research")
    budget = state.get("budget")
    booking = state.get("booking")
    recommendation = state.get("recommendation")

    if not all([research, budget, booking, recommendation]):
        return {"error": state.get("error") or "One or more agents failed to produce results"}

    execution_time = (time.time() - state["start_time"]) * 1000
    itinerary = build_itinerary(inp.start_date, inp.end_date, booking, recommendation, budget)
    explanations = build_plan_explanations(research, budget, booking, recommendation, inp.travel_style)

    merged = MergedTripPlan(
        trip_id=inp.trip_id,
        destination=inp.destination,
        itinerary=itinerary,
        budget_breakdown=budget.allocation.model_dump() if hasattr(budget, "allocation") else {},
        flights=[f.model_dump() for f in booking.best_flights] if booking.best_flights else [],
        hotels=[h.model_dump() for h in booking.best_hotels] if booking.best_hotels else [],
        recommendations=[r.model_dump() for r in recommendation.recommendations] if recommendation.recommendations else [],
        explanations={
            "research": explanations["research"]["summary"],
            "budget": explanations["budget"]["summary"],
            "bookings": f"Found {len(booking.best_flights)} flights and {len(booking.best_hotels)} hotels",
            "recommendations": f"Generated {len(recommendation.recommendations)} personalized recommendations",
            "structured": explanations,
        },
        execution_time_ms=execution_time,
    )
    return {"merged_plan": merged}


def build_orchestrator_graph():
    """Compile the LangGraph orchestration workflow."""
    builder = StateGraph(OrchestratorState)
    builder.add_node("run_agents", run_parallel_agents)
    builder.add_node("merge", merge_results)
    builder.add_edge(START, "run_agents")
    builder.add_edge("run_agents", "merge")
    builder.add_edge("merge", END)
    return builder.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_orchestrator_graph()
    return _graph


async def run_langgraph_orchestration(input_data: OrchestratorInput) -> MergedTripPlan:
    graph = get_graph()
    initial: OrchestratorState = {
        "input": input_data,
        "research": None,
        "budget": None,
        "booking": None,
        "recommendation": None,
        "error": None,
        "merged_plan": None,
        "start_time": time.time(),
    }
    result = await graph.ainvoke(initial)
    if result.get("error") and not result.get("merged_plan"):
        raise RuntimeError(result["error"])
    if not result.get("merged_plan"):
        raise RuntimeError("Orchestration produced no plan")
    return result["merged_plan"]
