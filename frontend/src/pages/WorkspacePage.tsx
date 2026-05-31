import { AppShell, Burger, Button, Group, ScrollArea, Stack, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";
import {
  createConversation,
  deleteConversation,
  listConversations,
  renameConversation,
  type Conversation,
} from "../api/chat";
import ChatPane from "../components/ChatPane";
import ConversationList from "../components/ConversationList";
import FileTree from "../components/FileTree";
import FileUploadButton from "../components/FileUploadButton";
import { useAuth } from "../store/auth";

export default function WorkspacePage() {
  const [opened, { toggle }] = useDisclosure();
  const user = useAuth((s) => s.user);
  const clear = useAuth((s) => s.clear);
  const navigate = useNavigate();

  const [convs, setConvs] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [fileReloadKey, setFileReloadKey] = useState(0);

  async function loadConvs() {
    const list = await listConversations();
    setConvs(list);
    if (activeId == null && list.length > 0) setActiveId(list[0].id);
  }

  useEffect(() => { loadConvs(); /* eslint-disable-next-line */ }, []);

  async function onCreate() {
    const c = await createConversation();
    await loadConvs();
    setActiveId(c.id);
  }

  async function onDelete(id: number) {
    await deleteConversation(id);
    if (activeId === id) setActiveId(null);
    await loadConvs();
  }

  async function onRename(id: number, title: string) {
    await renameConversation(id, title);
    await loadConvs();
  }

  async function onLogout() {
    try { await logout(); } catch { /* ignore */ }
    clear();
    navigate("/login");
  }

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 240, breakpoint: "sm", collapsed: { mobile: !opened } }}
      aside={{ width: 220, breakpoint: "md", collapsed: { mobile: true, desktop: false } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            {/* Branding placeholder — replace with your team's name. */}
            <Text fw={600}>实践团 AI 工作台</Text>
          </Group>
          <Group>
            <Button size="xs" variant="subtle" component={Link} to="/settings">设置</Button>
            {user?.role === "admin" && (
              <>
                <Button size="xs" variant="subtle" component={Link} to="/admin/users">用户管理</Button>
                <Button size="xs" variant="subtle" component={Link} to="/admin/feedback">反馈</Button>
              </>
            )}
            <Text size="sm">{user?.username}</Text>
            <Button size="xs" variant="subtle" onClick={onLogout}>退出</Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm">
        <Stack h="100%" gap="sm">
          <Group justify="space-between">
            <Text fw={600}>文件</Text>
            <FileUploadButton onUploaded={() => setFileReloadKey((k) => k + 1)} />
          </Group>
          <ScrollArea style={{ flex: 1 }}>
            <FileTree key={fileReloadKey} />
          </ScrollArea>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Aside p="sm">
        <Text fw={600} mb="xs">会话</Text>
        <ConversationList
          items={convs}
          activeId={activeId}
          onSelect={setActiveId}
          onCreate={onCreate}
          onDelete={onDelete}
          onRename={onRename}
        />
      </AppShell.Aside>

      <AppShell.Main>
        <ChatPane
          conversationId={activeId}
          onFilesPossiblyChanged={() => setFileReloadKey((k) => k + 1)}
        />
      </AppShell.Main>
    </AppShell>
  );
}
