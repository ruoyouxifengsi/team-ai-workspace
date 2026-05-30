import {
  Anchor, Button, Container, Group, PasswordInput, Progress, Stack, Text, Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  clearPersonalKey, getSettings, setPersonalKey, type MeSettings,
} from "../api/settings";

export default function SettingsPage() {
  const [s, setS] = useState<MeSettings | null>(null);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    setS(await getSettings());
  }
  useEffect(() => { reload(); }, []);

  async function onSave() {
    if (!key.trim()) return;
    setBusy(true);
    try {
      await setPersonalKey(key.trim());
      setKey("");
      await reload();
      notifications.show({ color: "green", message: "已保存个人 key" });
    } catch (e: any) {
      notifications.show({ color: "red", message: e?.message ?? "保存失败" });
    } finally { setBusy(false); }
  }

  async function onClear() {
    if (!confirm("解绑个人 key？后续将回到团队池配额。")) return;
    setBusy(true);
    try {
      await clearPersonalKey();
      await reload();
      notifications.show({ color: "green", message: "已解绑" });
    } catch (e: any) {
      notifications.show({ color: "red", message: e?.message ?? "解绑失败" });
    } finally { setBusy(false); }
  }

  if (!s) return <Container py="lg"><Text>加载中…</Text></Container>;
  const pct = s.daily_token_quota > 0
    ? Math.min(100, Math.round((s.daily_token_used / s.daily_token_quota) * 100))
    : 0;

  return (
    <Container py="lg" size="sm">
      <Stack>
        <Group justify="space-between">
          <Title order={3}>个人设置</Title>
          <Anchor component={Link} to="/workspace" size="sm">返回工作台</Anchor>
        </Group>

        <Stack gap="xs">
          <Title order={5}>今日用量</Title>
          <Text size="sm">
            {s.daily_token_used.toLocaleString()} / {s.daily_token_quota.toLocaleString()} tokens
          </Text>
          <Progress value={pct} />
          <Text size="xs" c="dimmed">每天北京时间 4:00 自动重置</Text>
        </Stack>

        <Stack gap="xs">
          <Title order={5}>DeepSeek 个人 Key</Title>
          <Text size="sm" c="dimmed">
            绑定个人 key 后，对话调用走你自己的 DeepSeek 账户，不占团队池配额。
          </Text>
          <Text size="sm">当前状态：{s.has_personal_key ? "已绑定" : "未绑定（使用团队池）"}</Text>
          <PasswordInput
            value={key}
            onChange={(e) => setKey(e.currentTarget.value)}
            placeholder="sk-..."
          />
          <Group>
            <Button onClick={onSave} loading={busy} disabled={!key.trim()}>保存</Button>
            {s.has_personal_key && (
              <Button color="red" variant="light" onClick={onClear} disabled={busy}>
                解绑
              </Button>
            )}
          </Group>
        </Stack>
      </Stack>
    </Container>
  );
}
