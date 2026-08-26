# Architecture

> Part of the [Chameleon.lr documentation](README.md).

Chameleon.lr is split into a Lightroom Classic plug-in and a local Python process. The
boundary is deliberately a versioned JSON protocol, so the image model can evolve without
coupling it to Lightroom's embedded Lua runtime.

```text
Lightroom selection
       |
       v
Lua workflow -- JPEG previews + current settings --> request.json
       |                                               |
       | LrTasks.execute                               v
       |                                      Python feature engine
       |                                               |
       v                                               v
catalog write transaction <-- allowlist + validation -- response.json
       |
       v
photo:applyDevelopSettings (undoable, non-destructive)
```

## Lightroom plug-in

- `ApplyAdaptiveStyle.lua` is the thin menu entry point.
- `modules/Workflow.lua` owns orchestration and the catalog write transaction.
- `modules/PhotoService.lua` captures rendered JPEG previews and metadata.
- `modules/EngineClient.lua` is the replaceable transport adapter. The initial transport is
  a foreground CLI invocation with per-run files in the OS temporary directory.
- `modules/DevelopSettings.lua` is the trust boundary. Only style-related settings are sent
  to and accepted from the engine; crop, transform, retouch, masks, detail, and lens settings
  are intentionally excluded.
- `modules/Json.lua` avoids a system Lua dependency and stays compatible with Lua 5.1.

The active photo is the reference. Every other selected photo is a target. All preview work
runs in an asynchronous Lightroom task. Results are applied in one `withWriteAccessDo`
transaction so an error rolls back catalog writes and the edit appears in Lightroom history.

## Python engine

- `models.py` validates the wire request.
- `features.py` reduces previews to normalized luminance, clipping, saturation, and RGB
  statistics.
- `algorithm.py` is an interpretable baseline and the intended model extension point.
- `settings.py` contains the authoritative outbound setting policy.
- `service.py` allows partial success when one target preview is unreadable.
- `cli.py` performs atomic response writes.

The current baseline copies the reference's tone, HSL, curve, and color-grading controls,
then estimates per-target exposure and white-balance corrections from rendered-preview
statistics. A learned model can replace `AdaptiveStyleEngine` while preserving the protocol,
validation, UI, and catalog transaction layers.

## Operational choices

The CLI transport is the default because it has no daemon lifecycle, stale-port, or protocol
framing failure modes. A future socket transport should implement the same request/response
objects and add authentication, request size limits, timeouts, and process supervision.

Preview files and JSON artifacts are deleted after each run by default. Enabling
`Keep temporary...` in Plug-in Manager retains them for diagnosis; those files can contain
image previews and metadata and should be handled as private data.
