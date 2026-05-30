import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ConversationList from "../src/components/ConversationList";

const sample = [
  { id: 1, title: "first", created_at: "2026-05-30T00:00:00", updated_at: "2026-05-30T00:01:00" },
  { id: 2, title: "second", created_at: "2026-05-30T00:00:00", updated_at: "2026-05-30T00:02:00" },
];

function renderWith(props: any) {
  return render(
    <MantineProvider>
      <ConversationList {...props} />
    </MantineProvider>,
  );
}

describe("ConversationList", () => {
  it("renders titles", () => {
    renderWith({ items: sample, activeId: null, onSelect: vi.fn(), onCreate: vi.fn(), onDelete: vi.fn() });
    expect(screen.getByText("first")).toBeInTheDocument();
    expect(screen.getByText("second")).toBeInTheDocument();
  });

  it("calls onSelect on click", () => {
    const onSelect = vi.fn();
    renderWith({ items: sample, activeId: null, onSelect, onCreate: vi.fn(), onDelete: vi.fn() });
    fireEvent.click(screen.getByText("first"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onCreate when 新建 clicked", () => {
    const onCreate = vi.fn();
    renderWith({ items: [], activeId: null, onSelect: vi.fn(), onCreate, onDelete: vi.fn() });
    fireEvent.click(screen.getByRole("button", { name: /新建/ }));
    expect(onCreate).toHaveBeenCalled();
  });
});
