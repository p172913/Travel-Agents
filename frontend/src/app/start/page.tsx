"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { orchestrateTrip } from "@/lib/api";

export default function StartPlanningPage() {
  const router = useRouter();
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState(50000);
  const [travelers, setTravelers] = useState(2);
  const [travelStyle, setTravelStyle] = useState("balanced");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!destination || !startDate || !endDate) {
      setError("Please provide destination, start date, and end date.");
      return;
    }

    setLoading(true);

    try {
      const response = await orchestrateTrip({
        destination,
        start_date: startDate,
        end_date: endDate,
        total_budget: budget,
        travel_style: travelStyle,
        travelers,
      });

      setSuccessMessage(`Trip created successfully! Trip ID: ${response.trip_id}`);
      setTimeout(() => {
        router.push("/trips");
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create trip.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16 sm:px-10">
        <div className="rounded-3xl border border-slate-200 bg-white/95 p-10 shadow-xl shadow-slate-200/40">
          <div className="mb-8">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Start Planning</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Start a new travel plan
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Fill in the details below to create a new trip plan. The app will send the request to the backend and generate a trip using the orchestration endpoint.
            </p>
          </div>

          <form className="space-y-8" onSubmit={handleSubmit}>
            <div className="grid gap-6 sm:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Destination</span>
                <input
                  value={destination}
                  onChange={(event) => setDestination(event.target.value)}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                  placeholder="Goa"
                  required
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Travel style</span>
                <select
                  value={travelStyle}
                  onChange={(event) => setTravelStyle(event.target.value)}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                >
                  <option value="balanced">Balanced</option>
                  <option value="budget">Budget</option>
                  <option value="luxury">Luxury</option>
                </select>
              </label>
            </div>

            <div className="grid gap-6 sm:grid-cols-3">
              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Start date</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(event) => setStartDate(event.target.value)}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                  required
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">End date</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(event) => setEndDate(event.target.value)}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                  required
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Travelers</span>
                <input
                  type="number"
                  min={1}
                  value={travelers}
                  onChange={(event) => setTravelers(Number(event.target.value))}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                />
              </label>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Budget</span>
                <input
                  type="number"
                  min={1000}
                  value={budget}
                  onChange={(event) => setBudget(Number(event.target.value))}
                  className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500"
                />
              </label>

              <div className="space-y-2">
                <span className="text-sm font-semibold text-slate-700">Current status</span>
                <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900">{loading ? "Creating trip..." : "Ready to execute"}</div>
              </div>
            </div>

            {error ? (
              <div className="rounded-3xl border border-red-200 bg-red-50 px-6 py-4 text-sm text-red-700">{error}</div>
            ) : null}
            {successMessage ? (
              <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-6 py-4 text-sm text-emerald-700">{successMessage}</div>
            ) : null}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Link href="/trips" className="inline-flex rounded-2xl border border-slate-200 bg-slate-100 px-6 py-4 text-center text-base font-semibold text-slate-900 transition hover:bg-slate-200">
                View Saved Trips
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex rounded-2xl bg-slate-950 px-6 py-4 text-base font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Starting trip..." : "Start Trip"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
