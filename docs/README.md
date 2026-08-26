# Chameleon.lr 文档导航

这里是项目的文档入口。主 README 用于快速了解和体验项目；本目录记录产品边界、技术
决策、协议、开发流程和发布条件。行为、接口或项目范围发生变化时，相关文档应与代码在
同一个 Pull Request 中更新。

## 第一次参与项目

建议按下面的顺序阅读：

1. [项目定义](project-definition.md)：理解用户问题、目标、非目标和设计原则。
2. [MVP 范围与验收](mvp.md)：了解当前已经证明什么，以及还没有证明什么。
3. [系统架构](architecture.md)：建立 Lua 插件、JSON 协议和 Python 引擎的整体认识。
4. [开发指南](development.md)：配置环境、运行检查并完成第一次变更。
5. [跨平台说明](portability.md)：理解 Windows、macOS、Linux 与 HPC 的差异。
6. [贡献指南](../CONTRIBUTING.md)：了解提交、评审和隐私要求。

## 按工作内容查找

| 工作内容 | 先读 | 同时检查 |
| --- | --- | --- |
| 调整特征或拟合算法 | [算法说明](algorithm.md) | Python 测试、Demo 指标、[路线图](roadmap.md) |
| 新增 Develop Setting | [协议](protocol.md) | Lua/Python 双重白名单、Schema、样例和双侧测试 |
| 修改插件 UI 或 Catalog 流程 | [Lightroom 开发](lightroom-development.md) | Lua Mock 测试、实机验收清单 |
| 修改进程调用或 JSON 传输 | [系统架构](architecture.md) | 超时、临时文件、隐私和向后兼容 |
| 排查本地环境或平台差异 | [跨平台说明](portability.md) | `scripts/dev.py doctor` 与三平台 CI |
| 准备版本发布 | [CI/CD](ci-cd.md) | Changelog、版本同步、签名状态、实机矩阵 |
| 规划下一阶段 | [研发路线](roadmap.md) | 数据来源、可衡量指标和退出条件 |

## 文档目录

- [项目定义](project-definition.md)：问题、用户、成功标准、范围与术语。
- [MVP 范围与验收](mvp.md)：当前版本能力、自动验收和人工 Host Gate。
- [系统架构](architecture.md)：模块职责、数据流和关键运行时选择。
- [算法说明](algorithm.md)：当前统计基线、限制和后续评测方向。
- [Engine Protocol v1](protocol.md)：请求、响应、错误与版本兼容规则。
- [开发指南](development.md)：环境、命令、调试和常见变更清单。
- [跨平台说明](portability.md)：普通电脑、CI 与 HPC 的一致入口和平台边界。
- [Lightroom 开发说明](lightroom-development.md)：SDK 限制、加载和实机调试。
- [CI/CD 与发布](ci-cd.md)：自动检查、构建、Tag 发布和 Adobe 注册说明。
- [研发路线](roadmap.md)：Now / Next / Later，以及生产可用的必要条件。

技术文档目前保留英文正文，以便准确对应 SDK/API 名称；产品和协作入口使用中文。新增
文档可选择中文或英文，但同一文件内应保持一致，并保留 API、字段名和命令的原始拼写。

## 维护规则

- 代码行为和文档描述冲突时，PR 不能视为完成。
- 协议、滑杆白名单、用户工作流和发布方式变化必须更新对应文档。
- 新文档应从本页链接，避免形成无法发现的孤立页面。
- 本地运行 `python scripts/dev.py metadata`；CI 会检查所有仓库内 Markdown 链接。
- 不在文档、截图或样例中提交真实照片路径、EXIF 隐私信息、Catalog 内容或临时请求。
