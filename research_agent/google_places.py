"""Google Places API integration for attraction research."""

import logging
import os
from typing import List

import httpx

from .schemas import PlaceDetail

logger = logging.getLogger("travelsouls.places")


async def search_google_places(destination: str, query: str = "top tourist attractions") -> List[PlaceDetail]:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": f"{query} in {destination}", "key": api_key},
                timeout=10.0,
            )
            if resp.status_code != 200:
                return []
            results = resp.json().get("results", [])
            places = []
            for r in results[:5]:
                places.append(PlaceDetail(
                    name=r.get("name", "Unknown"),
                    description=r.get("formatted_address", "Popular attraction"),
                    location=r.get("formatted_address", destination),
                    rating=round(r.get("rating", 4.0), 1),
                ))
            return places
    except Exception as exc:
        logger.warning("Google Places search failed: %s", exc)
    return []
