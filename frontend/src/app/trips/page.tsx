"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getTrips } from "@/lib/api";

export default function TripsPage() {
  const { data: trips = [], isLoading, error } = useQuery({
    queryKey: ["trips"],
    queryFn: getTrips,
  });

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Dashboard</h1>
            <p className="mt-2 text-slate-600">Current and upcoming trips.</p>
          </div>
          <div className="flex gap-2">
            <Link href="/chat" className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">New trip</Link>
            <Link href="/" className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-2 text-sm font-semibold hover:bg-slate-200">Home</Link>
          </div>
        </div>

        {isLoading ? (
          <div className="rounded-2xl border border-dashed p-8 text-center text-slate-500">Loading trips…</div>
        ) : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">{error.message}</div>
        ) : trips.length === 0 ? (
          <div className="rounded-2xl border p-8 text-center text-slate-500">
            No trips yet. <Link href="/chat" className="text-sky-600 hover:underline">Start planning</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {trips.map((trip) => (
              <Link key={trip.trip_id} href={`/trips/${trip.trip_id}`} className="block rounded-3xl border border-slate-200 bg-slate-50 p-6 transition hover:bg-slate-100">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm uppercase tracking-[0.3em] text-sky-600">{trip.status}</p>
                    <h2 className="mt-2 text-2xl font-semibold">{trip.title}</h2>
                    <p className="mt-2 text-sm text-slate-600">{trip.destination} • {trip.start_date} → {trip.end_date}</p>
                  </div>
                  <div className="text-right text-sm text-slate-500">
                    <p>Budget: ₹{trip.budget_limit.toLocaleString()}</p>
                    <p>{trip.plan_count} plan{trip.plan_count === 1 ? "" : "s"}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
