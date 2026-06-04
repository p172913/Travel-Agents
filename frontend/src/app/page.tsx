import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16 sm:px-10">
        <div className="rounded-3xl border border-slate-200 bg-white/95 p-10 shadow-xl shadow-slate-200/40">
          <div className="mb-8">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">TravelSouls</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              AI-powered travel planning for modern explorers.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Generate trip plans, research destinations, manage budgets, and review itineraries from a single interface.
              The prototype backend is ready and now the frontend can consume saved trips and plan details.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              href="/trips"
              className="rounded-2xl bg-slate-950 px-6 py-4 text-center text-base font-semibold text-white transition hover:bg-slate-800"
            >
              View Saved Trips
            </Link>
            <Link
              href="/start"
              className="rounded-2xl border border-slate-200 bg-white px-6 py-4 text-center text-base font-semibold text-slate-900 transition hover:bg-slate-50"
            >
              Start Planning
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
