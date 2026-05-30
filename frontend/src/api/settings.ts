import { api } from "./client";

export type MeSettings = {
  has_personal_key: boolean;
  daily_token_used: number;
  daily_token_quota: number;
};

export async function getSettings(): Promise<MeSettings> {
  const { data } = await api.get<MeSettings>("/me/settings");
  return data;
}

export async function setPersonalKey(key: string): Promise<void> {
  await api.put("/me/settings/key", { key });
}

export async function clearPersonalKey(): Promise<void> {
  await api.delete("/me/settings/key");
}

export async function setUserQuota(userId: number, quota: number): Promise<void> {
  await api.put(`/admin/users/${userId}/quota`, { daily_token_quota: quota });
}
