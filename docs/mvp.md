# MVP Scope and Acceptance

> Part of the [Chameleon.lr documentation](README.md).

The MVP proves one complete workflow: a photographer selects one edited reference and one or
more targets, Chameleon derives target-specific Develop Settings, and Lightroom applies them as
one undoable, non-destructive catalog operation.

## Included capability

- Lightroom selection, rendered-preview capture, progress/cancel handling, and catalog writes.
- A local Python CLI or packaged executable with atomic versioned JSON I/O.
- Reference style transfer for basic tone, HSL, tone curves, and color grading.
- Per-target exposure and white-balance adaptation from preview features.
- Strict Lua and Python setting allowlists and range validation.
- Batch partial-failure responses and an explicit error when no slider can be produced.
- A self-contained visual demo and machine-readable convergence metrics.
- Python/Lua CI, a downloadable demo artifact, mocked Lightroom control-flow tests, and tagged
  binary releases whose packaged engine reruns the demo as a smoke test.

## Acceptance commands

```bash
python scripts/dev.py test
python scripts/dev.py lint
python scripts/dev.py demo
```

For the generated demo, both targets must have `status: ok`, at least one proposed Develop
Setting, and lower median-luminance and mean-RGB gaps after approximation. These conditions are
enforced by `backend/tests/test_demo.py`.

The final host gate remains manual because Lightroom Classic has no supported headless runner:

1. Add `plugin/Chameleon.lrplugin` in Plug-in Manager and pass `Test Engine`.
2. Use an edited active reference plus at least two targets in a disposable catalog.
3. Apply the style and verify exposure, white balance, tone/HSL, one history entry, and Undo.
4. Repeat with a missing/unreadable target preview and verify partial-failure reporting.

## Deliberate boundaries

This is a feature-based baseline, not a trained color model. The HTML demo's fitted images are a
diagnostic approximation rather than Adobe Camera Raw output. Production readiness additionally
requires a photographer-owned evaluation set, signed/notarized binaries, and host testing across
supported Lightroom/macOS/Windows versions.
