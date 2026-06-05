from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class OrchestratorInput(BaseModel):
    trip_id: int
    destination: str
    start_date: str
    end_date: str
    total_budget: float
    travel_style: str = "balanced"
    travelers: int = 1


class MergedTripPlan(BaseModel):
    trip_id: int
    destination: str
    itinerary: Dict[str, Any] = Field(default_factory=dict)
    budget_breakdown: Dict[str, Any] = Field(default_factory=dict)
    flights: List[Dict[str, Any]] = Field(default_factory=list)
    hotels: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    explanations: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
