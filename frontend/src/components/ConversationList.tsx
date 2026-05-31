import { ActionIcon, Button, Group, ScrollArea, Stack, Text, TextInput, UnstyledButton } from "@mantine/core";
import { IconCheck, IconPencil, IconPlus, IconTrash, IconX } from "@tabler/icons-react";
import { useState, type KeyboardEvent } from "react";
import type { Conversation } from "../api/chat";

type Props = {
  items: Conversation[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
  onDelete: (id: number) => void;
  onRename: (id: number, title: string) => void;
};

export default function ConversationList({
  items, activeId, onSelect, onCreate, onDelete, onRename,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");

  function startEdit(c: Conversation) {
    setEditingId(c.id);
    setEditText(c.title);
  }

  function commitEdit() {
    if (editingId == null) return;
    const trimmed = editText.trim();
    if (trimmed) onRename(editingId, trimmed);
    setEditingId(null);
  }

  function cancelEdit() {
    setEditingId(null);
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitEdit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancelEdit();
    }
  }

  return (
    <Stack gap="xs" h="100%">
      <Button leftSection={<IconPlus size={14} />} variant="light" onClick={onCreate}>
        新建
      </Button>
      <ScrollArea style={{ flex: 1 }}>
        <Stack gap={4}>
          {items.length === 0 && <Text size="sm" c="dimmed">还没有会话</Text>}
          {items.map((c) => (
            <Group key={c.id} justify="space-between" gap={4} wrap="nowrap">
              {editingId === c.id ? (
                <>
                  <TextInput
                    value={editText}
                    onChange={(e) => setEditText(e.currentTarget.value)}
                    onKeyDown={onKey}
                    size="xs"
                    autoFocus
                    style={{ flex: 1 }}
                  />
                  <ActionIcon variant="subtle" color="green" size="sm" onClick={commitEdit} title="保存">
                    <IconCheck size={14} />
                  </ActionIcon>
                  <ActionIcon variant="subtle" size="sm" onClick={cancelEdit} title="取消">
                    <IconX size={14} />
                  </ActionIcon>
                </>
              ) : (
                <>
                  <UnstyledButton
                    onClick={() => onSelect(c.id)}
                    style={{
                      flex: 1,
                      padding: "6px 8px",
                      borderRadius: 4,
                      background: c.id === activeId ? "var(--mantine-color-gray-2)" : undefined,
                    }}
                  >
                    <Text size="sm" truncate>{c.title}</Text>
                  </UnstyledButton>
                  <ActionIcon
                    variant="subtle"
                    size="sm"
                    title="重命名"
                    onClick={() => startEdit(c)}
                  >
                    <IconPencil size={14} />
                  </ActionIcon>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    size="sm"
                    onClick={() => {
                      if (confirm(`删除会话「${c.title}」？此操作不可逆。`)) onDelete(c.id);
                    }}
                  >
                    <IconTrash size={14} />
                  </ActionIcon>
                </>
              )}
            </Group>
          ))}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
