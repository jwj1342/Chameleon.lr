# 参与贡献

感谢你帮助改进 Chameleon.lr。项目仍处于 MVP 阶段，当前最有价值的贡献是：可复现的失败
样例、清晰的测试、对 Lightroom SDK 边界的验证，以及有数据支持的算法改进。

参与前请阅读[项目定义](docs/project-definition.md)和[社区行为准则](CODE_OF_CONDUCT.md)。
安全问题不要提交公开 Issue，请按[安全策略](SECURITY.md)报告。

## 开始之前

- Bug 和明确的小修复可以直接提交 Pull Request。
- 新滑杆、协议破坏性变更、较大的 UI/算法方案建议先开 Issue，确认范围和验收方式。
- 不确定是使用问题还是缺陷时，先查看[支持指南](SUPPORT.md)。
- 不要上传未经授权的照片、Catalog、完整 EXIF、用户名路径或保留的临时请求。

## 本地开发

```bash
python -m venv .venv
# 激活环境后：
python scripts/dev.py bootstrap
python scripts/dev.py doctor --strict
python scripts/dev.py test
python scripts/dev.py lint
```

`scripts/dev.py` 不依赖 Make 或 POSIX Shell，可在 Windows、macOS、Linux 和 HPC 使用。
环境安装、平台差异和分模块变更清单见[开发指南](docs/development.md)与
[跨平台说明](docs/portability.md)。不具备 Lightroom 环境时仍可贡献后端、Mock 测试和
文档，但 PR 中必须明确真实 Host Gate 未运行。

## 变更原则

### 保持插件与引擎边界可验证

JSON Schema 是 Lua 与 Python 的合同。新增必填字段、语义变化或设置表示变化必须提升
`schema_version`，并提供明确的兼容或拒绝路径。不要依赖未写入 Schema 的隐式字段。

### Develop Settings 需要双侧更新

新增或修改滑杆时，必须同时更新：

- `backend/src/chameleon_engine/settings.py`
- `plugin/Chameleon.lrplugin/modules/DevelopSettings.lua`
- `protocol/` 中的 JSON Schema
- `examples/` 中的请求/响应样例
- Python 与 Lua 的类型、范围和未知字段测试

裁剪、Transform、修复、蒙版、Detail 和 Lens 设置不在当前风格迁移范围内。

### 算法改动需要证据

至少提供合成边界测试和现有 Demo 指标。真实数据集建立后，算法 PR 还需要报告锁定评测集
上的前后对比，不应只提交挑选后的视觉样例。随机过程必须可复现。

### 文档与行为一起更新

用户流程、命令、协议、支持范围或已知限制变化时，在同一 PR 中更新相关文档和 Changelog。
运行 `python scripts/dev.py metadata` 确认版本和仓库内链接有效。

## Pull Request 要求

一个易于评审的 PR 应当：

1. 解决一个清晰问题，并在描述中说明用户可观察到的变化。
2. 保持改动范围集中，不混入无关格式化或重构。
3. 为新行为添加测试，为无法自动测试的部分提供人工步骤。
4. 说明协议、隐私、性能和 Lightroom 兼容性影响。
5. 列出实际运行的命令；未运行的检查应写明原因。
6. 对 UI 变化附截图，但必须使用合成或已获授权且移除隐私信息的素材。

建议使用简短的命令式提交信息，例如 `fix: reject unknown target ids` 或
`docs: clarify Lightroom host gate`。项目不要求压缩为单个提交，维护者可能在合并时 Squash。

## 评审与合并

CI 检查 Python、Lua 5.1、SDK Mock、版本同步、文档链接和可运行 Demo。评审重点是行为
正确性、协议兼容、安全边界和测试证据。CI 通过不代表 Lightroom 实机验证已完成；触及
SDK、UI、进程启动或 Catalog 写入的变更必须在合并或发布前完成相应 Host Gate。

维护者可能要求缩小范围、补充失败样例或将实验性方案放在独立分支。提交贡献即表示你有权
按仓库的 [GPL-3.0](LICENSE) 许可证提供相关代码、文档和素材。
