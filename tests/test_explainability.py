from shared.explainability import (
    build_item_explanation,
    explain_budget_allocation,
    explain_flight,
    explain_hotel,
    explain_recommendation,
)


def test_build_item_explanation():
    result = build_item_explanation("Test", ["Within budget", "4.6 rating"])
    assert result["title"] == "Test"
    assert len(result["checks"]) == 2
    assert result["checks"][0]["passed"] is True


def test_explain_flight():
    result = explain_flight({"price": 100, "duration_minutes": 180, "provider": "Amadeus", "flight_number": "AI123"}, 200)
    assert "Within budget" in result["why_ai_picked_this"]


def test_explain_hotel():
    result = explain_hotel({"hotel_name": "Test Hotel", "nightly_rate": 50, "rating": 4.5}, 500)
    assert "4.5 star rating" in result["why_ai_picked_this"]


def test_explain_recommendation():
    result = explain_recommendation({"name": "Museum", "rating": 4.5, "price_level": 2, "rationale": "Cultural fit", "type": "attraction"}, "balanced")
    assert any("4.5" in c for c in result["why_ai_picked_this"])


def test_explain_budget():
    result = explain_budget_allocation({"flights": 20000, "accommodation": 15000, "food": 8000, "activities": 7000, "misc": 0}, 50000)
    assert "fully allocated" in result["summary"].lower() or "₹50,000" in result["summary"]
