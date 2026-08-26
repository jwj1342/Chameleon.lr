# Changelog

本文件记录对用户、贡献者或发布流程有意义的变化。格式参考 Keep a Changelog，版本号遵循
Semantic Versioning。尚未发布的改动保留在 `Unreleased`，发布时再移动到对应版本。

## [Unreleased]

### Added

- Lightroom Lua 插件：参考/目标选择、异步预览、进度、取消与单次 Catalog 写事务。
- 本地 Python 引擎：图像特征、曝光/白平衡适配和白名单 Develop Settings 输出。
- Versioned JSON Protocol v1、Schema、样例与原子请求/响应文件传输。
- Python 单元测试、Lua 5.1 SDK Mock 测试和确定性的可视化 MVP Demo。
- GitHub Actions CI、跨平台引擎打包和 Tag 驱动的 Release 工作流。
- 无 Make/Shell 依赖的跨平台开发入口，以及 Windows/macOS/Linux Python CI 矩阵。
- 项目定义、开发指南、路线图、支持/安全策略和 GitHub 协作模板。

### Security

- Lua 与 Python 双重滑杆白名单，拒绝未知照片和未知 Develop Settings。
- 临时预览与 JSON 默认在运行后清理，诊断保留由用户显式启用。

[Unreleased]: https://github.com/jwj1342/Chameleon.lr/commits/main
