import { api } from "./client";

export type AdminUser = { id: number; username: string; role: string; daily_token_used: number };

export async function listAdminUsers() {
  const { data } = await api.get<AdminUser[]>("/admin/users");
  return data;
}

export async function createAdminUser(payload: { username: string; password: string; role: "admin" | "member" }) {
  const { data } = await api.post<AdminUser>("/admin/users", payload);
  return data;
}

export async function deleteAdminUser(id: number) {
  await api.delete(`/admin/users/${id}`);
}

export async function resetPassword(id: number, password: string) {
  await api.put(`/admin/users/${id}/password`, { password });
}
