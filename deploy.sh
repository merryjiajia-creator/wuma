#!/bin/bash
# 自动部署脚本 - 推送日报到 GitHub Pages
# 用法: bash deploy.sh "commit message"
# 依赖: 本地 ./bin/gh.exe 已通过 gh auth login 授权（凭证持久保存在系统中）

set -e
cd "$(dirname "$0")"

GH="./bin/gh.exe"
REPO="merryjiajia-creator/wuma"
USER="merryjiajia-creator"
MSG="${1:-Update daily report $(date +%Y-%m-%d)}"

# 1. 检查 gh 认证
if ! $GH auth token > /dev/null 2>&1; then
  echo "✗ gh 未授权，请先运行: ./bin/gh.exe auth login"
  exit 1
fi

TOKEN=$($GH auth token)

# 2. 暂存所有日报相关文件
git add index.html archive/ 2>/dev/null || true

# 3. 提交（若无变化则跳过）
if git diff --cached --quiet; then
  echo "无文件变更，检查是否有未推送的提交..."
else
  git commit -m "$MSG"
  echo "✓ 已提交: $MSG"
fi

# 4. 推送（使用 gh token 内联认证，避免交互式提示）
GIT_TERMINAL_PROMPT=0 git push "https://${USER}:${TOKEN}@github.com/${REPO}.git" main 2>&1
echo "✓ 已推送到 GitHub Pages"

# 5. 验证
sleep 3
DATE=$(curl -s "https://raw.githubusercontent.com/${REPO}/main/index.html" | grep -o "2026年[0-9]*月[0-9]*日" | head -1)
echo "✓ GitHub 当前日报日期: ${DATE}"
echo "✓ 访问地址: https://${USER}.github.io/wuma/"
