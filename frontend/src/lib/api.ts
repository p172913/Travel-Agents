const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
export const API_BASE = rawApiUrl || "http://localhost:8000";
export const API_URL_SOURCE = rawApiUrl ? "env" : "fallback";

function apiErrorMessage(url: string, response: Response, body: string) {
  return `API request failed: ${response.status} ${response.statusText} when fetching ${url}. Response body: ${body}`;
}

function missingApiUrlError(url: string) {
  return `Missing NEXT_PUBLIC_API_URL in Vercel environment. Tried to fetch ${url} using fallback http://localhost:8000.`;
}

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

async function fetchJson<T>(url: string): Promise<T> {
  if (!rawApiUrl) {
    throw new Error(missingApiUrlError(url));
  }

  const response = await fetch(url, {
    cache: "no-store",
  });

  const body = await response.text();
  if (!response.ok) {
    throw new Error(apiErrorMessage(url, response, body));
  }

  try {
    return JSON.parse(body) as T;
  } catch (e) {
    throw new Error(`Invalid JSON response from ${url}: ${e instanceof Error ? e.message : String(e)}`);
  }
}

export async function getTrips(): Promise<TripSummary[]> {
  return fetchJson<TripSummary[]>(`${API_BASE}/api/trips`);
}

export async function getTripDetails(tripId: number): Promise<TripDetails> {
  return fetchJson<TripDetails>(`${API_BASE}/api/trips/${tripId}`);
}
