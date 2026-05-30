import { api } from "./client";

export type FileItem = {
  id: number; name: string; size: number; mime: string;
  uploaded_at: string; is_public: boolean;
};

export async function listFiles() {
  const { data } = await api.get<{ personal: FileItem[]; public: FileItem[] }>("/files");
  return data;
}

export async function uploadFile(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const { data } = await api.post<FileItem>("/files", fd);
  return data;
}

export async function deleteFile(id: number) {
  await api.delete(`/files/${id}`);
}

export async function downloadFile(id: number, filename: string) {
  return triggerDownload(id, filename);
}

export async function triggerDownload(id: number, fallbackName?: string): Promise<void> {
  const r = await api.get(`/files/${id}`, { responseType: "blob" });
  let name = fallbackName ?? `file-${id}`;
  const cd = r.headers["content-disposition"] as string | undefined;
  if (cd) {
    const m = /filename="?([^";]+)"?/.exec(cd);
    if (m) name = decodeURIComponent(m[1]);
  }
  const url = URL.createObjectURL(r.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function publishFile(id: number) {
  const { data } = await api.post<FileItem>(`/files/${id}/publish`);
  return data;
}
