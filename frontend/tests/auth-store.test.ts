import { describe, expect, it, beforeEach } from "vitest";
import { useAuth } from "../src/store/auth";

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuth.getState().clear();
  });

  it("starts logged out", () => {
    expect(useAuth.getState().token).toBeNull();
    expect(useAuth.getState().user).toBeNull();
  });

  it("setSession persists to localStorage", () => {
    useAuth.getState().setSession("tok", { id: 1, username: "a", role: "admin" });
    expect(localStorage.getItem("auth.token")).toBe("tok");
    expect(JSON.parse(localStorage.getItem("auth.user")!)).toEqual({ id: 1, username: "a", role: "admin" });
  });

  it("clear removes from store and storage", () => {
    useAuth.getState().setSession("tok", { id: 1, username: "a", role: "admin" });
    useAuth.getState().clear();
    expect(useAuth.getState().token).toBeNull();
    expect(localStorage.getItem("auth.token")).toBeNull();
  });
});
