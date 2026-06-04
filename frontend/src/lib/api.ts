export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type TripSummary = {
  trip_id: number;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget_limit: number;
  status: string;
  plan_count: number;
  created_at: string;
};

export type TripPlanDetails = {
  plan_id: number;
  itinerary: Record<string, any>;
  budget_breakdown: Record<string, any>;
  explanation: string | null;
  created_at: string;
  bookings: Array<Record<string, any>>;
};

export type TripDetails = {
  trip_id: number;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget_limit: number;
  status: string;
  plans: TripPlanDetails[];
  requests: Array<Record<string, any>>;
};

export async function getTrips(): Promise<TripSummary[]> {
  const response = await fetch(`${API_BASE}/api/trips`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to load trips");
  }
  return response.json();
}

export async function getTripDetails(tripId: number): Promise<TripDetails> {
  const response = await fetch(`${API_BASE}/api/trips/${tripId}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to load trip details");
  }
  return response.json();
}
