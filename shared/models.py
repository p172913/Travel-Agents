import datetime
import uuid
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Date,
    ForeignKey,
    JSON,
    create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable if third party auth
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    budget_tier = Column(String(50), default="mid-range")  # economy, mid-range, luxury
    dietary_preferences = Column(JSON, default=list)        # list of strings
    travel_style = Column(JSON, default=list)               # solo, family, adventure, etc.
    interests = Column(JSON, default=list)                  # sightseeing, adventure, nature, food, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_limit = Column(Float, nullable=False)
    status = Column(String(50), default="planning")  # planning, draft, confirmed, past
    share_token = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="trips")
    requests = relationship("TripRequest", back_populates="trip", cascade="all, delete-orphan")
    plans = relationship("TripPlan", back_populates="trip", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="trip", cascade="all, delete-orphan")


class TripRequest(Base):
    __tablename__ = "trip_requests"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="processing")  # processing, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="requests")


class TripPlan(Base):
    __tablename__ = "trip_plans"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    itinerary = Column(JSON, nullable=False)  # Day-by-day structure
    budget_breakdown = Column(JSON, nullable=False)  # Allocated costs for flight, hotel, food, etc.
    explanation = Column(Text, nullable=True)  # AI explanation for recommendations
    recommendations = Column(JSON, nullable=True, default=list)  # Saved recommendation items
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="plans")
    bookings = relationship("Booking", back_populates="trip_plan", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="trip_plan", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    trip_plan_id = Column(Integer, ForeignKey("trip_plans.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # flight, hotel, activity
    details = Column(JSON, nullable=False)  # booking-specific properties
    price = Column(Float, nullable=False)
    booking_reference = Column(String(100), nullable=True)
    status = Column(String(50), default="searched")  # searched, reserved, booked
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip_plan = relationship("TripPlan", back_populates="bookings")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    agent_name = Column(String(100), nullable=False)  # research-agent, budget-agent, etc.
    action = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="agent_logs")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    trip_plan_id = Column(Integer, ForeignKey("trip_plans.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String(50), nullable=False)  # hotel, activity, restaurant
    item_id = Column(String(100), nullable=False)   # Reference to item id in JSON itinerary
    rating = Column(Integer, nullable=False)       # 1 for thumbs up, -1 for thumbs down
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    trip_plan = relationship("TripPlan", back_populates="feedbacks")
