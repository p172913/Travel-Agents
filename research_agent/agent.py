import os
import sys
import httpx
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

# Add workspace directory to python path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent.schemas import DestinationResearch, PlaceDetail
from research_agent.google_places import search_google_places
from shared.cache import cached_json

# Initialize PydanticAI Agent
# To prevent raising credentials errors on import when API keys are not set,
# we resolve the model name dynamically using TestModel if no keys exist.
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
    output_type=DestinationResearch,
    system_prompt=(
        "You are an expert travel research assistant. Your task is to compile a detailed, "
        "reliable, and interesting research report for a given destination. "
        "Use your tools to find accurate information on weather, top sights, and hidden gems. "
        "Verify your facts. Provide realistic safety scores (1 to 10) and engaging descriptions."
    )
)

@agent.tool
async def search_wikipedia(ctx: RunContext[None], query: str) -> str:
    """Search Wikipedia for information on the destination or its attractions.
    
    Args:
        query: The search terms (e.g., 'Goa weather' or 'Baga Beach Goa').
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "utf8": 1,
        "formatversion": 2
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                if search_results:
                    # Summarize search hits
                    snippets = [
                        f"Title: {result['title']}\nSnippet: {result['snippet']}"
                        for result in search_results[:3]
                    ]
                    return "\n\n".join(snippets)
                return "No Wikipedia articles found."
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"
    return "Failed to search Wikipedia."

@agent.tool
async def search_tavily(ctx: RunContext[None], query: str) -> str:
    """Run a general web search query using Tavily API.
    
    Args:
        query: Search query for weather, travel tips, safety, or hidden gems.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key not configured. Cannot perform web search."
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=8.0)
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer")
                if answer:
                    return f"Tavily Answer: {answer}"
                
                results = data.get("results", [])
                snippets = [
                    f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
                    for r in results[:3]
                ]
                return "\n\n".join(snippets)
    except Exception as e:
        return f"Error running search query: {str(e)}"
    return "Tavily search failed."

@agent.tool
async def search_google_places_tool(ctx: RunContext[None], destination: str, query: str = "top tourist attractions") -> str:
    """Search Google Places for attractions, restaurants, and points of interest.
    
    Args:
        destination: City or destination name.
        query: Search query (e.g. 'hidden gems', 'best restaurants').
    """
    places = await search_google_places(destination, query)
    if not places:
        return "Google Places API not configured or no results found."
    return "\n\n".join(
        f"Name: {p.name}\nLocation: {p.location}\nRating: {p.rating}\nDescription: {p.description}"
        for p in places
    )


@agent.tool
async def get_weather(ctx: RunContext[None], destination: str, month: Optional[str] = None) -> str:
    """Fetch seasonal weather information for the destination.
    
    Args:
        destination: City or destination name.
        month: Optional month of travel.
    """
    # OpenWeather API integration if API key is provided
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": destination, "appid": api_key, "units": "metric"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    temp = data.get("main", {}).get("temp")
                    desc = data.get("weather", [{}])[0].get("description", "")
                    return f"Current weather in {destination}: {temp}°C, {desc}."
        except Exception:
            pass # Fall back to heuristic description below
            
    # Heuristic weather fallbacks
    weather_dict = {
        "goa": {
            "july": "Monsoon season with heavy rainfall, high humidity, and temperatures around 25-30°C.",
            "default": "Tropical climate. Warm and sunny from November to February (22-32°C). Hot and humid in summer (March-May). Monsoons from June to September."
        },
        "tokyo": {
            "july": "Hot and humid summer with temperatures between 24-31°C. Occasional rain showers.",
            "default": "Temperate climate. Spring (March-May) is mild and features cherry blossoms. Autumn (September-November) is cool and scenic. Winter is cold but dry."
        },
        "paris": {
            "july": "Pleasant summer weather, warm and sunny with temperatures averaging 16-25°C. Highly active tourist season.",
            "default": "Temperate oceanic climate. Mild summers and cold winters. Average temperature ranges from 5°C in winter to 20°C in summer."
        }
    }
    
    dest_key = destination.lower()
    month_key = month.lower() if month else "default"
    
    if dest_key in weather_dict:
        return weather_dict[dest_key].get(month_key, weather_dict[dest_key]["default"])
        
    return f"Weather for {destination} is typically tropical or temperate depending on the region. Summers are warm and winters are mild. Best visited in dry season months."


def generate_mock_research(destination: str, month: Optional[str] = None) -> DestinationResearch:
    """Generates a high-quality mock DestinationResearch response.
    Used when API credentials for OpenAI/Gemini/Claude are not set.
    """
    dest_clean = destination.strip()
    dest_lower = dest_clean.lower()
    
    # Destination specific mock templates
    if "goa" in dest_lower:
        return DestinationResearch(
            destination=dest_clean,
            weather="Monsoon season in July. Warm and humid with frequent heavy rains. Average temperatures around 27°C (81°F). Lush green surroundings.",
            safety_score=8,
            top_places=[
                PlaceDetail(
                    name="Baga Beach",
                    description="One of the most famous beaches in North Goa, known for nightlife, water sports, and beach shacks.",
                    location="North Goa, Bardez",
                    rating=4.2
                ),
                PlaceDetail(
                    name="Basilica of Bom Jesus",
                    description="A UNESCO World Heritage site holding the mortal remains of St. Francis Xavier. Famous Baroque architecture.",
                    location="Old Goa",
                    rating=4.6
                )
            ],
            hidden_gems=[
                PlaceDetail(
                    name="Chorao Island & Salim Ali Bird Sanctuary",
                    description="A tranquil riverine island reachable by ferry. Hosts beautiful mangrove forests and rare migratory birds.",
                    location="Mandovi River, near Panaji",
                    rating=4.4
                ),
                PlaceDetail(
                    name="Cola Beach",
                    description="An offbeat, secluded beach in South Goa famous for its freshwater blue lagoon meeting the sea.",
                    location="South Goa, Canacona",
                    rating=4.5
                )
            ]
        )
    elif "tokyo" in dest_lower:
        return DestinationResearch(
            destination=dest_clean,
            weather="Warm and humid in July. Summer festivals and firework displays are common. Average temperatures range from 22°C to 29°C.",
            safety_score=10,
            top_places=[
                PlaceDetail(
                    name="Senso-ji Temple",
                    description="Tokyo's oldest and one of its most significant Buddhist temples, located in the historic Asakusa district.",
                    location="Asakusa, Taito City",
                    rating=4.7
                ),
                PlaceDetail(
                    name="Shibuya Crossing",
                    description="The world's busiest pedestrian scramble crossing, illuminated by giant neon screens and packed with shops.",
                    location="Shibuya City",
                    rating=4.5
                )
            ],
            hidden_gems=[
                PlaceDetail(
                    name="Yanaka District",
                    description="One of the few remaining old neighborhoods of Tokyo that survived WWII bombing. Exudes old 'Shitamachi' atmosphere.",
                    location="Taito City, north of Ueno",
                    rating=4.6
                ),
                PlaceDetail(
                    name="Todoroki Valley",
                    description="A forested ravine path and sanctuary hidden right in the middle of Tokyo's urban residential sprawl.",
                    location="Setagaya City",
                    rating=4.3
                )
            ]
        )
    else:
        # Generic mock template for any other city
        month_str = f" in {month}" if month else ""
        return DestinationResearch(
            destination=dest_clean,
            weather=f"Comfortable climate{month_str}. Mild temperatures with moderate sunshine and occasional light breeze, averaging 20°C - 24°C.",
            safety_score=7,
            top_places=[
                PlaceDetail(
                    name=f"Historic Old Town of {dest_clean}",
                    description="A charming central district featuring beautiful heritage architecture, local boutique shops, and cafes.",
                    location="Central District",
                    rating=4.6
                ),
                PlaceDetail(
                    name=f"{dest_clean} City Park",
                    description="A large municipal garden perfect for walks, boat rentals, and panoramic views of the city skyline.",
                    location="North Sector",
                    rating=4.4
                )
            ],
            hidden_gems=[
                PlaceDetail(
                    name="The Secret Lookout Point",
                    description="A quiet hilltop location loved by locals for catching spectacular sunset views away from tourist crowds.",
                    location="Eastern Ridge",
                    rating=4.8
                )
            ]
        )


async def _run_research_inner(destination: str, month: Optional[str] = None) -> DestinationResearch:
    """Core research logic without caching."""
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not openai_key and not gemini_key:
        result = generate_mock_research(destination, month)
    else:
        try:
            prompt = f"Perform research for destination: {destination}"
            if month:
                prompt += f", visiting in the month of {month}"
            agent_result = await agent.run(prompt)
            result = agent_result.data
        except Exception as e:
            print(f"Error running PydanticAI agent: {str(e)}. Falling back to mock data.", file=sys.stderr)
            result = generate_mock_research(destination, month)

    # Enrich with Google Places when available
    google_places = await search_google_places(destination)
    if google_places and len(result.top_places) < 3:
        result.top_places = (result.top_places + google_places)[:5]
    hidden = await search_google_places(destination, "hidden gems off the beaten path")
    if hidden:
        result.hidden_gems = (result.hidden_gems + hidden)[:5]
    return result


async def run_research(destination: str, month: Optional[str] = None) -> DestinationResearch:
    """Executes destination research with Redis caching and Google Places enrichment."""
    month_key = month or "any"
    payload = await cached_json(
        "research",
        (destination.lower(), month_key),
        ttl=3600,
        fetcher=lambda: _run_research_inner(destination, month),
    )
    return DestinationResearch(**payload)
