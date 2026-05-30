import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";
import FileTree from "../src/components/FileTree";
import * as filesApi from "../src/api/files";

function renderTree() {
  return render(<MantineProvider><FileTree /></MantineProvider>);
}

describe("FileTree", () => {
  it("shows personal and public sections", async () => {
    vi.spyOn(filesApi, "listFiles").mockResolvedValue({
      personal: [{ id: 1, name: "p1.txt", size: 5, mime: "text/plain",
                   uploaded_at: "2026-01-01T00:00:00", is_public: false }],
      public: [{ id: 2, name: "pub.md", size: 5, mime: "text/plain",
                 uploaded_at: "2026-01-01T00:00:00", is_public: true }],
    });
    renderTree();
    await waitFor(() => expect(screen.getByText("p1.txt")).toBeInTheDocument());
    expect(screen.getByText("pub.md")).toBeInTheDocument();
    expect(screen.getByText(/我的文件/)).toBeInTheDocument();
    expect(screen.getByText(/公共资料/)).toBeInTheDocument();
  });

  it("shows empty placeholder when no files", async () => {
    vi.spyOn(filesApi, "listFiles").mockResolvedValue({ personal: [], public: [] });
    renderTree();
    await waitFor(() => expect(screen.getAllByText(/暂无文件/)[0]).toBeInTheDocument());
  });
});
