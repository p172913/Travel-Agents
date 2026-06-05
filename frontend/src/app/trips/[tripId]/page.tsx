"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getTripDetails, replanTrip, submitFeedback } from "@/lib/api";

export default function TripDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const tripId = params?.tripId ? Number(params.tripId) : NaN;
  const [replanning, setReplanning] = useState(false);
  const [copied, setCopied] = useState(false);

  const { data: trip, isLoading, error } = useQuery({
    queryKey: ["trip", tripId],
    queryFn: () => getTripDetails(tripId),
    enabled: !Number.isNaN(tripId),
  });

  if (Number.isNaN(tripId)) {
    router.replace("/trips");
    return null;
  }

  async function handleFeedback(planId: number, item: Record<string, unknown>, rating: 1 | -1) {
    await submitFeedback({
      trip_plan_id: planId,
      item_type: String(item.type || "activity"),
      item_id: String(item.id || item.name),
      rating,
    });
    queryClient.invalidateQueries({ queryKey: ["trip", tripId] });
  }

  async function handleReplan() {
    setReplanning(true);
    try {
      const result = await replanTrip(tripId);
      router.push(`/trips/${result.trip_id}`);
    } finally {
      setReplanning(false);
    }
  }

  function copyShareLink() {
    if (!trip?.share_token) return;
    const url = `${window.location.origin}/t/${trip.share_token}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-5xl rounded-3xl border bg-white p-8">Loading trip details…</div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-5xl rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700">
          <p>Unable to load this trip.</p>
          <Link href="/trips" className="mt-4 inline-block rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white">Back to trips</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Trip details</p>
            <h1 className="mt-2 text-3xl font-semibold">{trip.title}</h1>
            <p className="mt-2 text-sm text-slate-600">{trip.destination} • {trip.start_date} → {trip.end_date}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={copyShareLink} className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-2 text-sm font-semibold hover:bg-slate-200">
              {copied ? "Copied!" : "Share"}
            </button>
            <button onClick={handleReplan} disabled={replanning} className="rounded-2xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50">
              {replanning ? "Replanning…" : "Auto-replan"}
            </button>
            <Link href="/trips" className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-2 text-sm font-semibold hover:bg-slate-200">Back</Link>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="font-semibold">Budget</h2>
            <p className="mt-2">₹{trip.budget_limit.toLocaleString()}</p>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 className="font-semibold">Status</h2>
            <p className="mt-2 capitalize">{trip.status}</p>
          </div>
        </div>

        <section className="mt-8 space-y-6">
          {trip.plans.map((plan) => (
            <div key={plan.plan_id} className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
              <h2 className="text-xl font-semibold">Plan #{plan.plan_id}</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold">Budget breakdown</h3>
                  <pre className="mt-2 overflow-x-auto rounded-2xl bg-white p-3 text-sm">{JSON.stringify(plan.budget_breakdown, null, 2)}</pre>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Why AI picked this plan</h3>
                  <p className="mt-2 text-sm leading-6">{plan.explanation || "No explanation available."}</p>
                </div>
              </div>

              {plan.itinerary?.days ? (
                <div className="mt-6 space-y-4">
                  <h3 className="font-semibold">Itinerary</h3>
                  {(plan.itinerary.days as Array<Record<string, unknown>>).map((day) => (
                    <div key={String(day.day)} className="rounded-3xl border bg-white p-4">
                      <p className="text-sm font-semibold">Day {String(day.day)}</p>
                      <div className="mt-3 space-y-3">
                        {(day.items as Array<Record<string, unknown>>)?.map((item, index) => (
                          <div key={index} className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-sm font-semibold">{String(item.time)} — {String(item.title)}</p>
                            <p className="mt-1 text-sm">{String(item.details)}</p>
                            {item.reason ? (
                              <div className="mt-2 rounded-xl bg-sky-50 px-3 py-2 text-xs text-sky-800">
                                ✓ {String(item.reason)}
                              </div>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}

              {plan.recommendations?.length > 0 ? (
                <div className="mt-6">
                  <h3 className="font-semibold">Recommendations</h3>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    {plan.recommendations.map((item, index) => (
                      <div key={index} className="rounded-3xl border bg-white p-4">
                        <p className="font-semibold">{String(item.name)}</p>
                        <p className="text-sm text-slate-600">{String(item.type)}</p>
                        <p className="mt-2 text-sm">{String(item.description || item.rationale)}</p>
                        {item.rationale ? (
                          <div className="mt-2 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
                            ✓ {String(item.rationale)}
                          </div>
                        ) : null}
                        <div className="mt-3 flex gap-2">
                          <button onClick={() => handleFeedback(plan.plan_id, item, 1)} className="rounded-xl border px-3 py-1 text-sm hover:bg-slate-50" title="Helpful">👍</button>
                          <button onClick={() => handleFeedback(plan.plan_id, item, -1)} className="rounded-xl border px-3 py-1 text-sm hover:bg-slate-50" title="Not helpful">👎</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
