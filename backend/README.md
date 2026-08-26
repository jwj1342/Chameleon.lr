# Chameleon Engine

> See the repository [documentation index](../docs/README.md) for architecture, protocol, and
> development guidance.

The engine is a local, deterministic CLI process. Lightroom passes it a JSON request
containing rendered previews, metadata, and current develop settings. The engine writes
one JSON response containing an allowlisted set of proposed settings for each target.

```bash
python -m pip install -e './backend[dev]'
chameleon-engine health --json
chameleon-engine fit --request request.json --output response.json
chameleon-engine demo --output-dir demo/output --force
```

For development without installing the package, use `python backend/chameleon_cli.py`.
After installation, `python -m chameleon_engine` is equivalent to the console script.
