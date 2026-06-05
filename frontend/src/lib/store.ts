import { create } from "zustand";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  tripId?: number;
};

type PlannerStore = {
  messages: ChatMessage[];
  addMessage: (msg: Omit<ChatMessage, "id">) => void;
  clearMessages: () => void;
};

export const usePlannerStore = create<PlannerStore>((set) => ({
  messages: [
    {
      id: "welcome",
      role: "assistant",
      content: "Where do you want to go? Tell me your destination, dates, and budget — e.g. \"Plan a Goa trip in July for ₹50,000\"",
    },
  ],
  addMessage: (msg) =>
    set((state) => ({
      messages: [...state.messages, { ...msg, id: `${Date.now()}-${Math.random()}` }],
    })),
  clearMessages: () =>
    set({
      messages: [
        {
          id: "welcome",
          role: "assistant",
          content: "Where do you want to go?",
        },
      ],
    }),
}));
