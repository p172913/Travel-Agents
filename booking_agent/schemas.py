from pydantic import BaseModel, Field
from typing import List, Optional


class Flight(BaseModel):
    provider: str
    flight_number: str
    depart_time: str
    arrive_time: str
    duration_minutes: int
    price: float
    currency: str


class Hotel(BaseModel):
    provider: str
    hotel_name: str
    check_in: str
    check_out: str
    nightly_rate: float
    total_price: float
    rating: Optional[float] = None


class BookingResult(BaseModel):
    destination: str
    start_date: str
    end_date: str
    best_flights: List[Flight] = Field(default_factory=list)
    best_hotels: List[Hotel] = Field(default_factory=list)
