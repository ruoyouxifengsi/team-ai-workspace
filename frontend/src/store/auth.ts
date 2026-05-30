import { create } from "zustand";
import type { AuthUser } from "../api/auth";

type State = {
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  clear: () => void;
};

function loadInitial(): { token: string | null; user: AuthUser | null } {
  const token = localStorage.getItem("auth.token");
  const userRaw = localStorage.getItem("auth.user");
  return { token, user: userRaw ? JSON.parse(userRaw) : null };
}

export const useAuth = create<State>((set) => ({
  ...loadInitial(),
  setSession: (token, user) => {
    localStorage.setItem("auth.token", token);
    localStorage.setItem("auth.user", JSON.stringify(user));
    set({ token, user });
  },
  clear: () => {
    localStorage.removeItem("auth.token");
    localStorage.removeItem("auth.user");
    set({ token: null, user: null });
  },
}));
