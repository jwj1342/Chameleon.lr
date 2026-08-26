# 开发指南

本指南面向准备修改代码、协议或文档的贡献者。系统背景见[架构](architecture.md)，宿主环境
限制见 [Lightroom 开发说明](lightroom-development.md)，平台差异见
[跨平台说明](portability.md)。

## 环境要求

| 工具 | 用途 | 建议版本 |
| --- | --- | --- |
| Python | 引擎、测试、打包脚本 | 3.10+ |
| Lua / `luac` | 插件 Mock 测试与语法检查 | 5.1 |
| Luacheck | Lua 静态检查 | 1.x |
| Lightroom Classic | UI、SDK 和 Catalog 实机验收 | SDK 6.0+ 对应版本 |

只有修改 Python、文档或纯 Lua 逻辑时，不需要安装 Lightroom。CI 使用合成图片和
`tests/lua/LrSDK_Mock.lua`，不依赖私人照片或 Adobe 软件。

## 初始化环境

```text
git clone https://github.com/jwj1342/Chameleon.lr.git
cd Chameleon.lr

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

激活环境后运行 `python scripts/dev.py bootstrap`。它使用当前 Python 安装开发、测试和本机
打包依赖。然后运行 `python scripts/dev.py doctor` 检查引擎和工具路径。

Lua 5.1 和 Luacheck 请使用操作系统包管理器安装。命令名称可能是 `lua5.1` / `luac5.1`，
也可能是 `lua` / `luac`。非标准位置可通过 `CHAMELEON_LUA`、`CHAMELEON_LUAC`、
`CHAMELEON_LUACHECK` 指定。

## 常用命令

```bash
# 所有可自动运行的单元测试
python scripts/dev.py test

# Python、Lua、语法、版本和文档检查
python scripts/dev.py lint

# 生成无需 Lightroom 的端到端报告
python scripts/dev.py demo

# 从最新 Demo 输出重建 README 预览图
python scripts/dev.py readme-preview

# 构建插件、当前平台引擎和 Python wheel
python scripts/dev.py package
```

`python scripts/dev.py demo` 会覆盖被忽略的 `demo/output/`。README 预览图是版本化文档资产，只有 Demo
视觉内容发生有意义的变化时才应重新生成并提交。

`test-python`、`test-lua`、`lint-python`、`lint-lua` 和 `metadata` 子命令可单独执行。
Makefile 保留为 POSIX/HPC 快捷入口，但所有关键工作流都有不依赖 Make 的 Python 入口。

## 代码边界

- `plugin/Chameleon.lrplugin/` 只负责宿主交互、请求组织、结果验证和 Catalog 写入。
- `backend/src/chameleon_engine/` 负责模型校验、图像特征、拟合和结果生成。
- `protocol/` 是两个运行时之间的正式契约，不应从某一侧“顺便”推断字段。
- `DevelopSettings.lua` 与 `settings.py` 共同构成安全边界；后端返回值不能绕过 Lua 校验。
- 临时预览和请求默认是私密运行时数据，不属于调试 fixture 或提交产物。

## 常见变更清单

### 修改算法或特征

1. 在 `backend/tests/` 添加正常、边界和退化输入测试。
2. 保持确定性；随机算法必须固定种子并记录版本。
3. 运行 Demo，检查两个目标的距离没有回归，并查看生成图像。
4. 更新[算法说明](algorithm.md)中的公式、假设或限制。
5. 如果输出语义变化，评估是否需要协议版本升级。

### 新增 Develop Setting

1. 同时更新 `backend/src/chameleon_engine/settings.py` 和
   `plugin/Chameleon.lrplugin/modules/DevelopSettings.lua`。
2. 明确字段类型、合法范围、混合规则和缺失值行为。
3. 更新请求/响应 Schema 与 `examples/` 中的样例。
4. 添加 Python 范围测试、Lua 拒绝/接受测试和一次端到端协议测试。
5. 在真实 Lightroom 中确认字段名称、处理版本和 Undo 行为。

### 修改 Lua 工作流或 UI

1. 保持 SDK 调用位于 `LrTasks` 异步任务中。
2. Catalog 更新必须通过有名称的 `withWriteAccessDo` 事务。
3. 在 Mock 中覆盖成功、取消、部分失败和引擎错误。
4. 使用一次性 Catalog 完成[人工 Host Gate](mvp.md#manual-lightroom-gate)。

### 修改协议

1. 先更新 JSON Schema 和[协议文档](protocol.md)，再更新两侧实现。
2. 可选字段的添加可以留在 v1；必填字段或语义变化需要新 `schema_version`。
3. 保留明确的旧版本拒绝或兼容路径，不静默猜测。
4. 请求与响应样例、模型测试和 Lua 测试必须同步更新。

## 调试

- 后端先运行 `python scripts/dev.py doctor`，排除版本、安装和入口问题。
- 协议问题可从 `examples/request.example.json` 建立最小复现，不要分享真实临时请求。
- Lightroom 中通过 Plug-in Manager 的 `Test Engine` 检查路径与执行权限。
- 只有排障时启用 `Keep temporary...`；完成后删除其中的预览和元数据。
- Lua 日志写入 Lightroom 的插件日志位置。提交 Issue 前先移除用户名、绝对路径和 EXIF。

## 提交前

```bash
python scripts/dev.py test
python scripts/dev.py lint
git status --short
```

然后按照[贡献指南](../CONTRIBUTING.md)填写 PR 的行为变化、验证结果、协议影响和人工测试
状态。没有 Lightroom 环境不是提交纯算法或文档改动的障碍，但必须明确标注未运行的 Host
Gate。
