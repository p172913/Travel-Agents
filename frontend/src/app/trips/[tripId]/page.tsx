"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getTripDetails, TripDetails } from "@/lib/api";

export default function TripDetailPage() {
  const params = useParams();
  const router = useRouter();
  const tripId = params?.tripId ? Number(params.tripId) : NaN;

  const [trip, setTrip] = useState<TripDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (Number.isNaN(tripId)) {
      router.replace("/trips");
      return;
    }

    async function fetchTrip() {
      try {
        const details = await getTripDetails(tripId);
        setTrip(details);
      } catch (err) {
        setError("Unable to load this trip. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    fetchTrip();
  }, [tripId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
        <div className="mx-auto max-w-5xl rounded-3xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/50">Loading trip details…</div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
        <div className="mx-auto max-w-5xl rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700 shadow-lg shadow-red-100/60">
          <p>{error ?? "Trip not found."}</p>
          <Link href="/trips" className="mt-4 inline-block rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800">
            Back to trips
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg shadow-slate-200/50">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Trip details</p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-950">{trip.title}</h1>
            <p className="mt-2 text-sm text-slate-600">{trip.destination} • {trip.start_date} → {trip.end_date}</p>
          </div>
          <Link href="/trips" className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-slate-200">
            Back to trips
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-base font-semibold text-slate-900">Budget</h2>
            <p className="mt-2 text-slate-700">₹{trip.budget_limit.toLocaleString()}</p>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-base font-semibold text-slate-900">Status</h2>
            <p className="mt-2 text-slate-700 capitalize">{trip.status}</p>
          </div>
        </div>

        <section className="mt-8 space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-xl font-semibold text-slate-950">Plans</h2>
            {trip.plans.length === 0 ? (
              <p className="mt-3 text-slate-600">No saved plans yet. Run orchestration to generate one.</p>
            ) : (
              <div className="mt-4 space-y-4">
                {trip.plans.map((plan) => (
                  <div key={plan.plan_id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-lg font-semibold text-slate-950">Plan #{plan.plan_id}</p>
                      <p className="text-sm text-slate-500">Created {new Date(plan.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">Budget breakdown</h3>
                        <pre className="mt-2 overflow-x-auto rounded-2xl bg-slate-100 p-3 text-sm text-slate-700">{JSON.stringify(plan.budget_breakdown, null, 2)}</pre>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">Explanation</h3>
                        <p className="mt-2 text-sm leading-6 text-slate-700">{plan.explanation || "No explanation available."}</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <h3 className="text-sm font-semibold text-slate-900">Itinerary</h3>
                      <div className="mt-2 space-y-4">
                        {plan.itinerary.days && plan.itinerary.days.length > 0 ? (
                          plan.itinerary.days.map((day: any) => (
                            <div key={day.day} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                              <p className="text-sm font-semibold text-slate-900">Day {day.day} • {new Date(day.date).toLocaleDateString()}</p>
                              <div className="mt-3 space-y-3">
                                {day.items?.map((item: any, index: number) => (
                                  <div key={index} className="rounded-2xl bg-white p-3 shadow-sm">
                                    <p className="text-sm font-semibold text-slate-900">{item.time} — {item.title}</p>
                                    <p className="mt-1 text-sm leading-6 text-slate-700">{item.details}</p>
                                    {item.reason ? (
                                      <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">Why: {item.reason}</p>
                                    ) : null}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-slate-600">No itinerary details available.</p>
                        )}
                      </div>
                    </div>
                    <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                      <h3 className="text-sm font-semibold text-slate-900">Recommendations</h3>
                      {plan.recommendations && plan.recommendations.length > 0 ? (
                        <div className="mt-4 grid gap-4 sm:grid-cols-2">
                          {plan.recommendations.map((item: any, index: number) => (
                            <div key={index} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                              <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                              <p className="mt-1 text-sm text-slate-600">{item.type}</p>
                              <p className="mt-3 text-sm leading-6 text-slate-700">{item.description || item.rationale}</p>
                              <div className="mt-3 flex items-center justify-between gap-3 text-xs text-slate-500">
                                <span>Rating: {item.rating}</span>
                                {item.price_level ? <span>Price level: {item.price_level}</span> : null}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="mt-3 text-sm text-slate-600">No recommendations available for this plan.</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-xl font-semibold text-slate-950">Requests</h2>
            {trip.requests.length === 0 ? (
              <p className="mt-3 text-slate-600">No request history available.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {trip.requests.map((request) => (
                  <li key={request.request_id} className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-sm font-semibold text-slate-900">{request.prompt}</p>
                    <p className="mt-1 text-sm text-slate-500">Status: {request.status}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
