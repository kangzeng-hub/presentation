#!/usr/bin/env bash
# scripts/secret_scan.sh
#
# 扫描"可能被 git 跟踪的源文件"中是否存在明文 API 密钥。
# 这是一个安全网：在 git commit 之后、git push 之前运行，
# 如果发现密钥就报警并退出码 1。
#
# 注意：.env 被故意排除——它本来就该存真实密钥，且已被 .gitignore 忽略。
# 本脚本扫的是"代码文件、配置文件、文档"里不该出现的密钥。

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 扫描模式：只扫有标准前缀的真实 key，不扫赋值语句（避免文档示例、.env.example 模板误报）。
# 本项目用到的所有服务（DashScope / Ark / OpenAI / AWS）的 key 都有可识别前缀。
#   sk-xxx   → DashScope / OpenAI 风格
#   ark-xxx  → Ark / 火山引擎风格
#   AKIAxxx  → AWS Access Key
PATTERN='(sk-[A-Za-z0-9_-]{20,}|ark-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16})'

printf '========================================\nSecret Scan\n========================================\n'

# -r 递归  -E 扩展正则  -I 忽略二进制文件
# --exclude-dir 排除不该扫描的目录
# --exclude 排除不该扫描的文件
if grep -rEI "$PATTERN" . \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=.ppt-venv \
  --exclude-dir=node_modules \
  --exclude-dir=frontend/node_modules \
  --exclude-dir=output \
  --exclude-dir=__pycache__ \
  --exclude-dir=archive \
  --exclude=.env \
  --exclude='*.pyc' \
  --exclude='*.pptx' \
  --exclude='*.png' \
  --exclude='*.jpg' \
  --exclude='*.jpeg' \
  --exclude='*.gif' \
  --exclude='*.lock' \
  2>/dev/null; then
  echo ""
  echo "✗ 检测到可能的密钥泄露！"
  echo "  请检查上方匹配的文件。如果该文件本就该包含密钥（如 .env），"
  echo "  请确认它已被 .gitignore 忽略，并加入本脚本的 exclude 列表。"
  exit 1
else
  echo "✓ 源文件中未发现明显密钥。"
  exit 0
fi
