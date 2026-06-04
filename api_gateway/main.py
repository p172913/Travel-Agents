import sys
import os
import datetime
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

# Load environment variables from .env in local and production dev mode
load_dotenv()

# Add the workspace root directory to python path to resolve shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_gateway.config import settings
from shared.db import init_db, get_db
from shared.models import User, Trip, TripRequest, AgentLog, TripPlan, Booking
from research_agent.agent import run_research
from budget_agent.agent import run_budget_analysis
from booking_agent.agent import run_booking_search
from recommendation_agent.agent import run_recommendation_engine
from orchestrator.agent import orchestrate_trip_plan
from orchestrator.schemas import OrchestratorInput
from pydantic import BaseModel

class BudgetRequest(BaseModel):
    trip_id: int
    total_budget: float
    travel_style: str = "mid-range"


class BookingRequest(BaseModel):
    trip_id: int
    start_date: str
    end_date: str
    travelers: int = 1


class RecommendationRequest(BaseModel):
    trip_id: int
    travel_style: str = "balanced"
    budget_tier: str = "mid-range"
    interests: list = None


class OrchestratorTripRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    total_budget: float
    travel_style: str = "balanced"
    travelers: int = 1

app = FastAPI(
    title="TravelSouls API Gateway",
    description="Gateway API routing frontend requests to multi-agent travel planner backend services.",
    version="1.0.0"
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("travelsouls")
logger.info("Starting TravelSouls API Gateway in %s mode", settings.app_env)

if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, traces_sample_rate=0.1)
        app.add_middleware(SentryAsgiMiddleware)
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry-sdk is not installed. Skipping Sentry initialization.")

from urllib.parse import urlparse

# Enable CORS for frontend development and production host origins.
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
allow_origin_regex = None
frontend_origin = os.getenv("FRONTEND_URL")
if frontend_origin:
    for origin_text in frontend_origin.split(","):
        origin = origin_text.strip()
        if not origin:
            continue
        parsed_origin = urlparse(origin)
        if parsed_origin.scheme and parsed_origin.netloc:
            allowed_origins.append(f"{parsed_origin.scheme}://{parsed_origin.netloc}")
        else:
            allowed_origins.append(origin.rstrip("/"))
else:
    if settings.app_env.lower() == "production":
        allow_origin_regex = r"https?://.*"
        logger.warning("FRONTEND_URL not configured in production; CORS will allow HTTPS origins by regex.")

logger.info("Allowing CORS origins: %s", allowed_origins)
if allow_origin_regex:
    logger.info("Allowing CORS origin regex: %s", allow_origin_regex)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_default_user_if_not_exists(db: Session):
    """Utility to seed a default traveler profile to resolve FK dependencies in local MVP mode."""
    default_user = db.query(User).filter_by(email="default@travelsouls.com").first()
    if not default_user:
        default_user = User(
            email="default@travelsouls.com",
            full_name="Default Traveler"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    return default_user

@app.on_event("startup")
def on_startup():
    # Initialize the database and create tables
    init_db()
    # Seed default user
    db = next(get_db())
    create_default_user_if_not_exists(db)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Quick query validation to verify database connection works
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "database": db_status
    }

@app.get("/api/research")
async def get_research(
    destination: str = Query(..., description="The travel destination to research"),
    month: str = Query(None, description="The month of travel"),
    db: Session = Depends(get_db)
):
    """Exposes destination research capabilities. Saves queries and responses into 
    local audit logs inside PostgreSQL / SQLite.
    """
    if not destination.strip():
        raise HTTPException(status_code=400, detail="Destination cannot be blank")

    # Get seed user
    user = create_default_user_if_not_exists(db)

    # 1. Start a temporary Trip tracking record in our db schema
    # Defaulting start/end dates to next month if none is provided
    today = datetime.date.today()
    start_date = datetime.date(today.year, today.month + 1, 1) if today.month < 12 else datetime.date(today.year + 1, 1, 1)
    end_date = start_date + datetime.timedelta(days=7)

    trip = Trip(
        user_id=user.id,
        title=f"Trip to {destination}",
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        budget_limit=50000.0,  # Default budget
        status="planning"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Log initial prompt request
    trip_request = TripRequest(
        trip_id=trip.id,
        prompt=f"Research Goa in {month}" if month else f"Research {destination}",
        status="processing"
    )
    db.add(trip_request)
    db.commit()

    # 2. Execute Research agent
    try:
        research_result = await run_research(destination, month)
        
        # Log successful completion in database AgentLog table
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="research-agent",
            action="destination-research",
            message=f"Successfully researched {destination} for month {month}",
            input_data={"destination": destination, "month": month},
            output_data=research_result.model_dump()
        )
        db.add(agent_log)
        
        # Update trip request status
        trip_request.status = "completed"
        db.commit()

        return {
            "trip_id": trip.id,
            "research": research_result
        }

    except Exception as e:
        # Log failure in database AgentLog table
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="research-agent",
            action="destination-research",
            message=f"Failed to research {destination}: {str(e)}",
            input_data={"destination": destination, "month": month},
            output_data=None
        )
        db.add(agent_log)
        trip_request.status = "failed"
        db.commit()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Agent research execution failed: {str(e)}"
        )

@app.post("/api/budget")
async def analyze_budget(
    request: BudgetRequest,
    db: Session = Depends(get_db)
):
    """Exposes budget analysis and allocation capability for a specific trip."""
    trip = db.query(Trip).filter_by(id=request.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {request.trip_id} not found")

    # Calculate duration
    duration = (trip.end_date - trip.start_date).days
    if duration <= 0:
        duration = 1

    try:
        # Run the budget agent
        budget_result = await run_budget_analysis(
            destination=trip.destination,
            total_budget=request.total_budget,
            duration_days=duration,
            travel_style=request.travel_style
        )

        # Update trip budget limit
        trip.budget_limit = request.total_budget
        db.commit()

        # Update or create a draft TripPlan storing this budget breakdown
        plan = db.query(TripPlan).filter_by(trip_id=trip.id).first()
        if not plan:
            plan = TripPlan(
                trip_id=trip.id,
                itinerary={"days": []},
                budget_breakdown=budget_result.allocation.model_dump(),
                explanation=budget_result.cost_prediction_summary
            )
            db.add(plan)
        else:
            plan.budget_breakdown = budget_result.allocation.model_dump()
            plan.explanation = budget_result.cost_prediction_summary
        
        # Log successful agent execution
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="budget-agent",
            action="budget-allocation",
            message=f"Successfully allocated budget of {request.total_budget} {budget_result.currency}",
            input_data={
                "trip_id": request.trip_id,
                "total_budget": request.total_budget,
                "travel_style": request.travel_style
            },
            output_data=budget_result.model_dump()
        )
        db.add(agent_log)
        db.commit()
        db.refresh(plan)

        return {
            "trip_id": trip.id,
            "plan_id": plan.id,
            "budget_analysis": budget_result
        }

    except Exception as e:
        # Log failure
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="budget-agent",
            action="budget-allocation",
            message=f"Failed to allocate budget: {str(e)}",
            input_data={
                "trip_id": request.trip_id,
                "total_budget": request.total_budget,
                "travel_style": request.travel_style
            },
            output_data=None
        )
        db.add(agent_log)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Budget agent execution failed: {str(e)}"
        )


@app.post("/api/booking")
async def search_booking(
    request: BookingRequest,
    db: Session = Depends(get_db)
):
    """Search for flights and hotels for a trip. Prototype uses mocked booking agent."""
    trip = db.query(Trip).filter_by(id=request.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {request.trip_id} not found")

    try:
        booking_result = await run_booking_search(
            destination=trip.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            travelers=request.travelers
        )

        # Log agent output
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="booking-agent",
            action="search-bookings",
            message=f"Performed booking search for trip {trip.id}",
            input_data={
                "trip_id": request.trip_id,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "travelers": request.travelers
            },
            output_data=booking_result.model_dump()
        )
        db.add(agent_log)
        db.commit()

        return {
            "trip_id": trip.id,
            "booking": booking_result
        }

    except Exception as e:
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="booking-agent",
            action="search-bookings",
            message=f"Booking search failed: {str(e)}",
            input_data={
                "trip_id": request.trip_id,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "travelers": request.travelers
            },
            output_data=None
        )
        db.add(agent_log)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Booking agent execution failed: {str(e)}")


@app.post("/api/recommendation")
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get personalized recommendations for a trip."""
    trip = db.query(Trip).filter_by(id=request.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {request.trip_id} not found")

    try:
        recommendation_result = await run_recommendation_engine(
            destination=trip.destination,
            travel_style=request.travel_style,
            budget_tier=request.budget_tier,
            interests=request.interests
        )

        # Log agent output
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="recommendation-agent",
            action="generate-recommendations",
            message=f"Generated {len(recommendation_result.recommendations)} personalized recommendations",
            input_data={
                "trip_id": request.trip_id,
                "travel_style": request.travel_style,
                "budget_tier": request.budget_tier,
                "interests": request.interests
            },
            output_data=recommendation_result.model_dump()
        )
        db.add(agent_log)
        db.commit()

        return {
            "trip_id": trip.id,
            "recommendations": recommendation_result
        }

    except Exception as e:
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="recommendation-agent",
            action="generate-recommendations",
            message=f"Recommendation generation failed: {str(e)}",
            input_data={
                "trip_id": request.trip_id,
                "travel_style": request.travel_style,
                "budget_tier": request.budget_tier,
                "interests": request.interests
            },
            output_data=None
        )
        db.add(agent_log)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Recommendation agent execution failed: {str(e)}")


@app.post("/api/plan/orchestrate")
async def orchestrate_complete_plan(
    request: OrchestratorTripRequest,
    db: Session = Depends(get_db)
):
    """Generate a complete trip plan by orchestrating all agents (research, budget, booking, recommendation).
    
    This endpoint is the primary entry point for trip planning. It coordinates all agents to produce
    a complete, multi-faceted travel plan with budget, flights, hotels, activities, and explanations.
    """
    user = create_default_user_if_not_exists(db)
    
    # Create trip record
    trip = Trip(
        user_id=user.id,
        title=f"Trip to {request.destination}",
        destination=request.destination,
        start_date=parse_date(request.start_date),
        end_date=parse_date(request.end_date),
        budget_limit=request.total_budget,
        status="planning"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    try:
        # Log orchestration request
        trip_request = TripRequest(
            trip_id=trip.id,
            prompt=f"Plan a {request.travel_style} trip to {request.destination}",
            status="processing"
        )
        db.add(trip_request)
        db.commit()
        
        # Run orchestrator
        orchestrator_input = OrchestratorInput(
            trip_id=trip.id,
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            total_budget=request.total_budget,
            travel_style=request.travel_style,
            travelers=request.travelers
        )
        
        orchestrated_plan = await orchestrate_trip_plan(orchestrator_input)
        
        # Store the complete plan
        trip_plan = TripPlan(
            trip_id=trip.id,
            itinerary=orchestrated_plan.itinerary,
            budget_breakdown=orchestrated_plan.budget_breakdown,
            explanation=" | ".join([f"{k}: {v}" for k, v in orchestrated_plan.explanations.items()]),
            recommendations=orchestrated_plan.recommendations
        )
        db.add(trip_plan)
        db.commit()
        db.refresh(trip_plan)

        # Persist booking results into the plan booking table
        for flight in orchestrated_plan.flights:
            booking = Booking(
                trip_plan_id=trip_plan.id,
                type="flight",
                details=flight,
                price=flight.get("price", 0.0),
                booking_reference=None,
                status="searched"
            )
            db.add(booking)

        for hotel in orchestrated_plan.hotels:
            total_price = hotel.get("total_price") if hotel.get("total_price") is not None else hotel.get("nightly_rate", 0.0)
            booking = Booking(
                trip_plan_id=trip_plan.id,
                type="hotel",
                details=hotel,
                price=total_price,
                booking_reference=None,
                status="searched"
            )
            db.add(booking)

        # Log orchestration success
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="orchestrator",
            action="complete-orchestration",
            message=f"Successfully orchestrated complete trip plan in {orchestrated_plan.execution_time_ms:.0f}ms",
            input_data=orchestrator_input.model_dump(),
            output_data=orchestrated_plan.model_dump()
        )
        db.add(agent_log)
        
        trip_request.status = "completed"
        db.commit()
        db.refresh(trip_plan)
        
        return {
            "trip_id": trip.id,
            "plan_id": trip_plan.id,
            "plan": orchestrated_plan
        }
        
    except Exception as e:
        # Log failure
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="orchestrator",
            action="complete-orchestration",
            message=f"Orchestration failed: {str(e)}",
            input_data=orchestrator_input.dict() if 'orchestrator_input' in locals() else {},
            output_data=None
        )
        db.add(agent_log)
        trip_request.status = "failed"
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Trip orchestration failed: {str(e)}"
        )


@app.get("/api/trips")
def list_trips(db: Session = Depends(get_db)):
    """Return a list of trips with summary metadata."""
    trips = db.query(Trip).order_by(Trip.created_at.desc()).all()
    return [
        {
            "trip_id": trip.id,
            "title": trip.title,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "budget_limit": trip.budget_limit,
            "status": trip.status,
            "plan_count": len(trip.plans),
            "created_at": trip.created_at.isoformat()
        }
        for trip in trips
    ]


@app.get("/api/trips/{trip_id}")
def get_trip_details(trip_id: int, db: Session = Depends(get_db)):
    """Return trip details including saved trip plans and booking context."""
    trip = db.query(Trip).filter_by(id=trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")

    return {
        "trip_id": trip.id,
        "title": trip.title,
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "budget_limit": trip.budget_limit,
        "status": trip.status,
        "plans": [
            {
                "plan_id": plan.id,
                "itinerary": plan.itinerary,
                "budget_breakdown": plan.budget_breakdown,
                "explanation": plan.explanation,
                "recommendations": plan.recommendations or [],
                "created_at": plan.created_at.isoformat(),
                "bookings": [
                    {
                        "booking_id": booking.id,
                        "type": booking.type,
                        "details": booking.details,
                        "price": booking.price,
                        "booking_reference": booking.booking_reference,
                        "status": booking.status,
                        "created_at": booking.created_at.isoformat()
                    }
                    for booking in plan.bookings
                ]
            }
            for plan in trip.plans
        ],
        "requests": [
            {
                "request_id": request.id,
                "prompt": request.prompt,
                "status": request.status,
                "created_at": request.created_at.isoformat()
            }
            for request in trip.requests
        ]
    }


def parse_date(date_str: str):
    """Parse YYYY-MM-DD string into date object."""
    from datetime import datetime
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        import datetime as dt
        return dt.date.today()


