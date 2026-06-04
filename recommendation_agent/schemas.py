from pydantic import BaseModel, Field
from typing import List, Optional


class Recommendation(BaseModel):
    id: str
    type: str  # restaurant, activity, attraction, etc.
    name: str
    description: Optional[str] = None
    rating: float
    price_level: Optional[int] = None  # 1-5
    rationale: str  # Why AI recommended this


class RecommendationResult(BaseModel):
    destination: str
    travel_style: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    personalization_score: float = 0.0
