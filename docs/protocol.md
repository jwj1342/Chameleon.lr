# Engine Protocol v1

> Part of the [Chameleon.lr documentation](README.md).

The schemas in [`protocol/`](../protocol/) are the contract. UTF-8 JSON files are used for
transport. Photo identifiers are serialized as strings because Lightroom catalog-local IDs
do not have meaning outside the current catalog.

## Request

`schema_version` is currently `1`. `reference` is the active, styled photo and `targets` are
the remaining selected photos. Each photo contains:

- `preview_path`: path to a Lightroom-rendered JPEG reflecting current non-destructive edits.
- `develop_settings`: only supported style controls, never the source file itself.
- `metadata`: capture context that future engines may use.

Options include a blend `strength` in `[0, 1]` and independent exposure/white-balance
adaptation switches. See [`examples/request.example.json`](../examples/request.example.json).

## Response

The engine returns `ok`, `partial`, or `error`, plus one result per successfully fitted target.
Each result has the catalog photo ID, proposed `develop_settings`, and diagnostics. The Lua
client checks schema and request IDs, rejects unknown photos, and applies a strict setting
allowlist before touching the catalog.

Errors use `{ "photo_id": "...", "message": "..." }`. An empty photo ID denotes a request-
level error. The CLI writes responses atomically so Lightroom never reads a partially written
JSON document.

## Versioning

Additive optional fields may be introduced within v1. Any required field change, semantic
change, or setting representation change requires incrementing `schema_version` and retaining
an explicit compatibility path in both clients.
