# Halal Custom Blob Setup

Self-hosted media gateway for Next.js/v0 on cPanel: PHP endpoints for upload/list/delete, a Python builder to package and ship, and a minimal TypeScript SDK for client integration.

**Status:** 🚀 [AI-Ready] | [📚 Integration Guide (For Humans & AI)](./INTEGRATION_GUIDE.md)

## Why This Exists

- Control: Keep media on your domain (`blob.MYDOMAIN.com`), no vendor lock-in.
- Simplicity: Works on commodity cPanel/PHP hosting with straightforward file storage.
- Reliability: Uploads go directly to the gateway, avoiding Next.js server limits.
- Cost: Cheaper than managed blobs for many use-cases; predictable hosting.

## Architecture Overview

- Python Builder (`build_halal_custom_blob_setup.py` + `src/`)

  - Creates `api/blob/*.php`, `blob/`, `meta/`, `.env-template`, and a setup guide.
  - Zips output into `halal-custom-blob-setup.zip` at repo root.
  - Writes `sdk/node/halalBlobClient.ts` (not included in the ZIP).

- Blob Gateway (PHP endpoints, deploy on cPanel)

  - `upload.php`: Validates auth, size, type, moves file into `blob/`, writes JSON meta.
  - `delete.php`: Deletes a file and its metadata.
  - `list.php`: Lists files in a folder with pagination.
  - `ping.php`: Auth-gated health check.
  - `.htaccess`: Indexes disabled; blocks `.env`/`.ini` and PHP execution in `blob/`.

- TypeScript SDK (`sdk/node/halalBlobClient.ts`)
  - Minimal client for `uploadFile`, `deleteFile`, `listFiles`, `ping`.
  - Works in Node/Next.js; accepts `baseUrl` and `key`.

## ZIP Output Contents

| Path                    | Description                                                   |
| ----------------------- | ------------------------------------------------------------- |
| `api/blob/upload.php`   | Upload endpoint with auth, size/type checks, metadata writing |
| `api/blob/delete.php`   | Delete endpoint removes file and meta                         |
| `api/blob/list.php`     | List files with pagination                                    |
| `api/blob/ping.php`     | Auth-gated health check                                       |
| `api/.htaccess`         | Disables indexes; blocks `.env`/`.ini`                        |
| `blob/.htaccess`        | Disables indexes; blocks PHP execution                        |
| `blob/`                 | Public asset files live here                                  |
| `meta/`                 | JSON metadata mirroring `blob/` folders                       |
| `.env-template`         | Config: `HALAL_BLOB_KEY`, max bytes, allowed types            |
| `How to Setup [EZ].txt` | Deployment and usage guide                                    |

## Installation on cPanel

1. Upload `halal-custom-blob-setup.zip` to your site root or a subfolder.
2. Extract the zip.
3. Rename `.env-template` to `.env`.
   > **Note:** In cPanel File Manager, click **Settings** (top right) and check **"Show Hidden Files (dotfiles)"** if you don't see it!
4. Set `HALAL_BLOB_KEY` to a long random string (64–128 chars).
5. Set `HALAL_BLOB_BASE_URL` to your subdomain URL (e.g., `https://blob.yourdomain.com`).
6. Optionally set `HALAL_BLOB_MAX_BYTES`, `HALAL_BLOB_ALLOWED_EXT`, and `HALAL_BLOB_PATH`.
7. Point subdomain `blob.MYDOMAIN.com` to the extracted folder so public files resolve under `https://blob.MYDOMAIN.com/blob/...` (or your custom path).

## Usage in Next.js / Vercel

- Copy `sdk/node/halalBlobClient.ts` into your Next.js repo (preserve types).
- Import the client and pass environment variables.

Environment variables (Next.js):

- `HALAL_BLOB_BASE_URL` (e.g. `https://blob.yourdomain.com`)
- `HALAL_BLOB_KEY`

Example minimal API route (App Router):

```ts
// app/api/halal-upload/route.ts
import { NextResponse } from "next/server";
import { HalalBlobClient } from "@/sdk/node/halalBlobClient";

export async function POST(request: Request) {
  const client = new HalalBlobClient({
    baseUrl: process.env.HALAL_BLOB_BASE_URL!,
    key: process.env.HALAL_BLOB_KEY!,
  });
  const formData = await request.formData();
  const file = formData.get("file") as File | null;
  if (!file)
    return NextResponse.json(
      { success: false, error: { code: "NO_FILE", message: "Missing file" } },
      { status: 400 }
    );
  const folder = (formData.get("folder") as string | null) ?? undefined;
  const filename = (formData.get("filename") as string | null) ?? undefined;
  const res = await client.uploadFile(file, { folder, filename });
  return NextResponse.json(res, { status: res.success ? 200 : 400 });
}
```

## Security Model

- Auth via `X-Halal-Blob-Key` header; optional `?key=` fallback for testing.
- Secrets are never publicly listed; `.env` is protected by `.htaccess`.
- `blob/` disallows PHP execution to prevent code upload attacks.

## Performance Notes

- Lightweight PHP file handling with direct disk writes.
- Avoids Next.js server payload limits; file transfer goes straight to the gateway.
- Simple architecture reduces overhead and points of failure.

## Versioning

- Current version: `v1.1.2`
- Future directions: presigned URLs, moderation API, quotas, built-in dashboard.

## License

MIT (placeholder).
