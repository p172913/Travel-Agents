const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const isBrowser = typeof window !== "undefined";
const isLocalhost = isBrowser && ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE = rawApiUrl || (isLocalhost ? "http://localhost:8000" : undefined);
export const API_URL_SOURCE = rawApiUrl ? "env" : isLocalhost ? "localhost-fallback" : "missing-env";

function apiErrorMessage(url: string, response: Response, body: string) {
  return `API request failed: ${response.status} ${response.statusText} when fetching ${url}. Response body: ${body}`;
}

function missingApiUrlError(url: string) {
  if (isLocalhost) {
    return `Missing NEXT_PUBLIC_API_URL. Using local development fallback for ${url}. Set NEXT_PUBLIC_API_URL to your backend URL for production.`;
  }
  return `Missing NEXT_PUBLIC_API_URL in production. The app cannot reach the backend. Set NEXT_PUBLIC_API_URL in Vercel to your Render backend URL (for example https://travel-agents-i4p2.onrender.com).`;
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
  recommendations: Array<Record<string, any>>;
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

export type OrchestratorTripRequest = {
  destination: string;
  start_date: string;
  end_date: string;
  total_budget: number;
  travel_style: string;
  travelers: number;
};

export type OrchestrationResponse = {
  trip_id: number;
  plan_id: number;
  plan: Record<string, any>;
};

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  if (!API_BASE) {
    throw new Error(missingApiUrlError(url));
  }

  const response = await fetch(url, {
    cache: "no-store",
    ...options,
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

export async function orchestrateTrip(request: OrchestratorTripRequest): Promise<OrchestrationResponse> {
  return fetchJson<OrchestrationResponse>(`${API_BASE}/api/plan/orchestrate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}
