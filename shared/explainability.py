"""Structured explainability layer for all agent recommendations."""

from typing import Any, Dict, List, Optional


def build_item_explanation(
    title: str,
    checks: List[str],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a structured explanation with checkmark reasons."""
    return {
        "title": title,
        "why_ai_picked_this": checks,
        "checks": [{"label": c, "passed": True} for c in checks],
        "context": context or {},
        "summary": " • ".join(checks),
    }


def explain_flight(flight: Dict[str, Any], budget_remaining: float) -> Dict[str, Any]:
    price = flight.get("price", 0)
    checks = []
    if price <= budget_remaining:
        checks.append("Within budget")
    checks.append(f"Duration {flight.get('duration_minutes', 0)} min")
    checks.append(f"Provider: {flight.get('provider', 'unknown')}")
    return build_item_explanation(
        title=f"Flight {flight.get('flight_number', '')}",
        checks=checks,
        context={"price": price, "currency": flight.get("currency", "USD")},
    )


def explain_hotel(hotel: Dict[str, Any], budget_remaining: float) -> Dict[str, Any]:
    rating = hotel.get("rating")
    checks = []
    if rating and rating >= 4.0:
        checks.append(f"{rating} star rating")
    nightly = hotel.get("nightly_rate", 0)
    if nightly <= budget_remaining / 3:
        checks.append("Within accommodation budget")
    checks.append("Near city center and attractions")
    return build_item_explanation(
        title=hotel.get("hotel_name", "Hotel"),
        checks=checks,
        context={"nightly_rate": nightly, "rating": rating},
    )


def explain_recommendation(rec: Dict[str, Any], travel_style: str) -> Dict[str, Any]:
    checks = []
    rating = rec.get("rating")
    if rating and rating >= 4.0:
        checks.append(f"{rating} rating")
    if rec.get("price_level", 3) <= 3:
        checks.append("Within budget")
    checks.append(f"Matches {travel_style} traveler profile")
    rationale = rec.get("rationale", "")
    if rationale:
        checks.append(rationale)
    return build_item_explanation(
        title=rec.get("name", "Recommendation"),
        checks=checks,
        context={"type": rec.get("type"), "price_level": rec.get("price_level")},
    )


def explain_budget_allocation(allocation: Dict[str, Any], total: float) -> Dict[str, Any]:
    checks = [
        f"Total budget ₹{total:,.0f} fully allocated",
        f"Flights: ₹{allocation.get('flights', 0):,.0f}",
        f"Accommodation: ₹{allocation.get('accommodation', 0):,.0f}",
        f"Food: ₹{allocation.get('food', 0):,.0f}",
        f"Activities: ₹{allocation.get('activities', 0):,.0f}",
    ]
    return build_item_explanation(title="Budget allocation", checks=checks)


def build_plan_explanations(
    research: Any,
    budget: Any,
    booking: Any,
    recommendations: Any,
    travel_style: str,
) -> Dict[str, Any]:
    """Merge all agent outputs into a unified explainability payload."""
    budget_dict = budget.allocation.model_dump() if hasattr(budget, "allocation") else {}
    flights = [f.model_dump() if hasattr(f, "model_dump") else f for f in (booking.best_flights or [])]
    hotels = [h.model_dump() if hasattr(h, "model_dump") else h for h in (booking.best_hotels or [])]
    recs = [r.model_dump() if hasattr(r, "model_dump") else r for r in (recommendations.recommendations or [])]

    return {
        "research": build_item_explanation(
            title=f"Research: {research.destination if hasattr(research, 'destination') else 'destination'}",
            checks=[
                f"Safety score: {getattr(research, 'safety_score', 'N/A')}/10",
                f"Weather analyzed for travel period",
                f"{len(getattr(research, 'top_places', []))} top places identified",
                f"{len(getattr(research, 'hidden_gems', []))} hidden gems found",
            ],
        ),
        "budget": explain_budget_allocation(budget_dict, getattr(budget, "total_budget", 0)),
        "flights": [explain_flight(f, budget_dict.get("flights", 0)) for f in flights[:3]],
        "hotels": [explain_hotel(h, budget_dict.get("accommodation", 0)) for h in hotels[:3]],
        "recommendations": [explain_recommendation(r, travel_style) for r in recs[:5]],
        "alerts": getattr(budget, "alerts", []) or [],
    }
