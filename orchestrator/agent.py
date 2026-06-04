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
    month = start_date_to_month(input_data.start_date)
    duration_days = max(days_between_dates(input_data.start_date, input_data.end_date), 1)

    try:
        research_task = run_research(input_data.destination, month)
        budget_task = run_budget_analysis(
            destination=input_data.destination,
            total_budget=input_data.total_budget,
            duration_days=duration_days,
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

        research_result, budget_result, booking_result, recommendation_result = await asyncio.gather(
            research_task,
            budget_task,
            booking_task,
            recommendation_task,
            return_exceptions=False
        )

        execution_time = (time.time() - start_time) * 1000
        itinerary = build_itinerary(
            input_data.start_date,
            input_data.end_date,
            booking_result,
            recommendation_result,
            budget_result
        )

        merged_plan = MergedTripPlan(
            trip_id=input_data.trip_id,
            destination=input_data.destination,
            itinerary=itinerary,
            budget_breakdown=budget_result.allocation.model_dump() if hasattr(budget_result, 'allocation') else {},
            flights=[f.model_dump() for f in booking_result.best_flights] if booking_result.best_flights else [],
            hotels=[h.model_dump() for h in booking_result.best_hotels] if booking_result.best_hotels else [],
            recommendations=[r.model_dump() for r in recommendation_result.recommendations] if recommendation_result.recommendations else [],
            explanations={
                "research": f"Researched {input_data.destination}",
                "budget": f"Allocated {input_data.total_budget} across categories",
                "bookings": f"Found {len(booking_result.best_flights)} flights and {len(booking_result.best_hotels)} hotels",
                "recommendations": f"Generated {len(recommendation_result.recommendations)} personalized recommendations"
            },
            execution_time_ms=execution_time
        )

        return merged_plan

    except Exception as e:
        raise RuntimeError(f"Orchestration failed: {str(e)}")


def build_itinerary(start_date: str, end_date: str, booking_result, recommendation_result, budget_result):
    """Create a structured itinerary from booking and recommendation results."""
    from datetime import datetime, timedelta

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception:
        from datetime import date
        start = date.today()
        end = start + timedelta(days=6)

    total_days = max((end - start).days, 1)
    days = []
    recs = recommendation_result.recommendations or []

    for day_index in range(total_days):
        current_date = start + timedelta(days=day_index)
        items = []

        if day_index == 0:
            if booking_result.best_flights:
                first_flight = booking_result.best_flights[0]
                items.append({
                    "time": "09:00",
                    "title": "Arrive at destination",
                    "details": f"Flight {first_flight.flight_number} arrives. Check in to hotel and relax.",
                    "reason": "Start the trip with arrival, settling in, and a smooth first-day plan."
                })
            items.append({
                "time": "12:00",
                "title": "Check in and lunch",
                "details": "Settle into accommodations and enjoy a local lunch nearby.",
                "reason": "Give travelers time to recharge after arrival and explore local food."
            })

        if recs:
            recommendation = recs[min(day_index, len(recs) - 1)]
            items.append({
                "time": "15:00",
                "title": recommendation.name,
                "details": recommendation.description or recommendation.rationale,
                "reason": recommendation.rationale or f"Recommended because it fits your {recommendation.type} preferences."
            })

        if booking_result.best_hotels and day_index == 0:
            items.append({
                "time": "18:00",
                "title": f"Stay at {booking_result.best_hotels[0].hotel_name}",
                "details": f"Nightly rate {booking_result.best_hotels[0].nightly_rate} {booking_result.best_hotels[0].rating} stars.",
                "reason": "This hotel is selected as a comfortable first-night stay near the destination."
            })

        if day_index == total_days - 1:
            items.append({
                "time": "17:00",
                "title": "Trip wrap-up",
                "details": "Review your itinerary, pack, and prepare for departure tomorrow.",
                "reason": "Finish the trip with a calm wrap-up and preparation for departure."
            })

        days.append({
            "day": day_index + 1,
            "date": current_date.isoformat(),
            "items": items
        })

    return {"days": days}


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
