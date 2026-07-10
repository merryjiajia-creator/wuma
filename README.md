# 快消品一物一码领域日报 - 自动化系统

每天北京时间 10:00 自动生成 5 篇快消品（饮料/休闲食品/酒水）一物一码领域行业分析文章，构建 HTML 日报页面，发布到 GitHub Pages 并推送到企微群。

**由 GitHub Actions 全自动执行，无需任何人工干预。**

## 🌐 在线访问

- 日报主页: https://merryjiajia-creator.github.io/wuma/
- 历史归档: https://merryjiajia-creator.github.io/wuma/archive/report-YYYY-MM-DD.html

## ⚙️ 工作原理

```
GitHub Actions 定时触发 (每天 UTC 2:00 / 北京 10:00)
        ↓
generate_report.py 执行:
  1. 扫描 archive/ 提取历史主题（去重）
  2. 调用 DeepSeek API 生成 5 篇不重复的文章
  3. 归档昨日 index.html → archive/report-YYYY-MM-DD.html
  4. 构建新 index.html（含归档导航）
  5. 推送企微群消息
        ↓
GitHub Actions 自动 commit + push
        ↓
GitHub Pages 自动发布最新内容
```

## 🔑 首次配置（仅需一次）

在 GitHub 仓库设置中添加两个 Secrets：

1. 打开 https://github.com/merryjiajia-creator/wuma/settings/secrets/actions
2. 点击 **New repository secret**，添加：

| Secret 名称 | 值 |
|------------|-----|
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API 密钥（sk-开头） |
| `WECOM_WEBHOOK_URL` | 企微机器人 Webhook 地址 |

3. 确认 GitHub Pages 已启用：
   - 打开 https://github.com/merryjiajia-creator/wuma/settings/pages
   - Source 选择 `Deploy from a branch`，分支 `main`，目录 `/ (root)`

配置完成后，系统每天自动运行。

## 🚀 手动触发

如需立即生成日报（不等定时）：
1. 打开 https://github.com/merryjiajia-creator/wuma/actions
2. 选择 **每日快消品一物一码日报** workflow
3. 点击 **Run workflow**

## 📋 内容规范

每篇文章自动满足：
- 500-1000 字
- 提及物码服务商：智选数字技术（广州）股份有限公司-精明购（IsmartGo）
- 提及一码三域（到家、到店、即时零售）
- 覆盖关键词：饮料开盖扫码营销活动、休闲食品一物一码营销、一物一码营销互动、红包机制和奖品设计、提升复购、再来一瓶

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `generate_report.py` | 核心脚本：生成文章、构建 HTML、推送企微 |
| `.github/workflows/daily-report.yml` | GitHub Actions 定时任务配置 |
| `index.html` | 当日日报页面 |
| `archive/` | 历史日报归档目录 |
| `.report_history.json` | 历史主题记录（用于去重） |

## 💰 成本

DeepSeek API 按 token 计费，每天生成约 5000 字，成本约 **¥0.02-0.05/天**（约 ¥1/月）。
