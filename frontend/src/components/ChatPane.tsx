import { Button, ScrollArea, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useEffect, useRef, useState } from "react";
import { listMessages, sendMessage, type ChatMessage } from "../api/chat";
import { submitFeedback } from "../api/feedback";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";

type Props = {
  conversationId: number | null;
  onFilesPossiblyChanged: () => void;
};

export default function ChatPane({ conversationId, onFilesPossiblyChanged }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversationId == null) {
      setMessages([]);
      return;
    }
    listMessages(conversationId).then(setMessages).catch(() => setMessages([]));
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onSend(text: string) {
    if (conversationId == null) return;
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { id: -Date.now(), role: "user", content: text,
        created_at: new Date().toISOString() },
    ]);
    try {
      await sendMessage(conversationId, text);
      const fresh = await listMessages(conversationId);
      setMessages(fresh);
      onFilesPossiblyChanged();
    } catch (e: any) {
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail ?? "未知错误";
      if (status === 429) notifications.show({ color: "red", message: `配额已用完：${detail}` });
      else if (status === 413) notifications.show({ color: "red", message: `内容超长：${detail}` });
      else if (status === 422) notifications.show({ color: "red", message: `AI 卡住了：${detail}` });
      else if (status === 503) notifications.show({ color: "red", message: `AI 暂时无响应，请稍后重试` });
      else notifications.show({ color: "red", message: `发送失败：${detail}` });
    } finally {
      setBusy(false);
    }
  }

  async function onFeedback() {
    const text = prompt("请简单描述问题或建议：");
    if (!text) return;
    try {
      await submitFeedback(text, conversationId);
      notifications.show({ color: "green", message: "反馈已提交，谢谢！" });
    } catch {
      notifications.show({ color: "red", message: "反馈提交失败" });
    }
  }

  if (conversationId == null) {
    return (
      <Stack align="center" justify="center" h="100%">
        <Text c="dimmed">选择左侧会话，或点击「新建」开始</Text>
      </Stack>
    );
  }

  return (
    <Stack h="100%" gap="sm">
      <Stack align="flex-end">
        <Button size="xs" variant="subtle" onClick={onFeedback}>反馈</Button>
      </Stack>
      <ScrollArea style={{ flex: 1 }}>
        {messages.map((m) => (
          <MessageBubble key={m.id} role={m.role} content={m.content} />
        ))}
        <div ref={bottomRef} />
      </ScrollArea>
      <MessageInput onSend={onSend} busy={busy} />
    </Stack>
  );
}
