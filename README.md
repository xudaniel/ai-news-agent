# 科技与 AI Top 5

Daniel 的中文科技日报。优先 AI，每期最多五个独立事件，分别说明**发生了什么、为什么重要、接下来观察什么**，保留日期与原始来源链接。

基于 [nickzren/ai-news-agent](https://github.com/nickzren/ai-news-agent) 的 MIT 开源项目定制，保留原有采集、去重、候选快照绑定和发布检查。

## 当前交付方式

| 项目 | 状态 |
|---|---|
| 中文 Top 5 代码 | 已配置，默认 `top5-zh` |
| 日报时区 | `Asia/Shanghai`（北京时间） |
| 现有直接 Gmail 日报 | 由独立的定时助手任务负责，每天 10:00 开始研究，完成后发送；不是本仓库执行 |
| GitHub Actions 日报 | 已配置每天 10:00，**默认不自动生成**；需设置 `ENABLE_GITHUB_DIGEST=true` 才运行 |
| 仓库独立生成 | 需自备有效 `OPENAI_API_KEY`；未执行真实模型调用或 GitHub 发布验收 |
| 仓库邮件方式 | 发布 Issue 后通过 GitHub Watch 通知；**没有直接 Gmail/SMTP 发信功能** |

**无需为了现有 Gmail 日报再配置 API 密钥。** 如果之后切换到仓库独立运行，应先完成一次人工触发验收，再明确停用原任务，避免重复投递。GitHub Actions 是定时触发，不能保证邮件恰在 10:00 到达。

[仓库](https://github.com/xudaniel/ai-news-agent) · [配置步骤](docs/setup-zh.md) · [选题与写作要求](docs/editorial-policy.md) · [测试与限制](docs/verification.md)

## 阅读格式

- 最多五条，按实际影响排序；不足五条如实说明。
- 优先 AI，重大芯片、云计算、机器人、网络安全及科技商业事件也可入选。
- 每条包含中文标题、事件日期、报道时间、事实、影响推断、观察点、来源。
- 区分发布预告与正式上线、厂商主张与独立验证。
- 普通 Markdown、白底黑字，适合手机阅读；不依赖复杂表格或大图。

仓库的模型路径使用 RSS 标题和摘要，并不自动打开每篇全文核验，因此正文会明确说明这个证据边界。现有定时助手任务另外进行网页检索和来源核验，也负责查找过去七天的邮件以避免跨日重复。**仓库自身目前只有当次事件去重与同日 Issue 检查，没有跨日语义新闻记忆。**

## 本地使用

```bash
uv sync --locked --extra dev
uv run python src/main.py --candidates-only
# 按 docs/editorial-policy.md 和 AGENTS.md 编写绑定快照的 digest-decisions.json
uv run python src/main.py --apply-decisions digest-decisions.json
```

无需模型密钥即可导出候选或应用已经审核的决策。直接运行 `uv run python src/main.py` 才会调用模型；中文模式缺少密钥会停止，不会用英文标题列表冒充中文精选。

独立 Issue 发布与 GitHub 身份配置见 [setup-zh.md](docs/setup-zh.md)。订阅入口：[Watch / Issues](https://github.com/xudaniel/ai-news-agent/subscription)。

## 开发与兼容

```bash
uv run pytest -q
uv run mypy src
```

原英文列表模式仍可使用：`DIGEST_FORMAT=headlines`。如需完整复现上游英文日期与标题，同时设置 `DIGEST_TIMEZONE=America/New_York` 和 `DIGEST_ISSUE_TITLE_PREFIX=AI Headlines`。已有英文回归测试显式启用此兼容模式，中文默认值另有独立进程测试。

[开发说明](docs/development.md) · [架构](docs/architecture.md) · [自动化执行规范](AGENTS.md)

## License

[MIT](LICENSE)。原作者版权与许可保持不变。
