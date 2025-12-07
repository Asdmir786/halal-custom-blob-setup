# Halal Blob SDK (Node/Next.js)

This SDK in `sdk/node/halalBlobClient.ts` is a small, typed client for the PHP-based Halal Blob gateway you deploy from this repository. It works in Node and in Next.js (App Router, Next 15/16).

## Client Overview

- `HalalBlobClientOptions`
  - `baseUrl`: Base URL of the deployed gateway (e.g. `https://blob.yourdomain.com`).
  - `key`: Your gateway auth key (`HALAL_BLOB_KEY`).
  - `fetchImpl?`: Optional `fetch` implementation (defaults to `globalThis.fetch`).

- Public methods
  - `ping()`: Verifies connectivity and auth; returns `{ success, status, php_version, time }`.
  - `uploadFile(file, { folder?, filename? })`: Uploads a file (`Blob | File | Buffer`) to optional `folder` with optional `filename`.
  - `deleteFile(path)`: Deletes a file by its relative path under `blob/`.
  - `listFiles({ folder?, page?, perPage? })`: Lists files in a folder, paginated.

## Usage Example

```ts
import { HalalBlobClient } from './sdk/node/halalBlobClient';

const client = new HalalBlobClient({
  baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
  key: process.env.HALAL_BLOB_KEY!,
});

await client.ping();
```

## Next.js API Routes (App Router)

Below are route handlers you can paste into `app/api/.../route.ts` files.

```ts
// app/api/halal-upload/route.ts
import { NextResponse } from 'next/server';
import { HalalBlobClient } from '@/sdk/node/halalBlobClient';

export async function POST(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
  });

  const formData = await request.formData();
  const file = formData.get('file') as File | null;
  const folder = (formData.get('folder') as string | null) ?? undefined;
  const filename = (formData.get('filename') as string | null) ?? undefined;
  if (!file) return NextResponse.json({ success: false, error: { code: 'NO_FILE', message: 'Missing file' } }, { status: 400 });

  const res = await client.uploadFile(file, { folder, filename });
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

```ts
// app/api/halal-delete/route.ts
import { NextResponse } from 'next/server';
import { HalalBlobClient } from '@/sdk/node/halalBlobClient';

export async function POST(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
  });

  const body = await request.json();
  const path = body?.path as string;
  if (!path) return NextResponse.json({ success: false, error: { code: 'MISSING_PATH', message: 'Missing path' } }, { status: 400 });

  const res = await client.deleteFile(path);
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

```ts
// app/api/halal-list/route.ts
import { NextResponse } from 'next/server';
import { HalalBlobClient } from '@/sdk/node/halalBlobClient';

export async function GET(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.NEXT_PUBLIC_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
  });

  const url = new URL(request.url);
  const folder = url.searchParams.get('folder') ?? undefined;
  const page = url.searchParams.get('page') ? Number(url.searchParams.get('page')) : undefined;
  const perPage = url.searchParams.get('per_page') ? Number(url.searchParams.get('per_page')) : undefined;

  const res = await client.listFiles({ folder: folder ?? undefined, page, perPage });
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

## v0 Prompt Template

Use this prompt to instruct v0 to wire API routes and a minimal dashboard.

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
