# Changelog

## [1.1.1] - 2025-12-08
- SDK writer now embeds version constant `HALAL_BLOB_SDK_VERSION` from `VERSION`.
- Regenerated `sdk/node/halalBlobClient.ts` to match current client shape.

## [1.1.0] - 2025-12-08
- Modular Python builder split into `src/` modules.
- Added PHP endpoints: `list.php`, `ping.php` alongside `upload.php`, `delete.php`.
- Introduced TypeScript SDK consumed by Next.js/v0.
- Added comprehensive documentation and integration prompt.
- Established semantic versioning with root `VERSION` file.

## [1.0.0] - 2025-12-XX
- Initial release of Halal Custom Blob Setup.
- Basic PHP upload and delete endpoints.
- Simple Python builder that outputs gateway files and ZIP.
- `.env-template` configuration and `.htaccess` protections.
