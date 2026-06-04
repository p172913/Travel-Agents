from pydantic import BaseModel, Field
from typing import List

class BudgetAllocation(BaseModel):
    flights: float = Field(..., description="Estimated cost allocated to flight travel")
    accommodation: float = Field(..., description="Estimated cost allocated to hotels, resorts, or home rentals")
    food: float = Field(..., description="Estimated cost allocated to meals, dining, and drinking")
    activities: float = Field(..., description="Estimated cost allocated to tickets, tours, sightseeing, and activities")
    misc: float = Field(..., description="Estimated cost allocated to local travel, emergency funds, shopping, and tips")

class BudgetAnalysis(BaseModel):
    total_budget: float = Field(..., description="Total trip budget limit provided by the traveler")
    currency: str = Field("INR", description="The standard 3-letter currency code (e.g. INR, USD, EUR)")
    allocation: BudgetAllocation = Field(..., description="Detailed breakdown of budget across travel expense categories")
    cost_prediction_summary: str = Field(..., description="An AI description of budget feasibility, expected price levels, and tips")
    alerts: List[str] = Field(default_factory=list, description="A list of warnings or recommendations regarding budget constraints")
