from datetime import datetime, timedelta, date


def build_itinerary(start_date: str, end_date: str, booking_result, recommendation_result, budget_result):
    """Create a structured itinerary from booking and recommendation results."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception:
        start = date.today()
        end = start + timedelta(days=6)

    total_days = max((end - start).days, 1)
    days = []
    recs = recommendation_result.recommendations or []

    for day_index in range(total_days):
        current_date = start + timedelta(days=day_index)
        items = []

        if day_index == 0:
            if booking_result.best_flights:
                first_flight = booking_result.best_flights[0]
                items.append({
                    "time": "09:00",
                    "title": "Arrive at destination",
                    "details": f"Flight {first_flight.flight_number} arrives. Check in to hotel and relax.",
                    "reason": "Start the trip with arrival, settling in, and a smooth first-day plan."
                })
            items.append({
                "time": "12:00",
                "title": "Check in and lunch",
                "details": "Settle into accommodations and enjoy a local lunch nearby.",
                "reason": "Give travelers time to recharge after arrival and explore local food."
            })

        if recs:
            recommendation = recs[min(day_index, len(recs) - 1)]
            items.append({
                "time": "15:00",
                "title": recommendation.name,
                "details": recommendation.description or recommendation.rationale,
                "reason": recommendation.rationale or f"Recommended because it fits your {recommendation.type} preferences."
            })

        if booking_result.best_hotels and day_index == 0:
            items.append({
                "time": "18:00",
                "title": f"Stay at {booking_result.best_hotels[0].hotel_name}",
                "details": f"Nightly rate {booking_result.best_hotels[0].nightly_rate} {booking_result.best_hotels[0].rating} stars.",
                "reason": "This hotel is selected as a comfortable first-night stay near the destination."
            })

        if day_index == total_days - 1:
            items.append({
                "time": "17:00",
                "title": "Trip wrap-up",
                "details": "Review your itinerary, pack, and prepare for departure tomorrow.",
                "reason": "Finish the trip with a calm wrap-up and preparation for departure."
            })

        days.append({
            "day": day_index + 1,
            "date": current_date.isoformat(),
            "items": items
        })

    return {"days": days}


def start_date_to_month(date_str: str) -> str:
    try:
        parts = date_str.split("-")
        if len(parts) >= 2:
            month_num = int(parts[1])
            months = ["", "January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
            return months[month_num] if 1 <= month_num <= 12 else "Month"
    except Exception:
        pass
    return "Month"


def days_between_dates(start: str, end: str) -> int:
    try:
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        end_obj = datetime.strptime(end, "%Y-%m-%d")
        return (end_obj - start_obj).days
    except Exception:
        return 7
