import { Anchor, Paper } from "@mantine/core";
import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import "highlight.js/styles/github.css";
import { triggerDownload } from "../api/files";

type Props = {
  role: "user" | "assistant";
  content: string | null;
};

export default function MessageBubble({ role, content }: Props) {
  const isUser = role === "user";
  const body = content ?? "";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", margin: "0.5rem 0" }}>
      <Paper
        p="sm"
        radius="md"
        withBorder
        style={{
          maxWidth: "85%",
          background: isUser ? "var(--mantine-color-gray-1)" : "white",
        }}
      >
        {isUser ? (
          <div style={{ whiteSpace: "pre-wrap" }}>{body}</div>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            urlTransform={(url) => (url.startsWith("download:") ? url : defaultUrlTransform(url))}
            components={{
              a: ({ href, children }) => {
                if (href && href.startsWith("download:")) {
                  const fileId = Number(href.slice("download:".length));
                  const label = String(
                    Array.isArray(children) ? children.join("") : children ?? `file-${fileId}`,
                  );
                  return (
                    <Anchor
                      component="button"
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        triggerDownload(fileId, label);
                      }}
                    >
                      {label}
                    </Anchor>
                  );
                }
                return (
                  <Anchor href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </Anchor>
                );
              },
            }}
          >
            {body}
          </ReactMarkdown>
        )}
      </Paper>
    </div>
  );
}
