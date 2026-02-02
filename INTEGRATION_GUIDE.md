# Halal Custom Blob: Integration & AI Guide

This guide is designed for developers and AI Agents (v0, Cursor, GPT, etc.) to quickly understand and integrate the **Halal Custom Blob Setup**.

## 🚀 Core Concept

Halal Custom Blob is a self-hosted, PHP-backed media gateway. It allows you to host your own "blob storage" on commodity cPanel/PHP hosting without the overhead or cost of S3 or specialized blob providers.

- **Storage Path:** `blob/` (default, configurable via `HALAL_BLOB_PATH`)
- **Metadata Path:** `meta/` (shadows blob structure)
- **SDK:** A generated TypeScript client for Next.js/Node.

---

## 🛠 Setup Summary

1. **Deploy:** Upload the generated ZIP to your PHP host.
2. **Config:** Rename `.env-template` to `.env` and set `HALAL_BLOB_KEY`.
3. **URL:** Point a subdomain (e.g., `blob.yourdomain.com`) to the folder.

---

## 🤖 AI Agent Instructions

If you are an AI assisting with this project, follow these patterns:

### 1. SDK Implementation

If the SDK file is not already in your project, create it at `sdk/node/halalBlobClient.ts` with the following content:

```ts
/**
 * Halal Blob Client SDK v1.1.2
 */

declare type Buffer = unknown;

export type HalalBlobClientOptions = {
  baseUrl: string;
  key: string;
  blobPath?: string;
  fetchImpl?: typeof fetch;
};

export type ErrorPayload = {
  success: false;
  error: { code: string; message: string };
};
export type UploadResponse =
  | {
      success: true;
      url: string;
      filename: string;
      path: string;
      meta: {
        size_bytes: number;
        mime_type: string;
        uploaded_at: string;
        folder: string;
        original_name: string;
        client_ip: string;
      };
    }
  | ErrorPayload;
export type DeleteResponse = { success: true } | ErrorPayload;
export type PingResponse =
  | { success: true; status: "ok"; php_version: string; time: string; blob_path: string }
  | ErrorPayload;
export type ListItem = { path: string; url: string; meta?: any };
export type ListResponse =
  | {
      success: true;
      folder: string;
      page: number;
      per_page: number;
      total: number;
      files: ListItem[];
    }
  | ErrorPayload;

export class HalalBlobClient {
  private baseUrl: string;
  private key: string;
  private blobPath: string;
  private fetchImpl: typeof fetch;

  constructor(options: HalalBlobClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.key = options.key;
    this.blobPath = (options.blobPath ?? "blob").replace(/^\/|\/$/g, "");
    this.fetchImpl = options.fetchImpl ?? (globalThis.fetch as typeof fetch);
  }

  async ping(): Promise<PingResponse> {
    const res = await this.fetchImpl(`${this.baseUrl}/api/${this.blobPath}/ping.php`, {
      headers: { "X-Halal-Blob-Key": this.key },
    });
    return res.json();
  }

  async uploadFile(
    file: Blob | File | Buffer,
    options?: { folder?: string; filename?: string }
  ): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file as any);
    if (options?.folder) form.append("folder", options.folder);
    if (options?.filename) form.append("filename", options.filename);
    const res = await this.fetchImpl(`${this.baseUrl}/api/${this.blobPath}/upload.php`, {
      method: "POST",
      headers: { "X-Halal-Blob-Key": this.key },
      body: form,
    });
    return res.json();
  }

  async deleteFile(path: string): Promise<DeleteResponse> {
    const res = await this.fetchImpl(`${this.baseUrl}/api/${this.blobPath}/delete.php`, {
      method: "POST",
      headers: {
        "X-Halal-Blob-Key": this.key,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ path }),
    });
    return res.json();
  }

  async listFiles(options?: {
    folder?: string;
    page?: number;
    perPage?: number;
  }): Promise<ListResponse> {
    const params = new URLSearchParams();
    if (options?.folder) params.set("folder", options.folder);
    if (options?.page) params.set("page", String(options.page));
    if (options?.perPage) params.set("per_page", String(options.perPage));
    const url =
      `${this.baseUrl}/api/${this.blobPath}/list.php` +
      (params.toString() ? `?${params.toString()}` : "");
    const res = await this.fetchImpl(url, {
      headers: { "X-Halal-Blob-Key": this.key },
    });
    return res.json();
  }
}
```

### 2. SDK Initialization

Once the file is created, use it like this:

```ts
import { HalalBlobClient } from "@/sdk/node/halalBlobClient";

const client = new HalalBlobClient({
  baseUrl: process.env.HALAL_BLOB_BASE_URL!,
  key: process.env.HALAL_BLOB_KEY!,
});
```

### 2. API Route Patterns (Next.js App Router)

Create standard handlers for Upload, Delete, and List.

#### Upload Handler

`POST /api/upload`

```ts
const formData = await request.formData();
const file = formData.get("file") as File;
const folder = formData.get("folder") as string; // Optional
const res = await client.uploadFile(file, { folder });
```

#### Delete Handler

`POST /api/delete`

```ts
const { path } = await request.json();
const res = await client.deleteFile(path);
```

### 3. Frontend Integration

Always use `FormData` for uploads. Display files using the `url` returned by the SDK.

---

## 📝 API Specification

### `POST /api/{blobPath}/upload.php`

- **Auth:** `X-Halal-Blob-Key` header.
- **Body:** `multipart/form-data`
  - `file`: The binary file (required).
  - `folder`: Subdirectory under `{blobPath}/` (optional).
  - `filename`: Specific name to use (optional, otherwise random UUID used).

### `POST /api/{blobPath}/delete.php`

- **Auth:** `X-Halal-Blob-Key` header.
- **Body:** `application/json`
  - `{ "path": "folder/filename.ext" }`

### `GET /api/{blobPath}/list.php`

- **Auth:** `X-Halal-Blob-Key` header.
- **Query Params:** `folder`, `page`, `per_page`.

---

## 🧠 v0 / Agent Prompt

**Copy-paste this to v0 or any AI to get a working dashboard:**

> "I have a self-hosted blob storage setup.
>
> 1. First, create a typed client file at `sdk/node/halalBlobClient.ts` using the SDK source code provided in the documentation.
> 2. Create 3 Next.js API routes: `/api/blob/upload` (POST), `/api/blob/delete` (POST), and `/api/blob/list` (GET) using the client.
> 3. Create a 'Media Manager' component that shows a list of uploaded files, allows uploading new ones, and deleting existing ones.
> 4. Use `process.env.HALAL_BLOB_BASE_URL` and `process.env.HALAL_BLOB_KEY` for configuration."

---

## 🔒 Security Best Practices

- Never expose `HALAL_BLOB_KEY` to the client-side/browser.
- Always wrap SDK calls in server-side API routes (Next.js Routes or Server Actions).
- Validate file types and sizes in your API routes before calling the SDK if strict control is needed.
