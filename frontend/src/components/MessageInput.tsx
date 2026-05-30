import { Button, Group, Textarea } from "@mantine/core";
import { useState, type KeyboardEvent } from "react";

type Props = {
  onSend: (text: string) => void;
  busy?: boolean;
};

export default function MessageInput({ onSend, busy = false }: Props) {
  const [text, setText] = useState("");
  const disabled = busy || text.trim().length === 0;

  function fire() {
    if (disabled) return;
    onSend(text.trim());
    setText("");
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      fire();
    }
  }

  return (
    <Group gap="sm" align="flex-end" wrap="nowrap">
      <Textarea
        value={text}
        onChange={(e) => setText(e.currentTarget.value)}
        onKeyDown={onKey}
        placeholder="输入消息… (Cmd/Ctrl+Enter 发送, Shift+Enter 换行)"
        autosize
        minRows={2}
        maxRows={8}
        style={{ flex: 1 }}
        disabled={busy}
      />
      <Button onClick={fire} disabled={disabled} loading={busy}>
        发送
      </Button>
    </Group>
  );
}
