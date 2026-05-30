import { Anchor, Container, Group, Table, Text, Title } from "@mantine/core";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listFeedback, type FeedbackItem } from "../api/feedback";

export default function AdminFeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[] | null>(null);
  useEffect(() => {
    listFeedback().then(setItems).catch(() => setItems([]));
  }, []);
  if (items === null) return <Container py="lg"><Text>加载中…</Text></Container>;
  return (
    <Container py="lg">
      <Group justify="space-between" mb="md">
        <Title order={3}>用户反馈</Title>
        <Anchor component={Link} to="/workspace" size="sm">返回工作台</Anchor>
      </Group>
      <Table withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>时间</Table.Th>
            <Table.Th>用户 ID</Table.Th>
            <Table.Th>会话</Table.Th>
            <Table.Th>内容</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {items.length === 0 && (
            <Table.Tr><Table.Td colSpan={4}><Text c="dimmed">暂无反馈</Text></Table.Td></Table.Tr>
          )}
          {items.map((f) => (
            <Table.Tr key={f.id}>
              <Table.Td>{new Date(f.created_at).toLocaleString()}</Table.Td>
              <Table.Td>{f.user_id}</Table.Td>
              <Table.Td>{f.conversation_id ?? "—"}</Table.Td>
              <Table.Td><Text style={{ whiteSpace: "pre-wrap" }}>{f.text}</Text></Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Container>
  );
}
