from typing import List
from .schemas import RecommendationResult, Recommendation


async def run_recommendation_engine(
    destination: str,
    travel_style: str = "balanced",
    budget_tier: str = "mid-range",
    interests: List[str] = None
) -> RecommendationResult:
    """Generate personalized recommendations based on user profile and trip context.
    
    Prototype uses hardcoded recommendations tailored by travel_style.
    In production, this would query Pinecone embeddings and LLM re-rank.
    """
    if interests is None:
        interests = ["sightseeing", "food", "culture"]
    
    # Mock personalized recommendations by travel style
    recommendations_map = {
        "adventure": [
            Recommendation(
                id="rec_001",
                type="activity",
                name="Paragliding Tour",
                description="Experience breathtaking views while paragliding",
                rating=4.8,
                price_level=4,
                rationale="Matches adventure travel style and high-adrenaline preference"
            ),
            Recommendation(
                id="rec_002",
                type="activity",
                name="Rock Climbing",
                description="Professional guided rock climbing experience",
                rating=4.7,
                price_level=3,
                rationale="Budget-friendly adventure activity"
            ),
            Recommendation(
                id="rec_003",
                type="restaurant",
                name="Mountain View Bistro",
                description="Local cuisine with panoramic views",
                rating=4.4,
                price_level=3,
                rationale="Outdoor seating aligns with adventure preference"
            )
        ],
        "luxury": [
            Recommendation(
                id="rec_101",
                type="restaurant",
                name="The Golden Plate",
                description="5-star Michelin dining experience",
                rating=4.9,
                price_level=5,
                rationale="Premium fine dining for luxury traveler"
            ),
            Recommendation(
                id="rec_102",
                type="activity",
                name="Private Yacht Cruise",
                description="Exclusive sunset cruise with champagne service",
                rating=4.8,
                price_level=5,
                rationale="Ultra-premium experience matching luxury profile"
            ),
            Recommendation(
                id="rec_103",
                type="accommodation",
                name="Royal Palace Resort",
                description="5-star beachfront luxury resort",
                rating=4.9,
                price_level=5,
                rationale="Flagship luxury accommodation"
            )
        ],
        "balanced": [
            Recommendation(
                id="rec_201",
                type="attraction",
                name="Historical Museum",
                description="Explore rich cultural heritage",
                rating=4.5,
                price_level=2,
                rationale="Popular mid-range cultural attraction"
            ),
            Recommendation(
                id="rec_202",
                type="restaurant",
                name="Local Food Market",
                description="Authentic street food and local cuisine",
                rating=4.3,
                price_level=1,
                rationale="Budget-friendly culinary exploration"
            ),
            Recommendation(
                id="rec_203",
                type="activity",
                name="Guided City Tour",
                description="Comprehensive tour of major attractions",
                rating=4.4,
                price_level=2,
                rationale="Well-balanced sightseeing experience"
            )
        ]
    }
    
    # Default to balanced if style not recognized
    recs = recommendations_map.get(travel_style, recommendations_map["balanced"])
    
    return RecommendationResult(
        destination=destination,
        travel_style=travel_style,
        recommendations=recs,
        personalization_score=0.85  # Placeholder confidence score
    )
