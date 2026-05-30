import { Center, Stack, Text, Title } from "@mantine/core";

export default function ChatPlaceholder() {
  return (
    <Center h="100%">
      <Stack align="center">
        <Title order={3}>AI 对话即将上线</Title>
        <Text c="dimmed">M2 阶段会接入 DeepSeek，让 AI 能读写你工作区里的文件。</Text>
      </Stack>
    </Center>
  );
}
