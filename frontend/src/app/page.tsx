import Link from "next/link";

const phases = [
  {
    title: "Recommendations",
    description: "Generate tailored restaurant, activity, and attraction suggestions for your trip.",
    highlight: "Personalized AI suggestions"
  },
  {
    title: "Orchestration",
    description: "Coordinate research, budget, booking, and recommendations into one complete plan.",
    highlight: "Multi-agent planning"
  },
  {
    title: "Itinerary",
    description: "Convert agent outputs into a readable day-by-day travel schedule.",
    highlight: "Daily itinerary builder"
  },
  {
    title: "Explainability",
    description: "Show why each recommendation was chosen so travelers understand the plan.",
    highlight: "Why this plan works"
  }
];

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto max-w-6xl px-6 py-16 sm:px-10">
        <section className="rounded-3xl border border-slate-200 bg-white/95 p-10 shadow-xl shadow-slate-200/40">
          <div className="mb-8">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">TravelSouls</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              AI-powered travel planning for modern explorers.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Generate trip plans, research destinations, manage budgets, and review itineraries from a single interface.
              The prototype backend is ready and the app now supports planning, saved trips, and explainable recommendations.
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
        </section>

        <section className="mt-10">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {phases.map((phase) => (
              <div key={phase.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/20">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-sky-600">{phase.title}</p>
                <h2 className="mt-4 text-xl font-semibold text-slate-950">{phase.highlight}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">{phase.description}</p>
                <Link
                  href="/start"
                  className="mt-6 inline-flex rounded-2xl border border-slate-200 bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  Run phase
                </Link>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
