from pathlib import Path

def write_sdk(root_path: Path) -> None:
    sdk_dir = root_path / "sdk" / "node"
    sdk_dir.mkdir(parents=True, exist_ok=True)
    content = (
        r"""/**
Usage example (Next.js 15/16):

import { HalalBlobClient } from './sdk/node/halalBlobClient';

const client = new HalalBlobClient({
  baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
  key: process.env.HALAL_BLOB_KEY!,
});

await client.ping();
*/

declare type Buffer = unknown;

export type HalalBlobClientOptions = {
  baseUrl: string;
  key: string;
  fetchImpl?: typeof fetch;
};

export type ErrorPayload = { success: false; error: { code: string; message: string } };
export type UploadResponse = { success: true; url: string; filename: string; path: string; meta: { size_bytes: number; mime_type: string; uploaded_at: string; folder: string; original_name: string; client_ip: string } } | ErrorPayload;
export type DeleteResponse = { success: true } | ErrorPayload;
export type PingResponse = { success: true; status: 'ok'; php_version: string; time: string } | ErrorPayload;
export type ListItem = { path: string; url: string; meta?: any };
export type ListResponse = { success: true; folder: string; page: number; per_page: number; total: number; files: ListItem[] } | ErrorPayload;

export class HalalBlobClient {
  private baseUrl: string;
  private key: string;
  private fetchImpl: typeof fetch;

  constructor(options: HalalBlobClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.key = options.key;
    this.fetchImpl = options.fetchImpl ?? (globalThis.fetch as typeof fetch);
  }

  async ping(): Promise<PingResponse> {
    const res = await this.fetchImpl(`${this.baseUrl}/api/blob/ping.php`, {
      headers: { 'X-Halal-Blob-Key': this.key },
    });
    return res.json();
  }

  async uploadFile(file: Blob | File | Buffer, options?: { folder?: string; filename?: string }): Promise<UploadResponse> {
    const form = new FormData();
    form.append('file', file as any);
    if (options?.folder) form.append('folder', options.folder);
    if (options?.filename) form.append('filename', options.filename);
    const res = await this.fetchImpl(`${this.baseUrl}/api/blob/upload.php`, {
      method: 'POST',
      headers: { 'X-Halal-Blob-Key': this.key },
      body: form,
    });
    return res.json();
  }

  async deleteFile(path: string): Promise<DeleteResponse> {
    const res = await this.fetchImpl(`${this.baseUrl}/api/blob/delete.php`, {
      method: 'POST',
      headers: { 'X-Halal-Blob-Key': this.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return res.json();
  }

  async listFiles(options?: { folder?: string; page?: number; perPage?: number }): Promise<ListResponse> {
    const params = new URLSearchParams();
    if (options?.folder) params.set('folder', options.folder);
    if (options?.page) params.set('page', String(options.page));
    if (options?.perPage) params.set('per_page', String(options.perPage));
    const url = `${this.baseUrl}/api/blob/list.php` + (params.toString() ? `?${params.toString()}` : '');
    const res = await this.fetchImpl(url, { headers: { 'X-Halal-Blob-Key': this.key } });
    return res.json();
  }
}
"""
    )
    (sdk_dir / "halalBlobClient.ts").write_text(content, encoding="utf-8")

