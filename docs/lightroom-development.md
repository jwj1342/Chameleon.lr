# Lightroom Classic Development Notes

> Part of the [Chameleon.lr documentation](README.md).

The plug-in targets Lightroom Classic SDK 6.0 or newer because
`photo:applyDevelopSettings` first appeared in SDK 6. The implementation was checked against
the Lightroom Classic 14.3 SDK reference and official sample plug-ins.

## SDK constraints reflected in the code

- `getDevelopSettings`, `getRawMetadata`, and `requestJpegThumbnail` are called from an
  `LrTasks` asynchronous task.
- Thumbnail requests are callback-based, and the request object remains referenced until the
  callback fires.
- `LrTasks.execute` blocks only the cooperative task, not Lightroom's entire UI thread.
- Catalog updates run in `withWriteAccessDo`, giving rollback behavior and a named undo step.
- Adobe labels the develop-settings table experimental. The plugin therefore carries an
  explicit allowlist and versioned protocol instead of blindly round-tripping every field.
- The Mac App Store build of Lightroom can prevent child process execution because of sandbox
  inheritance. Use Adobe's regular Creative Cloud distribution when invoking a local engine.

## Install and debug

1. Activate a Python 3.10+ virtual environment and run
   `python -m pip install -e './backend[dev]'`.
2. Open Lightroom Classic's Plug-in Manager and add `plugin/Chameleon.lrplugin`.
3. In the Chameleon.lr section, choose `Python script (development)`, verify the Python
   executable and engine script paths, then use `Test Engine`.
4. In Library, make an edited photo active, multi-select its target photos, and choose
   `Library > Plug-in Extras > Apply Adaptive Style...`.

The default engine script path works while the repository layout is intact. A packaged release
must extract the matching engine archive, choose `Standalone executable`, and set its absolute
path in Plug-in Manager. Lua logs are written through `LrLogger` to Lightroom's normal plug-in
log location.

The repository does not require an HPC environment. Use `python scripts/dev.py doctor` to
diagnose Python, engine, and optional Lua tools on Windows, macOS, or Linux. See the
[portability guide](portability.md) for shell and path differences.

Local loading through Plug-in Manager does not use an Adobe API credential. An Adobe account is
needed to obtain the official SDK, while any future Adobe Marketplace distribution process is a
separate release concern. The repository does not currently automate Marketplace submission.

## Sources

- [Adobe Lightroom Classic developer entry](https://developer.adobe.com/lightroom-classic/)
- [Adobe Lightroom Classic SDK download entry](https://developer.adobe.com/console/servicesandapis/lr)
- [Lua 5.1 reference manual](https://www.lua.org/manual/5.1/manual.html)

The downloadable SDK is the authoritative source for `Info.lua` keys, API signatures, and
sample code. Re-check it when raising `LrSdkVersion` or expanding the develop-setting allowlist.
