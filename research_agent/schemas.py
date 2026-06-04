from pydantic import BaseModel, Field
from typing import List

class PlaceDetail(BaseModel):
    name: str = Field(..., description="Name of the place, attraction, or restaurant")
    description: str = Field(..., description="Short explanation of why it is interesting or recommended")
    location: str = Field(..., description="Address, area, or general geographic location of the attraction")
    rating: float = Field(..., description="A rating out of 5.0")

class DestinationResearch(BaseModel):
    destination: str = Field(..., description="Name of the researched destination city or country")
    weather: str = Field(..., description="A summary of the weather (e.g. current conditions, temperature, seasonality)")
    safety_score: int = Field(..., description="An integer rating of safety from 1 (dangerous) to 10 (extremely safe)")
    top_places: List[PlaceDetail] = Field(..., description="A list of the top popular attractions or landmarks in the destination")
    hidden_gems: List[PlaceDetail] = Field(..., description="A list of lesser-known local secrets, off-the-beaten-path recommendations")
