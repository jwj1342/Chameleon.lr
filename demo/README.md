# Chameleon.lr MVP Demo

> See the repository [documentation index](../docs/README.md) and
> [MVP acceptance criteria](../docs/mvp.md) for context.

The demo exercises the real protocol models, feature extractor, adaptive fitting service, and
JSON response without requiring Lightroom Classic.

From the repository root:

```bash
python -m venv .venv
# Activate .venv using the command for your shell, then:
python -m pip install -e './backend[dev]'
python scripts/dev.py demo
```

Open `demo/output/index.html`. The report contains:

- one styled reference and two targets rendered under different synthetic lighting;
- the target-specific exposure, temperature, and tint estimates;
- all proposed allowlisted Lightroom Develop Settings;
- before/after feature-distance measurements;
- the exact protocol `request.json` and `response.json`.

The fitted JPEGs are intentionally labeled as approximations. Pillow cannot reproduce Adobe
Camera Raw's rendering pipeline, so the JSON sliders remain the authoritative plugin output.
