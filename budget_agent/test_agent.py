import sys
import os
import pytest

# Add workspace root directory to python path to resolve modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budget_agent.schemas import BudgetAnalysis, BudgetAllocation
from budget_agent.agent import generate_mock_budget, run_budget_analysis

def test_budget_schemas():
    """Verify that BudgetAllocation and BudgetAnalysis schemas can be instantiated and validated."""
    alloc = BudgetAllocation(
        flights=15000.0,
        accommodation=15000.0,
        food=10000.0,
        activities=5000.0,
        misc=5000.0
    )
    analysis = BudgetAnalysis(
        total_budget=50000.0,
        currency="INR",
        allocation=alloc,
        cost_prediction_summary="Manageable",
        alerts=[]
    )
    assert analysis.total_budget == 50000.0
    assert analysis.allocation.flights == 15000.0

def test_mock_budget_math_and_sum():
    """Verify that allocations sum up exactly to the total budget across multiple budgets."""
    budgets = [10000.0, 50000.0, 123456.78, 500000.0]
    styles = ["economy", "mid-range", "luxury"]
    
    for budget in budgets:
        for style in styles:
            res = generate_mock_budget("Goa", budget, 5, style)
            alloc = res.allocation
            total_calc = alloc.flights + alloc.accommodation + alloc.food + alloc.activities + alloc.misc
            assert abs(res.total_budget - total_calc) < 0.01

def test_mock_budget_travel_styles():
    """Verify that mock allocations shift correctly based on travel styles."""
    budget = 100000.0
    
    econ_res = generate_mock_budget("Goa", budget, 7, "economy")
    luxury_res = generate_mock_budget("Goa", budget, 7, "luxury")
    
    # Accommodation should be higher in luxury
    assert luxury_res.allocation.accommodation > econ_res.allocation.accommodation
    
    # Flights ratio should be higher or equal in economy
    assert econ_res.allocation.flights > luxury_res.allocation.flights

@pytest.mark.asyncio
async def test_run_budget_analysis_async():
    """Verify that the async interface resolves cleanly to the Pydantic schema."""
    result = await run_budget_analysis("Tokyo", 150000.0, 10, "mid-range")
    assert isinstance(result, BudgetAnalysis)
    assert result.total_budget == 150000.0
    
    # Confirm math is correct in async run
    alloc = result.allocation
    total_calc = alloc.flights + alloc.accommodation + alloc.food + alloc.activities + alloc.misc
    assert abs(total_calc - 150000.0) < 0.01
