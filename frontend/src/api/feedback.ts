import { api } from "./client";

export type FeedbackItem = {
  id: number;
  user_id: number;
  conversation_id: number | null;
  text: string;
  created_at: string;
};

export async function submitFeedback(text: string, conversationId: number | null = null) {
  await api.post("/feedback", { text, conversation_id: conversationId });
}

export async function listFeedback(): Promise<FeedbackItem[]> {
  const { data } = await api.get<FeedbackItem[]>("/admin/feedback");
  return data;
}
