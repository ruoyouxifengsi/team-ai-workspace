import { Button } from "@mantine/core";
import { useRef } from "react";
import { uploadFile } from "../api/files";

export default function FileUploadButton({ onUploaded }: { onUploaded: () => void }) {
  const ref = useRef<HTMLInputElement>(null);
  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    await uploadFile(f);
    if (ref.current) ref.current.value = "";
    onUploaded();
  }
  return (
    <>
      <input ref={ref} type="file" hidden onChange={onChange} />
      <Button onClick={() => ref.current?.click()} size="xs">上传文件</Button>
    </>
  );
}
