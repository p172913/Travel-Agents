"""Amadeus API client for flight and hotel search with mock fallback."""

import logging
import os
import time
from typing import List, Optional, Tuple

import httpx

from .schemas import BookingResult, Flight, Hotel

logger = logging.getLogger("travelsouls.amadeus")

_token_cache: dict = {"token": None, "expires": 0}

IATA_CODES = {
    "goa": "GOI", "mumbai": "BOM", "delhi": "DEL", "tokyo": "TYO",
    "paris": "PAR", "london": "LON", "dubai": "DXB", "bangkok": "BKK",
    "new york": "NYC", "singapore": "SIN", "bali": "DPS", "jaipur": "JAI",
}


def _destination_iata(destination: str) -> str:
    key = destination.lower().strip()
    for name, code in IATA_CODES.items():
        if name in key:
            return code
    return "DEL"


async def _get_token() -> Optional[str]:
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    base = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base}/v1/security/oauth2/token",
                data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                _token_cache["token"] = data["access_token"]
                _token_cache["expires"] = time.time() + data.get("expires_in", 1800) - 60
                return _token_cache["token"]
    except Exception as exc:
        logger.warning("Amadeus auth failed: %s", exc)
    return None


async def search_amadeus_flights(
    origin: str, destination: str, start_date: str, travelers: int
) -> List[Flight]:
    token = await _get_token()
    if not token:
        return []
    dest_code = _destination_iata(destination)
    origin_code = os.getenv("AMADEUS_ORIGIN_IATA", "DEL")
    base = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{base}/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin_code,
                    "destinationLocationCode": dest_code,
                    "departureDate": start_date,
                    "adults": travelers,
                    "max": 5,
                    "currencyCode": "INR",
                },
                timeout=15.0,
            )
            if resp.status_code != 200:
                return []
            offers = resp.json().get("data", [])
            flights = []
            for offer in offers[:5]:
                itineraries = offer.get("itineraries", [{}])
                segments = itineraries[0].get("segments", [{}]) if itineraries else [{}]
                seg = segments[0]
                price = float(offer.get("price", {}).get("grandTotal", 0))
                flights.append(Flight(
                    provider="Amadeus",
                    flight_number=seg.get("carrierCode", "XX") + str(seg.get("number", "000")),
                    depart_time=seg.get("departure", {}).get("at", start_date + "T09:00:00"),
                    arrive_time=segments[-1].get("arrival", {}).get("at", start_date + "T12:00:00"),
                    duration_minutes=int(itineraries[0].get("duration", "PT3H").replace("PT", "").replace("H", "") or 3) * 60,
                    price=price,
                    currency=offer.get("price", {}).get("currency", "INR"),
                ))
            return sorted(flights, key=lambda f: f.price)
    except Exception as exc:
        logger.warning("Amadeus flight search failed: %s", exc)
    return []


async def search_amadeus_hotels(destination: str, start_date: str, end_date: str) -> List[Hotel]:
    token = await _get_token()
    if not token:
        return []
    dest_code = _destination_iata(destination)
    base = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
    try:
        async with httpx.AsyncClient() as client:
            city_resp = await client.get(
                f"{base}/v1/reference-data/locations/hotels/by-city",
                headers={"Authorization": f"Bearer {token}"},
                params={"cityCode": dest_code},
                timeout=10.0,
            )
            if city_resp.status_code != 200:
                return []
            hotel_ids = [h["hotelId"] for h in city_resp.json().get("data", [])[:5]]
            if not hotel_ids:
                return []
            offers_resp = await client.get(
                f"{base}/v3/shopping/hotel-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={"hotelIds": ",".join(hotel_ids), "checkInDate": start_date, "checkOutDate": end_date, "adults": 1},
                timeout=15.0,
            )
            if offers_resp.status_code != 200:
                return []
            hotels = []
            for item in offers_resp.json().get("data", [])[:5]:
                hotel = item.get("hotel", {})
                offers = item.get("offers", [{}])
                price_info = offers[0].get("price", {}) if offers else {}
                total = float(price_info.get("total", 0))
                nights = max((__import__("datetime").datetime.strptime(end_date, "%Y-%m-%d") - __import__("datetime").datetime.strptime(start_date, "%Y-%m-%d")).days, 1)
                hotels.append(Hotel(
                    provider="Amadeus",
                    hotel_name=hotel.get("name", "Hotel"),
                    check_in=start_date,
                    check_out=end_date,
                    nightly_rate=round(total / nights, 2),
                    total_price=total,
                    rating=4.0,
                ))
            return sorted(hotels, key=lambda h: h.total_price)
    except Exception as exc:
        logger.warning("Amadeus hotel search failed: %s", exc)
    return []


def generate_mock_booking(destination: str, start_date: str, end_date: str, travelers: int) -> BookingResult:
    flights = [
        Flight(provider="MockAir", flight_number="MA123", depart_time=f"{start_date}T09:00:00",
               arrive_time=f"{start_date}T12:00:00", duration_minutes=180, price=150.0 * travelers, currency="INR"),
        Flight(provider="MockSky", flight_number="MS456", depart_time=f"{start_date}T14:00:00",
               arrive_time=f"{start_date}T17:30:00", duration_minutes=210, price=175.0 * travelers, currency="INR"),
    ]
    nights = max((__import__("datetime").datetime.strptime(end_date, "%Y-%m-%d") - __import__("datetime").datetime.strptime(start_date, "%Y-%m-%d")).days, 1)
    hotels = [
        Hotel(provider="MockHotels", hotel_name=f"{destination} Seaside Resort", check_in=start_date, check_out=end_date,
              nightly_rate=2500.0, total_price=2500.0 * nights, rating=4.3),
        Hotel(provider="BudgetStay", hotel_name=f"{destination} City Inn", check_in=start_date, check_out=end_date,
              nightly_rate=1500.0, total_price=1500.0 * nights, rating=4.0),
    ]
    return BookingResult(destination=destination, start_date=start_date, end_date=end_date,
                         best_flights=sorted(flights, key=lambda f: f.price),
                         best_hotels=sorted(hotels, key=lambda h: h.total_price))
