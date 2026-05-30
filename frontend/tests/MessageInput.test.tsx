import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MessageInput from "../src/components/MessageInput";

function renderWith(props: { onSend: (text: string) => void; busy?: boolean }) {
  return render(
    <MantineProvider>
      <MessageInput {...props} />
    </MantineProvider>,
  );
}

describe("MessageInput", () => {
  it("sends text on click and clears", () => {
    const onSend = vi.fn();
    renderWith({ onSend });
    const ta = screen.getByPlaceholderText(/输入/) as HTMLTextAreaElement;
    fireEvent.change(ta, { target: { value: "hello" } });
    fireEvent.click(screen.getByRole("button", { name: /发送/ }));
    expect(onSend).toHaveBeenCalledWith("hello");
    expect(ta.value).toBe("");
  });

  it("sends on Cmd+Enter", () => {
    const onSend = vi.fn();
    renderWith({ onSend });
    const ta = screen.getByPlaceholderText(/输入/) as HTMLTextAreaElement;
    fireEvent.change(ta, { target: { value: "k" } });
    fireEvent.keyDown(ta, { key: "Enter", metaKey: true });
    expect(onSend).toHaveBeenCalledWith("k");
  });

  it("does not send when busy", () => {
    const onSend = vi.fn();
    renderWith({ onSend, busy: true });
    fireEvent.change(screen.getByPlaceholderText(/输入/), {
      target: { value: "x" },
    });
    fireEvent.click(screen.getByRole("button", { name: /发送/ }));
    expect(onSend).not.toHaveBeenCalled();
  });
});
