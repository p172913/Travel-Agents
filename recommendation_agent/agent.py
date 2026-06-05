import os
import sys
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cache import cached_json
from shared.pinecone_store import query_similar_preferences, upsert_preference
from .schemas import RecommendationResult, Recommendation


def _base_recommendations(travel_style: str) -> List[Recommendation]:
    recommendations_map = {
        "adventure": [
            Recommendation(id="rec_001", type="activity", name="Paragliding Tour",
                           description="Experience breathtaking views while paragliding", rating=4.8, price_level=4,
                           rationale="Matches adventure travel style and high-adrenaline preference"),
            Recommendation(id="rec_002", type="activity", name="Rock Climbing",
                           description="Professional guided rock climbing experience", rating=4.7, price_level=3,
                           rationale="Budget-friendly adventure activity"),
            Recommendation(id="rec_003", type="restaurant", name="Mountain View Bistro",
                           description="Local cuisine with panoramic views", rating=4.4, price_level=3,
                           rationale="Outdoor seating aligns with adventure preference"),
        ],
        "luxury": [
            Recommendation(id="rec_101", type="restaurant", name="The Golden Plate",
                           description="5-star Michelin dining experience", rating=4.9, price_level=5,
                           rationale="Premium fine dining for luxury traveler"),
            Recommendation(id="rec_102", type="activity", name="Private Yacht Cruise",
                           description="Exclusive sunset cruise with champagne service", rating=4.8, price_level=5,
                           rationale="Ultra-premium experience matching luxury profile"),
            Recommendation(id="rec_103", type="accommodation", name="Royal Palace Resort",
                           description="5-star beachfront luxury resort", rating=4.9, price_level=5,
                           rationale="Flagship luxury accommodation"),
        ],
        "balanced": [
            Recommendation(id="rec_201", type="attraction", name="Historical Museum",
                           description="Explore rich cultural heritage", rating=4.5, price_level=2,
                           rationale="Popular mid-range cultural attraction"),
            Recommendation(id="rec_202", type="restaurant", name="Local Food Market",
                           description="Authentic street food and local cuisine", rating=4.3, price_level=1,
                           rationale="Budget-friendly culinary exploration"),
            Recommendation(id="rec_203", type="activity", name="Guided City Tour",
                           description="Comprehensive tour of major attractions", rating=4.4, price_level=2,
                           rationale="Well-balanced sightseeing experience"),
        ],
    }
    return recommendations_map.get(travel_style, recommendations_map["balanced"])


def _personalize_recommendations(
    recs: List[Recommendation],
    destination: str,
    similar_prefs: List[dict],
    interests: List[str],
) -> List[Recommendation]:
    """Boost recommendations based on Pinecone similarity and user interests."""
    if not similar_prefs and not interests:
        return recs
    boosted = []
    liked_types = set()
    for pref in similar_prefs:
        for style in pref.get("travel_style", []) or []:
            liked_types.add(style)
        for interest in pref.get("interests", []) or []:
            liked_types.add(interest)
    for interest in interests:
        liked_types.add(interest)

    for rec in recs:
        score_boost = 0.0
        if rec.type in liked_types:
            score_boost += 0.1
        if any(i in (rec.description or "").lower() for i in interests):
            score_boost += 0.05
        boosted.append(rec.model_copy(update={
            "rationale": rec.rationale + (f" | Personalized for {destination}" if score_boost else ""),
        }))
    return boosted


async def run_recommendation_engine(
    destination: str,
    travel_style: str = "balanced",
    budget_tier: str = "mid-range",
    interests: List[str] = None,
    user_id: int = 1,
    preferences: Optional[dict] = None,
) -> RecommendationResult:
    """Generate personalized recommendations using Pinecone embeddings and style matching."""

    if interests is None:
        interests = ["sightseeing", "food", "culture"]

    async def _fetch():
        if preferences:
            await upsert_preference(user_id, preferences)
        similar = await query_similar_preferences(destination, travel_style)
        recs = _base_recommendations(travel_style)
        recs = _personalize_recommendations(recs, destination, similar, interests)

        # Destination-specific naming
        personalized = []
        for rec in recs:
            personalized.append(rec.model_copy(update={
                "name": rec.name if destination.lower() in rec.name.lower() else f"{rec.name} — {destination}",
            }))

        score = 0.75 + (0.1 * min(len(similar), 2))
        if preferences:
            score += 0.05
        return RecommendationResult(
            destination=destination,
            travel_style=travel_style,
            recommendations=personalized,
            personalization_score=min(score, 0.99),
        )

    payload = await cached_json(
        "recommendation",
        (destination.lower(), travel_style, budget_tier, ",".join(sorted(interests))),
        ttl=1800,
        fetcher=_fetch,
    )
    return RecommendationResult(**payload)
