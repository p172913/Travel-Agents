import sys
import os
import datetime
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add the workspace root directory to python path to resolve shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import init_db, get_db
from shared.models import User, Trip, TripRequest, AgentLog, TripPlan
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

# Enable CORS for Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
            output_data=research_result.dict()
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
                budget_breakdown=budget_result.allocation.dict(),
                explanation=budget_result.cost_prediction_summary
            )
            db.add(plan)
        else:
            plan.budget_breakdown = budget_result.allocation.dict()
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
            output_data=budget_result.dict()
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
            output_data=booking_result.dict()
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
            output_data=recommendation_result.dict()
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
            explanation=str(orchestrated_plan.explanations)
        )
        db.add(trip_plan)
        
        # Log orchestration success
        agent_log = AgentLog(
            trip_id=trip.id,
            agent_name="orchestrator",
            action="complete-orchestration",
            message=f"Successfully orchestrated complete trip plan in {orchestrated_plan.execution_time_ms:.0f}ms",
            input_data=orchestrator_input.dict(),
            output_data=orchestrated_plan.dict()
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


def parse_date(date_str: str):
    """Parse YYYY-MM-DD string into date object."""
    from datetime import datetime
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        import datetime as dt
        return dt.date.today()


