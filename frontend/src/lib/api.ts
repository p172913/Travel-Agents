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
  return `Missing NEXT_PUBLIC_API_URL in production. Set NEXT_PUBLIC_API_URL in Vercel to your Render backend URL.`;
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
  share_token?: string;
  share_url?: string;
  created_at: string;
};

export type TripPlanDetails = {
  plan_id: number;
  itinerary: Record<string, unknown>;
  budget_breakdown: Record<string, unknown>;
  explanation: string | null;
  recommendations: Array<Record<string, unknown>>;
  created_at: string;
  bookings: Array<Record<string, unknown>>;
};

export type TripDetails = {
  trip_id: number;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget_limit: number;
  status: string;
  share_token?: string;
  share_url?: string;
  plans: TripPlanDetails[];
  requests: Array<Record<string, unknown>>;
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
  plan: Record<string, unknown>;
};

export type ChatPlanRequest = {
  prompt: string;
  total_budget?: number;
  travelers?: number;
  travel_style?: string;
};

export type FeedbackRequest = {
  trip_plan_id: number;
  item_type: string;
  item_id: string;
  rating: 1 | -1;
  comments?: string;
};

export type Preferences = {
  budget_tier: string;
  dietary_preferences: string[];
  travel_style: string[];
  interests: string[];
};

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  if (!API_BASE) {
    throw new Error(missingApiUrlError(url));
  }

  const response = await fetch(url, { cache: "no-store", ...options });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(apiErrorMessage(url, response, body));
  }
  return JSON.parse(body) as T;
}

export async function getTrips(): Promise<TripSummary[]> {
  return fetchJson<TripSummary[]>(`${API_BASE}/api/trips`);
}

export async function getTripDetails(tripId: number): Promise<TripDetails> {
  return fetchJson<TripDetails>(`${API_BASE}/api/trips/${tripId}`);
}

export async function getSharedTrip(shareToken: string): Promise<TripDetails> {
  return fetchJson<TripDetails>(`${API_BASE}/api/share/${shareToken}`);
}

export async function orchestrateTrip(request: OrchestratorTripRequest): Promise<OrchestrationResponse> {
  return fetchJson<OrchestrationResponse>(`${API_BASE}/api/plan/orchestrate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export async function chatPlan(request: ChatPlanRequest): Promise<OrchestrationResponse> {
  return fetchJson<OrchestrationResponse>(`${API_BASE}/api/plan/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export async function replanTrip(tripId: number, reason?: string): Promise<OrchestrationResponse> {
  return fetchJson<OrchestrationResponse>(`${API_BASE}/api/plan/replan/${tripId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason || "User requested replan" }),
  });
}

export async function submitFeedback(request: FeedbackRequest): Promise<{ status: string; feedback_id: number }> {
  return fetchJson(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export async function getPreferences(): Promise<Preferences> {
  return fetchJson<Preferences>(`${API_BASE}/api/preferences`);
}

export async function updatePreferences(prefs: Preferences): Promise<{ status: string; preferences: Preferences }> {
  return fetchJson(`${API_BASE}/api/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prefs),
  });
}
