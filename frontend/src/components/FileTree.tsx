import { ActionIcon, Group, Stack, Text, Title } from "@mantine/core";
import { IconDownload, IconTrash, IconWorld } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { deleteFile, downloadFile, listFiles, publishFile, type FileItem } from "../api/files";
import { useAuth } from "../store/auth";

export default function FileTree() {
  const user = useAuth((s) => s.user);
  const [personal, setPersonal] = useState<FileItem[]>([]);
  const [pub, setPub] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    try {
      const r = await listFiles();
      setPersonal(r.personal); setPub(r.public);
    } finally { setLoading(false); }
  }

  useEffect(() => { reload(); }, []);

  function Section({ title, items, canDelete, canPublish }: {
    title: string; items: FileItem[]; canDelete: boolean; canPublish: boolean;
  }) {
    return (
      <Stack gap={4}>
        <Title order={5} mt="sm">{title}</Title>
        {items.length === 0 && <Text size="sm" c="dimmed">暂无文件</Text>}
        {items.map((f) => (
          <Group key={f.id} justify="space-between" gap="xs" wrap="nowrap">
            <Text size="sm" truncate>{f.name}</Text>
            <Group gap={4} wrap="nowrap">
              <ActionIcon variant="subtle" size="sm" onClick={() => downloadFile(f.id, f.name)}>
                <IconDownload size={14} />
              </ActionIcon>
              {canPublish && (
                <ActionIcon variant="subtle" color="blue" size="sm"
                  title="发布到公共资料"
                  onClick={async () => {
                    if (!confirm(`把 ${f.name} 移动到公共资料区？此操作不可逆。`)) return;
                    await publishFile(f.id);
                    reload();
                  }}>
                  <IconWorld size={14} />
                </ActionIcon>
              )}
              {canDelete && (
                <ActionIcon variant="subtle" color="red" size="sm"
                  onClick={async () => { await deleteFile(f.id); reload(); }}>
                  <IconTrash size={14} />
                </ActionIcon>
              )}
            </Group>
          </Group>
        ))}
      </Stack>
    );
  }

  if (loading) return <Text size="sm" c="dimmed">加载中…</Text>;
  const isAdmin = user?.role === "admin";
  return (
    <Stack>
      <Section title="我的文件" items={personal} canDelete={true} canPublish={true} />
      <Section title="公共资料" items={pub} canDelete={isAdmin} canPublish={false} />
    </Stack>
  );
}
