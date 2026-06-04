import sys
import os
import pytest

# Add workspace root directory to python path to resolve modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent.schemas import DestinationResearch, PlaceDetail
from research_agent.agent import generate_mock_research, run_research

def test_place_detail_schema():
    """Verify PlaceDetail model can be instantiated and validated."""
    place = PlaceDetail(
        name="Anjuna Beach",
        description="Famous for flea markets",
        location="Anjuna, Goa",
        rating=4.4
    )
    assert place.name == "Anjuna Beach"
    assert place.rating == 4.4

def test_destination_research_schema():
    """Verify DestinationResearch model can be instantiated and validated."""
    research = DestinationResearch(
        destination="Test City",
        weather="Sunny, 25C",
        safety_score=9,
        top_places=[],
        hidden_gems=[]
    )
    assert research.destination == "Test City"
    assert research.safety_score == 9

def test_generate_mock_research_goa():
    """Verify mock generator output for Goa matches schema specifications."""
    goa_mock = generate_mock_research("Goa", "July")
    assert isinstance(goa_mock, DestinationResearch)
    assert goa_mock.destination == "Goa"
    assert len(goa_mock.top_places) > 0
    assert len(goa_mock.hidden_gems) > 0
    
    # Check that individual places have valid structure
    place = goa_mock.top_places[0]
    assert isinstance(place, PlaceDetail)
    assert place.name != ""
    assert place.rating >= 0.0 and place.rating <= 5.0

def test_generate_mock_research_generic():
    """Verify mock generator fallback for arbitrary cities."""
    generic_mock = generate_mock_research("Anytown")
    assert isinstance(generic_mock, DestinationResearch)
    assert generic_mock.destination == "Anytown"
    assert len(generic_mock.top_places) > 0
    assert len(generic_mock.hidden_gems) > 0

@pytest.mark.asyncio
async def test_run_research_execution():
    """Verify async agent execution successfully resolves to schemas."""
    # Runs the fallback system if API keys are missing, which still resolves to schema
    result = await run_research("Tokyo", "July")
    assert isinstance(result, DestinationResearch)
    assert result.destination == "Tokyo"
    assert len(result.top_places) > 0
