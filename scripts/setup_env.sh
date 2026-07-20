#!/usr/bin/env bash
# setup_env.sh - 在 GitHub Actions runner 中安装 opencode、gitcode CLI，并复制 skills。
#
# 环境变量：
#   BAILIAN_API_KEY  - 稀宇 MiniMax API key（必需，通过 opencode {env:} 引用，不落盘）
#   GC_TOKEN         - GitCode CLI token（issue-create workflow 需要）
set -euo pipefail

SKILLS_SRC_DIR="${1:-skills}"
SKIP_GITCODE="${SKIP_GITCODE:-false}"

echo "=== 安装 opencode CLI ==="
if ! command -v opencode &>/dev/null; then
    curl -fsSL https://opencode.ai/install | bash
    export PATH="$HOME/.opencode/bin:$PATH"
else
    echo "opencode 已安装: $(opencode --version 2>&1 | head -1)"
fi

echo "=== 安装 gitcode CLI ==="
if [[ "$SKIP_GITCODE" == "true" ]]; then
    echo "跳过 gitcode CLI 安装"
elif ! command -v gc &>/dev/null; then
    GC_VERSION="0.8.0"
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  GC_ARCH="amd64" ;;
        aarch64) GC_ARCH="arm64" ;;
        *)       GC_ARCH="$ARCH" ;;
    esac

    GC_DEB_URL="https://gitcode.com/gitcode-cli/cli/releases/download/v${GC_VERSION}/gc_${GC_VERSION}_${GC_ARCH}.deb"
    echo "下载: $GC_DEB_URL"
    curl -fsSL "$GC_DEB_URL" -o /tmp/gc.deb && sudo dpkg -i /tmp/gc.deb && {
        echo "gitcode CLI 安装完成: $(gc version 2>&1 | head -1)"
    } || {
        echo "deb 安装失败，尝试 tar.gz 方式..."
        GC_TGZ_URL="https://gitcode.com/gitcode-cli/cli/releases/download/v${GC_VERSION}/gc_linux_${GC_ARCH}.tar.gz"
        curl -fsSL "$GC_TGZ_URL" -o /tmp/gc.tar.gz || {
            echo "错误：无法下载 gitcode CLI"
            exit 1
        }
        mkdir -p /tmp/gc-extract
        tar -xzf /tmp/gc.tar.gz -C /tmp/gc-extract
        cp /tmp/gc-extract/gc /usr/local/bin/gc 2>/dev/null || sudo cp /tmp/gc-extract/gc /usr/local/bin/gc
        chmod +x /usr/local/bin/gc
        echo "gitcode CLI 安装完成（tar.gz）: $(gc version 2>&1 | head -1)"
    }
else
    echo "gitcode CLI 已安装: $(gc version 2>&1 | head -1)"
fi

echo "=== 配置 GitCode CLI 认证 ==="
if [[ -n "${GC_TOKEN:-}" ]] && command -v gc &>/dev/null; then
    gc auth login --token "$GC_TOKEN" 2>&1 || echo "警告：gc auth login 失败（可能已登录）"
fi

echo "=== 复制 skills 到项目根目录 .claude/skills/ ==="
PROJECT_SKILLS_DIR="${PROJECT_DIR:-$PWD}/.claude/skills"
mkdir -p "$PROJECT_SKILLS_DIR"
if [[ -d "$SKILLS_SRC_DIR" ]]; then
    cp -r "$SKILLS_SRC_DIR"/* "$PROJECT_SKILLS_DIR/"
    echo "已复制 skills 到 $PROJECT_SKILLS_DIR:"
    ls -la "$PROJECT_SKILLS_DIR/"
else
    echo "警告：skills 目录不存在: $SKILLS_SRC_DIR"
fi

echo "=== 生成 opencode 配置 ==="
mkdir -p "$HOME/.config/opencode"
if [[ -z "${BAILIAN_API_KEY:-}" ]]; then
    echo "错误：BAILIAN_API_KEY 未设置"
    exit 1
fi

cat > "$HOME/.config/opencode/opencode.jsonc" <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "disabled_providers": [],
  "provider": {
    "bailian": {
      "name": "稀宇",
      "npm": "@ai-sdk/anthropic",
      "options": {
        "apiKey": "{env:BAILIAN_API_KEY}",
        "baseURL": "https://api.minimaxi.com/anthropic/v1"
      },
      "models": {
        "MiniMax-M3": {
          "name": "MiniMax-M3"
        }
      }
    }
  }
}
EOF
echo "opencode 配置已生成（apiKey 通过 {env:BAILIAN_API_KEY} 引用环境变量，不落盘）"

echo "=== 环境准备完成 ==="
