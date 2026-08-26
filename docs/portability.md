# 跨平台与非 HPC 环境

Chameleon.lr 不依赖 HPC 集群、作业调度器、共享文件系统、Environment Modules 或容器。
一台安装了 Python 3.10+ 的普通 Windows、macOS 或 Linux 电脑就能运行引擎、Demo 和 Python
测试；Lightroom 插件实机测试只需要 Lightroom Classic 支持的 Windows 或 macOS。

## 支持矩阵

| 场景 | Windows | macOS | Linux / HPC |
| --- | --- | --- | --- |
| Python 引擎与测试 | CI 自动验证 | CI 自动验证 | CI 自动验证 |
| Demo 与文档工具 | 支持 | 支持 | 支持 |
| Lightroom Lua 插件实机 | 支持 | 支持 | Lightroom 不提供 Linux 版本 |
| 原生引擎打包 | Windows x64 | Intel 与 Apple Silicon | 开发构建，不作为 Lightroom Release |

常规 Python CI 同时运行 Ubuntu、Windows 和 macOS。Tag Release 进一步在 Windows x64、
macOS Intel 和 macOS Apple Silicon 上原生构建并启动产物。Lua 逻辑在 Lua 5.1 Mock 中测试，
最终 SDK/UI 兼容性仍由真实 Lightroom Host Gate 保证。

## 统一开发入口

`scripts/dev.py` 仅依赖 Python 标准库，不调用 Bash，也不要求安装 Make：

```bash
python scripts/dev.py doctor
python scripts/dev.py test-python
python scripts/dev.py demo
```

完整 Lua 测试和 lint 需要 Lua 5.1、`luac` 与 Luacheck。工具不在 PATH 或名称不同可设置：

```text
CHAMELEON_LUA=/path/to/lua5.1
CHAMELEON_LUAC=/path/to/luac5.1
CHAMELEON_LUACHECK=/path/to/luacheck
```

Windows PowerShell 使用 `$env:CHAMELEON_LUA = 'C:\path\to\lua.exe'` 的形式。`doctor --strict`
会将缺失的测试/静态检查工具视为错误；不带 `--strict` 时，它们作为可选能力列出。

## 路径与临时文件

- Python 使用 `pathlib`、`tempfile`、`os.pathsep` 和参数数组，不拼接 Shell 命令。
- Lightroom 侧使用 `LrPathUtils` 获取系统临时目录和组合路径。
- Lua 调用本地引擎时会对 Windows 和 POSIX 参数分别加引号，并测试包含空格的 Windows 路径。
- 生产请求中的 `preview_path` 由插件写成当前操作系统的绝对路径；协议样例使用平台中立的
  相对路径，仅用于展示数据结构。
- 运行时文件写入系统临时目录并默认删除；仓库本身可以位于包含空格的路径中。

不要假设 `/tmp`、`$HOME`、盘符、路径分隔符或当前工作目录。新增 Python 进程调用应继续
使用参数数组与明确的 `cwd`；新增 Lua 路径应通过 `LrPathUtils` 处理。

## 平台相关限制

- Makefile 是 macOS/Linux/HPC 的快捷方式；Windows 合作者应优先使用 `scripts/dev.py`。
- PyInstaller 不是交叉编译器，必须在目标操作系统和 CPU 架构上构建。
- macOS/Windows 开发产物目前未签名；公开发布前需要签名和 macOS notarization。
- Mac App Store 版 Lightroom 可能因沙箱继承阻止子进程，建议使用 Creative Cloud 版本。
- 文件系统大小写规则不同。代码中的仓库路径和 Lua 模块名必须保持实际大小写。

## 报告平台问题

先运行 `python scripts/dev.py doctor`，然后在 Bug Report 中提供系统、CPU 架构、Python、
Lightroom 版本和失败命令。删除用户名、真实照片路径、EXIF 和 Catalog 信息后再附输出。
