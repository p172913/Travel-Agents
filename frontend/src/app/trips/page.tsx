"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTrips, TripSummary } from "@/lib/api";

export default function TripsPage() {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTrips() {
      try {
        const results = await getTrips();
        setTrips(results);
      } catch (err) {
        console.error("Trips load error:", err);
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Unable to load trips. Check the API connection.");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchTrips();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg shadow-slate-200/50">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Saved Trips</h1>
            <p className="mt-2 text-slate-600">Browse trips that have been created in the TravelSouls backend.</p>
          </div>
          <Link href="/" className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-slate-200">
            Home
          </Link>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">Loading trips...</div>
        ) : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>
        ) : trips.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 p-8 text-center text-slate-500">No trips found. Create a plan in the API and refresh.</div>
        ) : (
          <div className="space-y-4">
            {trips.map((trip) => (
              <Link
                key={trip.trip_id}
                href={`/trips/${trip.trip_id}`}
                className="group block rounded-3xl border border-slate-200 bg-slate-50 p-6 transition hover:border-slate-300 hover:bg-slate-100"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm uppercase tracking-[0.3em] text-sky-600">{trip.status}</p>
                    <h2 className="mt-2 text-2xl font-semibold text-slate-950">{trip.title}</h2>
                    <p className="mt-2 text-sm text-slate-600">{trip.destination} • {trip.start_date} → {trip.end_date}</p>
                  </div>
                  <div className="text-right text-sm text-slate-500">
                    <p>Budget: ₹{trip.budget_limit.toLocaleString()}</p>
                    <p>{trip.plan_count} plan{trip.plan_count === 1 ? "" : "s"}</p>
                  </div>
                </div>
                <p className="mt-4 text-sm text-slate-700">Click to view full trip details and itinerary information.</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
