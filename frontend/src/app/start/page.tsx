import Link from "next/link";

export default function StartPlanningPage() {
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
              This area is reserved for the trip planning workflow. For now, you can review your saved trips or create a new plan via the backend API.
            </p>
          </div>

          <div className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-8">
            <p className="text-slate-700">
              There is no UI for creating trips yet. To start planning, call the backend endpoints directly or add a trip planner page in the frontend.
            </p>
            <Link
              href="/trips"
              className="inline-flex rounded-2xl bg-slate-950 px-6 py-4 text-center text-base font-semibold text-white transition hover:bg-slate-800"
            >
              View Saved Trips
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
