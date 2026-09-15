# 配置与投递说明

## 目前已经在工作的部分

直接 Gmail 日报由已建立的定时助手任务执行：每天北京时间 10:00 开始研究，完成后发送本人。仓库提供可维护的开源代码，但不会自动取得 Gmail 授权或 ChatGPT 的模型额度。

仓库中不保存个人收件地址、Gmail 密码或 API 密钥。

## 可选：改用 GitHub 独立发布

此模式产生公开 GitHub Issue，由 GitHub 通知系统发邮件。它与直接 Gmail 邮件是两种不同的交付方式。只发布公开科技内容。

1. 在仓库 **Settings → Secrets and variables → Actions → Secrets** 添加 `OPENAI_API_KEY`。可用 `OPENAI_MODEL` Secret 覆盖默认模型；该模型必须对自己的 API 账号可用。不要把密钥粘贴进代码、Issue 或聊天。
2. 新 fork 的 Actions 可能需要在 **Actions** 页面手动启用。仓库还需要启用 Issues。
3. 在 **Actions → 科技与AI Top 5 → Run workflow** 人工运行一次。检查生成文本、日期、来源、公开 Issue 及通知邮箱；这次会真实调用模型并可能产生 API 费用。
4. 通过仓库 **Watch → Custom → Issues** 订阅，并确认 GitHub 通知邮箱指向所需邮箱。对自己触发的活动是否收邮件取决于 GitHub 个人通知设置，必须用实收邮件验收，不能只看 Issue 创建成功。
5. 确认替换现有投递任务后，在 **Variables** 添加 `ENABLE_GITHUB_DIGEST=true`，并停用原有同主题日报任务。不要在两边都发相同内容的情况下直接打开。

默认定时为 `0 10 * * *`，时区 `Asia/Shanghai`。任务可能排队或因来源/API 不可用而失败；这不是精确到达时间保证。

本次未读取或写入仓库 Secrets，也未启动付费模型运行。配置完成与真实投递成功应分别验证。

## 本地候选与审核

```bash
uv sync --locked
uv run python src/main.py --candidates-only
uv run python src/main.py --apply-decisions digest-decisions.json
```

候选快照保留上游的 `snapshot_id` 绑定和逐条 disposition 校验。中文事实与阅读标签字段写入每个保留 cluster，见 [编辑标准](editorial-policy.md)。执行顺序和错误处理沿用 [AGENTS.md](../AGENTS.md)。成功后同时生成 `news.md` 和 `news.html`，可直接在浏览器打开 HTML 预览手机邮件。验证失败会清除旧版 Markdown 与 HTML。

如需发布至 Issue，遵循 AGENTS.md 的身份预检查与 `--dispatch-publish` 路径；它需要已授权的本地 `gh` 或工作流派发权限的 token。连接在助手中的 GitHub 工具不等于本地命令已经有 GitHub token。

## 已知限制

- RSS 不能覆盖所有重要事件，尤其中国厂商与监管原文；定时研究助手需主动补查。
- 仓库模型路径根据摘要生成，事实仍需核验；页面显式标记该限制。
- 代码进行同批去重与同日 Issue 预检，没有跨日语义去重数据库。现有 Gmail 任务通过检索七天邮件补充。
- 本仓库未集成 SMTP 或 Gmail API；不能把 GitHub 通知称作 Gmail 已授权发信。
