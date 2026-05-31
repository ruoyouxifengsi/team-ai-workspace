import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ConversationList from "../src/components/ConversationList";

const sample = [
  { id: 1, title: "first", created_at: "2026-05-30T00:00:00", updated_at: "2026-05-30T00:01:00" },
  { id: 2, title: "second", created_at: "2026-05-30T00:00:00", updated_at: "2026-05-30T00:02:00" },
];

function baseProps(over: Partial<Parameters<typeof renderWith>[0]> = {}) {
  return {
    items: sample,
    activeId: null,
    onSelect: vi.fn(),
    onCreate: vi.fn(),
    onDelete: vi.fn(),
    onRename: vi.fn(),
    ...over,
  };
}

function renderWith(props: any) {
  return render(
    <MantineProvider>
      <ConversationList {...props} />
    </MantineProvider>,
  );
}

describe("ConversationList", () => {
  it("renders titles", () => {
    renderWith(baseProps());
    expect(screen.getByText("first")).toBeInTheDocument();
    expect(screen.getByText("second")).toBeInTheDocument();
  });

  it("calls onSelect on click", () => {
    const onSelect = vi.fn();
    renderWith(baseProps({ onSelect }));
    fireEvent.click(screen.getByText("first"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onCreate when 新建 clicked", () => {
    const onCreate = vi.fn();
    renderWith(baseProps({ items: [], onCreate }));
    fireEvent.click(screen.getByRole("button", { name: /新建/ }));
    expect(onCreate).toHaveBeenCalled();
  });

  it("rename: pencil click swaps to input, Enter commits", () => {
    const onRename = vi.fn();
    renderWith(baseProps({ onRename }));
    const pencils = screen.getAllByTitle("重命名");
    fireEvent.click(pencils[0]);
    const input = screen.getByDisplayValue("first") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "renamed" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onRename).toHaveBeenCalledWith(1, "renamed");
  });

  it("rename: Escape cancels without calling onRename", () => {
    const onRename = vi.fn();
    renderWith(baseProps({ onRename }));
    fireEvent.click(screen.getAllByTitle("重命名")[0]);
    const input = screen.getByDisplayValue("first") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "discarded" } });
    fireEvent.keyDown(input, { key: "Escape" });
    expect(onRename).not.toHaveBeenCalled();
  });

  it("rename: empty title is rejected", () => {
    const onRename = vi.fn();
    renderWith(baseProps({ onRename }));
    fireEvent.click(screen.getAllByTitle("重命名")[0]);
    const input = screen.getByDisplayValue("first") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onRename).not.toHaveBeenCalled();
  });
});
