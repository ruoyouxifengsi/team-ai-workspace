import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "../src/pages/LoginPage";
import * as authApi from "../src/api/auth";

function renderPage() {
  return render(
    <MantineProvider>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </MantineProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders username and password inputs", () => {
    renderPage();
    expect(screen.getByLabelText(/用户名/)).toBeInTheDocument();
    expect(screen.getByLabelText(/密码/)).toBeInTheDocument();
  });

  it("calls login api on submit and persists session", async () => {
    const spy = vi.spyOn(authApi, "login").mockResolvedValue({
      token: "T",
      user: { id: 1, username: "admin", role: "admin" },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText(/用户名/), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText(/密码/), { target: { value: "p" } });
    fireEvent.click(screen.getByRole("button", { name: /登录/ }));
    await waitFor(() => expect(spy).toHaveBeenCalledWith("admin", "p"));
    expect(localStorage.getItem("auth.token")).toBe("T");
  });

  it("shows error on bad credentials", async () => {
    vi.spyOn(authApi, "login").mockRejectedValue(new Error("bad"));
    renderPage();
    fireEvent.change(screen.getByLabelText(/用户名/), { target: { value: "x" } });
    fireEvent.change(screen.getByLabelText(/密码/), { target: { value: "y" } });
    fireEvent.click(screen.getByRole("button", { name: /登录/ }));
    await waitFor(() => expect(screen.getByText(/失败|错误/)).toBeInTheDocument());
  });
});
