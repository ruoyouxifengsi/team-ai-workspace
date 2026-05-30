import {
  ActionIcon, Button, Group, Modal, PasswordInput, Select, Stack, Table, Text, TextInput, Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconKey, IconTrash } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import {
  createAdminUser, deleteAdminUser, listAdminUsers, resetPassword, type AdminUser,
} from "../api/users";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<AdminUser | null>(null);
  const [form, setForm] = useState({ username: "", password: "", role: "member" as "admin" | "member" });
  const [resetPw, setResetPw] = useState("");

  async function reload() {
    setUsers(await listAdminUsers());
  }
  useEffect(() => { reload(); }, []);

  async function onCreate() {
    try {
      await createAdminUser(form);
      notifications.show({ message: "已创建", color: "green" });
      setCreateOpen(false); setForm({ username: "", password: "", role: "member" });
      reload();
    } catch (e) {
      notifications.show({ message: "创建失败（用户名可能已存在）", color: "red" });
    }
  }

  async function onDelete(u: AdminUser) {
    if (!window.confirm(`确认删除 ${u.username}？`)) return;
    await deleteAdminUser(u.id);
    reload();
  }

  async function onResetPw() {
    if (!resetTarget) return;
    await resetPassword(resetTarget.id, resetPw);
    notifications.show({ message: "密码已重置", color: "green" });
    setResetTarget(null); setResetPw("");
  }

  return (
    <Stack p="md">
      <Group justify="space-between">
        <Title order={3}>用户管理</Title>
        <Button onClick={() => setCreateOpen(true)}>新建账号</Button>
      </Group>
      <Table withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>ID</Table.Th>
            <Table.Th>用户名</Table.Th>
            <Table.Th>角色</Table.Th>
            <Table.Th>操作</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {users.map((u) => (
            <Table.Tr key={u.id}>
              <Table.Td>{u.id}</Table.Td>
              <Table.Td>{u.username}</Table.Td>
              <Table.Td>{u.role}</Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <ActionIcon variant="subtle" onClick={() => setResetTarget(u)}>
                    <IconKey size={16} />
                  </ActionIcon>
                  <ActionIcon variant="subtle" color="red" onClick={() => onDelete(u)}>
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <Modal opened={createOpen} onClose={() => setCreateOpen(false)} title="新建账号">
        <Stack>
          <TextInput label="用户名" value={form.username} onChange={(e) => setForm({ ...form, username: e.currentTarget.value })} />
          <PasswordInput label="密码" value={form.password} onChange={(e) => setForm({ ...form, password: e.currentTarget.value })} />
          <Select label="角色" data={[{ value: "member", label: "队员" }, { value: "admin", label: "管理员" }]}
                  value={form.role} onChange={(v: string | null) => setForm({ ...form, role: (v as "admin" | "member") })} />
          <Button onClick={onCreate}>创建</Button>
        </Stack>
      </Modal>

      <Modal opened={!!resetTarget} onClose={() => setResetTarget(null)} title={`重置 ${resetTarget?.username} 密码`}>
        <Stack>
          <PasswordInput label="新密码" value={resetPw} onChange={(e) => setResetPw(e.currentTarget.value)} />
          <Button onClick={onResetPw}>确认</Button>
        </Stack>
      </Modal>

      {users.length === 0 && <Text c="dimmed">暂无用户</Text>}
    </Stack>
  );
}
