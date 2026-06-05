"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getSharedTrip, TripDetails } from "@/lib/api";

export default function SharedTripPage() {
  const params = useParams();
  const token = params?.token as string;

  const { data: trip, isLoading, error } = useQuery<TripDetails>({
    queryKey: ["shared-trip", token],
    queryFn: () => getSharedTrip(token),
    enabled: !!token,
  });

  if (isLoading) {
    return <div className="min-h-screen bg-slate-50 px-6 py-10"><div className="mx-auto max-w-5xl rounded-3xl border bg-white p-8">Loading shared trip…</div></div>;
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-5xl rounded-3xl border border-red-200 bg-red-50 p-8 text-red-700">
          Shared trip not found.
          <Link href="/" className="mt-4 block text-sky-600">Go home</Link>
        </div>
      </div>
    );
  }

  const plan = trip.plans[0];

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Shared itinerary</p>
        <h1 className="mt-2 text-3xl font-semibold">{trip.title}</h1>
        <p className="mt-2 text-sm text-slate-600">{trip.destination} • {trip.start_date} → {trip.end_date}</p>

        {plan ? (
          <div className="mt-8 space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
              <h2 className="font-semibold">Budget breakdown</h2>
              <pre className="mt-2 overflow-x-auto rounded-2xl bg-white p-3 text-sm">{JSON.stringify(plan.budget_breakdown, null, 2)}</pre>
            </div>
            {plan.itinerary?.days ? (
              <div className="space-y-4">
                {(plan.itinerary.days as Array<Record<string, unknown>>).map((day) => (
                  <div key={String(day.day)} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="font-semibold">Day {String(day.day)}</p>
                    <div className="mt-3 space-y-2">
                      {(day.items as Array<Record<string, unknown>>)?.map((item, i) => (
                        <div key={i} className="rounded-2xl bg-white p-3 text-sm">
                          <p className="font-semibold">{String(item.time)} — {String(item.title)}</p>
                          {item.reason ? <p className="mt-1 text-xs text-slate-500">Why: {String(item.reason)}</p> : null}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : (
          <p className="mt-6 text-slate-600">No plan generated yet.</p>
        )}

        <Link href="/chat" className="mt-8 inline-block rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800">
          Plan your own trip
        </Link>
      </div>
    </div>
  );
}
