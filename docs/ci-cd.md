# CI/CD and Release Guide

> Part of the [Chameleon.lr documentation](README.md).

Lightroom Classic does not provide a supported headless test runner. The repository therefore
separates deterministic automated checks from a short manual test in the real host application.

## Continuous integration

`.github/workflows/ci.yml` runs for branch pushes and pull requests and is also callable by the
release workflow. It grants read-only repository access and contains four independent job
families:

- `Repository metadata and docs` checks that `VERSION`, the Python package, and `Info.lua`
  agree, then verifies every repository-local Markdown link.
- `Python` runs pytest and Ruff on Ubuntu (Python 3.10/3.12), Windows (3.12), and macOS (3.12).
  Tests generate small image fixtures at runtime, so private photos and large RAW assets are not
  committed.
- `MVP demo artifact` runs the real engine demo and uploads the complete HTML report for review.
- `Lua 5.1 and Lightroom SDK mocks` runs Luacheck, parses every Lua file with Lua 5.1, and runs
  the Lua tests. `tests/lua/LrSDK_Mock.lua` simulates selection, dialogs, progress, catalog write
  access, and Develop Settings application.

The mock verifies application control flow, but it cannot prove SDK compatibility or UI layout.
Protect the default branch in GitHub and require all four CI job families before merging.

## Local checks

```bash
python -m venv .venv
# Activate .venv using the command for your shell, then:
python scripts/dev.py bootstrap
python scripts/dev.py doctor --strict
python scripts/dev.py test
python scripts/dev.py lint
python scripts/dev.py package
```

The cross-platform runner uses `sys.executable`, argument arrays, `pathlib`, and `os.pathsep`; it
does not require Make, Bash, an HPC scheduler, or environment modules. `luacheck` must be
installed separately for the complete lint command. Override nonstandard tool locations with
`CHAMELEON_LUA`, `CHAMELEON_LUAC`, and `CHAMELEON_LUACHECK`. CI uses the official Luacheck
action pinned to a commit SHA.

## Tagged releases

`.github/workflows/release.yml` accepts stable semantic-version tags such as `v0.2.0`. It first
runs the complete CI workflow, then:

1. Uses the tag as the artifact version and updates version fields in the build checkout.
2. Creates a versioned `Chameleon.lrplugin` ZIP.
3. Runs PyInstaller natively on Windows x64, macOS Intel, and macOS Apple Silicon runners.
4. Starts each packaged engine and validates its JSON health response before upload.
5. Publishes all archives and `SHA256SUMS.txt` to a generated GitHub Release.

PyInstaller is not a cross-compiler, so each executable is built on its target operating system.
The workflow uses only the default `GITHUB_TOKEN`; no release secret is required.

Before tagging, keep the source tree itself aligned with the release version:

```bash
python scripts/sync_version.py --version 0.2.0
git add VERSION backend/pyproject.toml backend/src/chameleon_engine/__init__.py \
  plugin/Chameleon.lrplugin/Info.lua
git commit -m "chore: prepare v0.2.0"
git tag -s v0.2.0 -m "Chameleon.lr v0.2.0"
git push origin HEAD v0.2.0
```

The workflow also synchronizes its temporary checkout from the tag, preventing a mislabeled
artifact. It does not push generated version changes back into Git history.

## Manual Lightroom gate

Before publishing a production release, test each supported operating system in Lightroom
Classic using a disposable catalog:

1. Install the plugin ZIP and matching engine archive from the draft or test release.
2. Select `Standalone executable` in Plug-in Manager and run `Test Engine`.
3. Test JPEG and RAW reference/target sets with different exposure and white balance.
4. Verify batch application, partial failures, cancellation, history entries, and Undo.
5. Compare the resulting sliders and rendered output against the stored acceptance baseline.

CI outputs are currently unsigned development artifacts. Public distribution should add Apple
Developer ID signing/notarization and a Windows code-signing certificate before treating the
release job as a production deployment gate.

## Adobe developer registration

Local Lua plugin development and Plug-in Manager loading do not require API credentials in this
architecture because the plugin only uses the local Lightroom SDK and a child process. Download
the current SDK through Adobe's developer resources and keep its license outside this repository.
Adobe Marketplace submission, branding review, and any future cloud APIs are separate processes
and should be added only when distribution requirements are known.

## References

- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [GitHub CLI release commands](https://cli.github.com/manual/gh_release_create)
- [PyInstaller operating mode](https://pyinstaller.org/en/stable/operating-mode.html)
- [Luacheck](https://github.com/lunarmodules/luacheck)
- [Adobe Lightroom Classic developer resources](https://developer.adobe.com/lightroom-classic/)
