import os
import sys
from typing import List, Optional
from pydantic_ai import Agent, RunContext

# Add workspace directory to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budget_agent.schemas import BudgetAnalysis, BudgetAllocation

# Resolve model dynamically to prevent credentials errors on import
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if openai_key:
    model_name = "openai:gpt-4o-mini"
elif gemini_key:
    model_name = "gemini:gemini-1.5-flash"
else:
    from pydantic_ai.models.test import TestModel
    model_name = TestModel()

agent = Agent(
    model_name,
    output_type=BudgetAnalysis,
    system_prompt=(
        "You are an expert travel budget and financial analysis agent. "
        "Your task is to review the requested trip details (destination, total budget, duration, "
        "and travel style) and allocate the budget across Flights, Accommodation, Food, "
        "Activities, and Miscellaneous expenses. "
        "Ensure all allocations sum up exactly to the total budget. "
        "Assess if the budget is realistic for the destination and duration, "
        "and generate helpful alerts or cost saving tips."
    )
)

@agent.tool
async def estimate_average_costs(
    ctx: RunContext[None], 
    destination: str, 
    travel_style: str
) -> str:
    """Gets typical daily cost estimates for a destination depending on travel style.
    
    Args:
        destination: City or country.
        travel_style: 'economy', 'mid-range', or 'luxury'.
    """
    dest_lower = destination.lower()
    style_lower = travel_style.lower()
    
    # Generic index data in INR (per day)
    indices = {
        "goa": {"economy": 2500, "mid-range": 5000, "luxury": 15000},
        "tokyo": {"economy": 8000, "mid-range": 18000, "luxury": 45000},
        "paris": {"economy": 9000, "mid-range": 20000, "luxury": 50000}
    }
    
    selected_dest = "goa"
    for known in indices:
        if known in dest_lower:
            selected_dest = known
            break
            
    daily_cost = indices[selected_dest].get(style_lower, indices[selected_dest]["mid-range"])
    return f"Typical daily cost for {destination} in {travel_style} tier is approximately {daily_cost} INR per day (excluding long-distance flights)."


def generate_mock_budget(
    destination: str,
    total_budget: float,
    duration_days: int,
    travel_style: str = "mid-range"
) -> BudgetAnalysis:
    """Generates realistic mock budget allocations based on trip characteristics.
    Used when API credentials for LLMs are not set.
    """
    style_lower = travel_style.lower()
    dest_lower = destination.lower()
    
    # Define budget allocation ratios based on travel styles
    # Must sum up to 1.0 (100%)
    if style_lower == "economy" or style_lower == "budget":
        pct_flights = 0.35
        pct_hotel = 0.25
        pct_food = 0.15
        pct_activities = 0.10
        pct_misc = 0.15
    elif style_lower == "luxury":
        pct_flights = 0.20
        pct_hotel = 0.45
        pct_food = 0.20
        pct_activities = 0.10
        pct_misc = 0.05
    else:  # mid-range
        pct_flights = 0.30
        pct_hotel = 0.30
        pct_food = 0.15
        pct_activities = 0.15
        pct_misc = 0.10

    # Ensure floats represent exact sums
    flights_val = round(total_budget * pct_flights, 2)
    hotel_val = round(total_budget * pct_hotel, 2)
    food_val = round(total_budget * pct_food, 2)
    activities_val = round(total_budget * pct_activities, 2)
    
    # Force misc to absorb rounding errors so the total is exactly correct
    misc_val = round(total_budget - (flights_val + hotel_val + food_val + activities_val), 2)
    
    allocation = BudgetAllocation(
        flights=flights_val,
        accommodation=hotel_val,
        food=food_val,
        activities=activities_val,
        misc=misc_val
    )
    
    # Calculate daily spending allowance (excluding flights)
    daily_spendable = (hotel_val + food_val + activities_val + misc_val) / duration_days
    
    # Analyze feasibility and write summary
    is_expensive = any(exp in dest_lower for exp in ["tokyo", "paris", "london", "new york", "switzerland"])
    
    alerts = []
    
    if daily_spendable < 1500:
        summary = (
            f"The budget of {total_budget} INR for a {duration_days}-day trip to {destination} is extremely tight. "
            f"After flights, you have about {daily_spendable:.0f} INR per day for lodging, food, and sightseeing, "
            f"which will require using local transport and staying in hostels."
        )
        alerts.append("Warning: Daily budget is low. Hostels and street food are highly recommended to avoid deficits.")
    elif is_expensive and (style_lower != "luxury" and total_budget < 120000):
        summary = (
            f"A budget of {total_budget} INR for {destination} is manageable, but you are visiting a premium "
            f"destination. You will need to carefully track your accommodation and activity bookings."
        )
        alerts.append("Caution: Premium destination alert. Flight and accommodation prices fluctuate rapidly; book early.")
    else:
        summary = (
            f"Your budget of {total_budget} INR is well-suited for a {duration_days}-day {travel_style} trip to {destination}. "
            f"The distribution allows for comfortable mid-tier accommodations, enjoyable dining, and essential sightseeing."
        )
        
    if "goa" in dest_lower and "july" in summary.lower():
        alerts.append("Tip: Off-season travel. Monsoons in Goa in July mean hotel and activity rates can be discounted by 30-50%.")
        
    return BudgetAnalysis(
        total_budget=total_budget,
        currency="INR",
        allocation=allocation,
        cost_prediction_summary=summary,
        alerts=alerts
    )


async def run_budget_analysis(
    destination: str,
    total_budget: float,
    duration_days: int,
    travel_style: str = "mid-range"
) -> BudgetAnalysis:
    """Runs the budget allocation agent. If API credentials are not set, 
    falls back to generating high-fidelity mock allocations.
    """
    # Safeguard duration
    if duration_days <= 0:
        duration_days = 1
        
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not openai_key and not gemini_key:
        return generate_mock_budget(destination, total_budget, duration_days, travel_style)
        
    try:
        prompt = (
            f"Allocate a total budget of {total_budget} INR for a {duration_days}-day trip to {destination}. "
            f"The traveler style is: {travel_style}."
        )
        result = await agent.run(prompt)
        
        # Verify result math sums up exactly to total_budget (adjust misc for rounding differences)
        alloc = result.data.allocation
        total_calc = alloc.flights + alloc.accommodation + alloc.food + alloc.activities + alloc.misc
        diff = total_budget - total_calc
        if abs(diff) > 0.01:
            alloc.misc = round(alloc.misc + diff, 2)
            
        return result.data
    except Exception as e:
        print(f"Error running Budget Agent: {str(e)}. Falling back to mock budget.", file=sys.stderr)
        return generate_mock_budget(destination, total_budget, duration_days, travel_style)
