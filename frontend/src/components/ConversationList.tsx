import { ActionIcon, Button, Group, ScrollArea, Stack, Text, UnstyledButton } from "@mantine/core";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import type { Conversation } from "../api/chat";

type Props = {
  items: Conversation[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
  onDelete: (id: number) => void;
};

export default function ConversationList({ items, activeId, onSelect, onCreate, onDelete }: Props) {
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
                color="red"
                size="sm"
                onClick={() => {
                  if (confirm(`删除会话「${c.title}」？此操作不可逆。`)) onDelete(c.id);
                }}
              >
                <IconTrash size={14} />
              </ActionIcon>
            </Group>
          ))}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
