# Halal Blob SDK (Node/Next.js)

This SDK in `sdk/node/halalBlobClient.ts` is a small, typed client for the PHP-based Halal Blob gateway you deploy from this repository. It works in Node and in Next.js (App Router, Next 15/16).

## Client Overview

- `HalalBlobClientOptions`

  - `baseUrl`: Base URL of the deployed gateway (e.g. `https://blob.yourdomain.com`).
  - `key`: Your gateway auth key (`HALAL_BLOB_KEY`).
  - `blobPath?`: Optional custom path segment (defaults to `blob`).
  - `fetchImpl?`: Optional `fetch` implementation (defaults to `globalThis.fetch`).

- Public methods
  - `ping()`: Verifies connectivity and auth; returns `{ success, status, php_version, time, blob_path }`.
  - `uploadFile(file, { folder?, filename? })`: Uploads a file (`Blob | File | Buffer`) to optional `folder` with optional `filename`.
  - `deleteFile(path)`: Deletes a file by its relative path under the configured blob path.
- `listFiles({ folder?, page?, perPage? })`: Lists files in a folder, paginated.

## SDK Source Code

Copy this into `sdk/node/halalBlobClient.ts`:

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

## Usage Example

```ts
import { HalalBlobClient } from "./sdk/node/halalBlobClient";

const client = new HalalBlobClient({
  baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
  key: process.env.HALAL_BLOB_KEY!,
  blobPath: process.env.HALAL_BLOB_PATH, // Optional: defaults to 'blob'
});

await client.ping();
```

## Next.js API Routes (App Router)

Below are route handlers you can paste into `app/api/.../route.ts` files.

```ts
// app/api/halal-upload/route.ts
import { NextResponse } from "next/server";
import { HalalBlobClient } from "@/sdk/node/halalBlobClient";

export async function POST(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
    blobPath: process.env.HALAL_BLOB_PATH, // Optional: defaults to 'blob'
  });

  const formData = await request.formData();
  const file = formData.get("file") as File | null;
  const folder = (formData.get("folder") as string | null) ?? undefined;
  const filename = (formData.get("filename") as string | null) ?? undefined;
  if (!file)
    return NextResponse.json(
      { success: false, error: { code: "NO_FILE", message: "Missing file" } },
      { status: 400 }
    );

  const res = await client.uploadFile(file, { folder, filename });
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

```ts
// app/api/halal-delete/route.ts
import { NextResponse } from "next/server";
import { HalalBlobClient } from "@/sdk/node/halalBlobClient";

export async function POST(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
    blobPath: process.env.HALAL_BLOB_PATH, // Optional: defaults to 'blob'
  });

  const body = await request.json();
  const path = body?.path as string;
  if (!path)
    return NextResponse.json(
      {
        success: false,
        error: { code: "MISSING_PATH", message: "Missing path" },
      },
      { status: 400 }
    );

  const res = await client.deleteFile(path);
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

```ts
// app/api/halal-list/route.ts
import { NextResponse } from "next/server";
import { HalalBlobClient } from "@/sdk/node/halalBlobClient";

export async function GET(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
  });

  const url = new URL(request.url);
  const folder = url.searchParams.get("folder") ?? undefined;
  const page = url.searchParams.get("page")
    ? Number(url.searchParams.get("page"))
    : undefined;
  const perPage = url.searchParams.get("per_page")
    ? Number(url.searchParams.get("per_page"))
    : undefined;

  const res = await client.listFiles({
    folder: folder ?? undefined,
    page,
    perPage,
  });
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

## v0 & Agentic AI Usage

This project is optimized for AI integrations. See the [Integration Guide](./INTEGRATION_GUIDE.md) for detailed AI-specific patterns.

### v0 Prompt Template

Use this prompt to instruct v0 to wire API routes and a minimal dashboard:

```
You are building on an existing Next.js 15+ App Router project.
The repo already includes a typed client at sdk/node/halalBlobClient.ts.
Env vars available:
- HALAL_BLOB_BASE_URL (same as NEXT_PUBLIC_BLOB_BASE_URL)
- HALAL_BLOB_KEY

Goals:
1) Implement these API routes using the existing client:
   - POST /api/halal-upload : accepts form-data { file, folder?, filename? }
   - POST /api/halal-delete : JSON body { path }
   - GET  /api/halal-list   : query { folder?, page?, per_page? }

2) Build a simple dashboard page with:
   - File upload form (file input, optional folder, optional filename)
   - Files table (path, url, actions)
   - Delete button per row (calls /api/halal-delete)

Implementation notes:
- Client import: `import { HalalBlobClient } from '@/sdk/node/halalBlobClient';`
- Instantiate client with `baseUrl` and `key` from env vars
- Use `NextResponse.json` for all responses
- Keep UI minimal but functional
- Assume modern TypeScript and App Router conventions
```
