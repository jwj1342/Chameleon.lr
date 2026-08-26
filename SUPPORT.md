# 支持指南

Chameleon.lr 当前是研究原型，不提供商业支持或响应时间保证。提交问题前请确认你使用的是
最新 `main` 或最新正式 Release，并先查看 [README](README.md)、[文档导航](docs/README.md)
和现有 GitHub Issues。

## 在哪里提问

- 可复现的崩溃、错误结果或安装故障：使用 **Bug Report** Issue 模板。
- 新工作流或能力建议：使用 **Feature Request** 模板，并说明用户问题和验收标准。
- 文档不清楚或链接失效：提交 Bug，选择 Documentation 区域。
- 安全或隐私漏洞：不要公开提交，按[安全策略](SECURITY.md)私下报告。

## 提交有效的问题

请提供 Chameleon.lr 提交/版本、操作系统、Lightroom Classic 版本、引擎模式、最小复现步骤、
期望结果和实际结果。最好先运行：

```bash
python scripts/dev.py doctor
python scripts/dev.py test-python
```

只粘贴与问题有关的最小日志。提交前移除用户名、绝对路径、文件名、EXIF、Catalog ID 和
请求/响应中的私人元数据。不要上传原始照片；需要视觉复现时优先使用项目 Demo 或自行制作
的合成图。

## 已知限制

- 当前算法是全局统计基线，不处理局部光照、主体语义和精确相机色彩科学。
- Lightroom 没有官方 Headless Runner，UI 和 Catalog 交互必须实机验证。
- CI Release 产物目前未签名/notarize，操作系统可能显示安全提示。
- Mac App Store 版 Lightroom 的沙箱继承可能阻止插件启动本地引擎。

这些已知边界本身不一定是 Bug；如果你有可复现的新影响或改进方案，仍欢迎提交 Issue。
