"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { chatPlan } from "@/lib/api";
import { usePlannerStore } from "@/lib/store";

export default function ChatPlannerPage() {
  const router = useRouter();
  const { messages, addMessage } = usePlannerStore();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    if (!input.trim() || loading) return;

    const prompt = input.trim();
    setInput("");
    addMessage({ role: "user", content: prompt });
    setLoading(true);

    try {
      const response = await chatPlan({ prompt });
      addMessage({
        role: "assistant",
        content: `Your trip to ${response.plan?.destination ?? "your destination"} is ready! Trip #${response.trip_id} with plan #${response.plan_id}. Execution took ${Math.round((response.plan?.execution_time_ms as number) || 0)}ms.`,
        tripId: response.trip_id,
      });
      setTimeout(() => router.push(`/trips/${response.trip_id}`), 1500);
    } catch (err) {
      addMessage({
        role: "assistant",
        content: err instanceof Error ? err.message : "Failed to generate plan. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 sm:px-10">
      <div className="mx-auto flex max-w-3xl flex-col rounded-3xl border border-slate-200 bg-white shadow-lg shadow-slate-200/50" style={{ minHeight: "80vh" }}>
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">TravelSouls</p>
            <h1 className="text-xl font-semibold text-slate-950">Trip Planner</h1>
          </div>
          <Link href="/trips" className="text-sm font-semibold text-sky-600 hover:text-sky-700">My trips</Link>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                msg.role === "user"
                  ? "bg-slate-950 text-white"
                  : "border border-slate-200 bg-slate-50 text-slate-800"
              }`}>
                {msg.content}
                {msg.tripId ? (
                  <Link href={`/trips/${msg.tripId}`} className="mt-2 block font-semibold text-sky-600 hover:underline">
                    View trip →
                  </Link>
                ) : null}
              </div>
            </div>
          ))}
          {loading ? (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                Planning your trip…
              </div>
            </div>
          ) : null}
        </div>

        <form onSubmit={handleSend} className="border-t border-slate-200 px-6 py-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Where do you want to go?"
              className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-sky-400"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
