import asyncio

from recommendation_agent.agent import run_recommendation_engine


def test_run_recommendation_engine_returns_structure():
    result = asyncio.get_event_loop().run_until_complete(
        run_recommendation_engine("Goa", travel_style="adventure")
    )

    assert result.destination == "Goa"
    assert result.travel_style == "adventure"
    assert isinstance(result.recommendations, list)
    assert len(result.recommendations) >= 1
    assert result.personalization_score > 0


def test_luxury_travel_style():
    result = asyncio.get_event_loop().run_until_complete(
        run_recommendation_engine("Paris", travel_style="luxury")
    )

    assert result.travel_style == "luxury"
    # Luxury recommendations should have higher price levels
    price_levels = [rec.price_level for rec in result.recommendations if rec.price_level]
    assert any(p >= 4 for p in price_levels), "Luxury recs should include high-price items"
