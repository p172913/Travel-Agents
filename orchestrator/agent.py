import asyncio
import time
from .schemas import OrchestratorInput, MergedTripPlan
from research_agent.agent import run_research
from budget_agent.agent import run_budget_analysis
from booking_agent.agent import run_booking_search
from recommendation_agent.agent import run_recommendation_engine


async def orchestrate_trip_plan(input_data: OrchestratorInput) -> MergedTripPlan:
    """Orchestrate a complete trip plan by running all agents in parallel and merging results.
    
    This is a prototype coordinator that runs agents concurrently and merges their outputs.
    In production, this uses LangGraph for state management and workflow control.
    """
    start_time = time.time()
    
    # Extract month from start_date if available
    month = start_date_to_month(input_data.start_date)
    
    # Run all agents concurrently
    try:
        research_task = run_research(input_data.destination, month)
        budget_task = run_budget_analysis(
            destination=input_data.destination,
            total_budget=input_data.total_budget,
            duration_days=days_between_dates(input_data.start_date, input_data.end_date) or 7,
            travel_style=input_data.travel_style
        )
        booking_task = run_booking_search(
            destination=input_data.destination,
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            travelers=input_data.travelers
        )
        recommendation_task = run_recommendation_engine(
            destination=input_data.destination,
            travel_style=input_data.travel_style,
            interests=["sightseeing", "food", "culture"]
        )
        
        # Await all tasks concurrently
        research_result, budget_result, booking_result, recommendation_result = await asyncio.gather(
            research_task,
            budget_task,
            booking_task,
            recommendation_task,
            return_exceptions=False
        )
        
        # Merge results into unified trip plan
        execution_time = (time.time() - start_time) * 1000
        
        merged_plan = MergedTripPlan(
            trip_id=input_data.trip_id,
            destination=input_data.destination,
            itinerary={
                "days": [
                    {
                        "day": i + 1,
                        "attractions": [r.name for r in recommendation_result.recommendations[:2]]
                        if recommendation_result.recommendations else []
                    }
                    for i in range(days_between_dates(input_data.start_date, input_data.end_date) or 3)
                ]
            },
            budget_breakdown=budget_result.allocation.dict() if hasattr(budget_result, 'allocation') else {},
            flights=[f.dict() for f in booking_result.best_flights] if booking_result.best_flights else [],
            hotels=[h.dict() for h in booking_result.best_hotels] if booking_result.best_hotels else [],
            recommendations=[r.dict() for r in recommendation_result.recommendations] if recommendation_result.recommendations else [],
            explanations={
                "research": f"Researched {input_data.destination}",
                "budget": f"Allocated ₹{input_data.total_budget} across categories",
                "bookings": f"Found {len(booking_result.best_flights)} flights and {len(booking_result.best_hotels)} hotels",
                "recommendations": f"Generated {len(recommendation_result.recommendations)} personalized recommendations"
            },
            execution_time_ms=execution_time
        )
        
        return merged_plan
        
    except Exception as e:
        raise RuntimeError(f"Orchestration failed: {str(e)}")


def start_date_to_month(date_str: str) -> str:
    """Extract month name from date string (YYYY-MM-DD)."""
    try:
        parts = date_str.split("-")
        if len(parts) >= 2:
            month_num = int(parts[1])
            months = ["", "January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
            return months[month_num] if 1 <= month_num <= 12 else "Month"
    except:
        pass
    return "Month"


def days_between_dates(start: str, end: str) -> int:
    """Calculate days between two date strings (YYYY-MM-DD)."""
    try:
        from datetime import datetime
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        end_obj = datetime.strptime(end, "%Y-%m-%d")
        return (end_obj - start_obj).days
    except:
        return 7  # Default to 7 days
