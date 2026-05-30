import { Button, Container, Paper, PasswordInput, TextInput, Title, Text } from "@mantine/core";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../store/auth";

export default function LoginPage() {
  const setSession = useAuth((s) => s.setSession);
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const { token, user } = await login(username, password);
      setSession(token, user);
      navigate("/workspace");
    } catch {
      setErr("登录失败，请检查用户名密码");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Container size={420} my={80}>
      {/* Branding placeholder — replace with your team's name. */}
      <Title order={2} ta="center">实践团 AI 工作台</Title>
      <Paper withBorder shadow="sm" p={24} mt={24}>
        <form onSubmit={onSubmit}>
          <TextInput label="用户名" value={username} onChange={(e) => setUsername(e.currentTarget.value)} required />
          <PasswordInput label="密码" mt="md" value={password} onChange={(e) => setPassword(e.currentTarget.value)} required />
          {err && <Text c="red" mt="sm">{err}</Text>}
          <Button fullWidth mt="lg" type="submit" loading={busy}>登录</Button>
        </form>
      </Paper>
    </Container>
  );
}
