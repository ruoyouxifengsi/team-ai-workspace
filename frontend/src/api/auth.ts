import { api } from "./client";

export type AuthUser = { id: number; username: string; role: "admin" | "member" };

export async function login(username: string, password: string) {
  const { data } = await api.post<{ token: string; user: AuthUser }>("/auth/login", { username, password });
  return data;
}

export async function logout() {
  await api.post("/auth/logout");
}

export async function me() {
  const { data } = await api.get<AuthUser>("/auth/me");
  return data;
}
