import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MessageBubble from "../src/components/MessageBubble";

vi.mock("../src/api/files", () => ({
  triggerDownload: vi.fn().mockResolvedValue(undefined),
}));

function renderWith(role: "user" | "assistant", content: string) {
  return render(
    <MantineProvider>
      <MessageBubble role={role} content={content} />
    </MantineProvider>,
  );
}

describe("MessageBubble", () => {
  it("renders user content as plain text", () => {
    renderWith("user", "hello world");
    expect(screen.getByText("hello world")).toBeInTheDocument();
  });

  it("renders assistant markdown", () => {
    renderWith("assistant", "## Heading\n\nsome **bold**");
    expect(screen.getByRole("heading", { level: 2, name: "Heading" })).toBeInTheDocument();
  });

  it("intercepts download: links and calls triggerDownload", async () => {
    const { triggerDownload } = await import("../src/api/files");
    renderWith("assistant", "see [plan.docx](download:42)");
    const link = screen.getByText("plan.docx");
    fireEvent.click(link);
    expect(triggerDownload).toHaveBeenCalledWith(42, "plan.docx");
  });
});
