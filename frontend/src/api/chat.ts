import { api } from "./client";

export type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string | null;
  created_at: string;
};

export type SendResponse = { assistant_content: string };

export async function listConversations(): Promise<Conversation[]> {
  const { data } = await api.get<Conversation[]>("/chat/conversations");
  return data;
}

export async function createConversation(title?: string): Promise<Conversation> {
  const { data } = await api.post<Conversation>(
    "/chat/conversations",
    title ? { title } : {},
  );
  return data;
}

export async function renameConversation(id: number, title: string): Promise<Conversation> {
  const { data } = await api.put<Conversation>(`/chat/conversations/${id}`, { title });
  return data;
}

export async function deleteConversation(id: number): Promise<void> {
  await api.delete(`/chat/conversations/${id}`);
}

export async function listMessages(id: number): Promise<ChatMessage[]> {
  const { data } = await api.get<ChatMessage[]>(`/chat/conversations/${id}/messages`);
  return data;
}

export async function sendMessage(id: number, content: string): Promise<SendResponse> {
  const { data } = await api.post<SendResponse>(
    `/chat/conversations/${id}/send`,
    { content },
    { timeout: 180000 },
  );
  return data;
}
