#!/bin/bash
# 自动修复 lint 问题的脚本（仅修复可自动修复的问题）
# 用法: ./lint-fix.sh [ascend_pytorch_path]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LINT_CONFIG="${REPO_ROOT}/lint-config"
LINT_TOOLS="${REPO_ROOT}/lint-tools"

# Ascend/pytorch 目录
ASCEND_PATH="${1:-/tmp/ascend_pytorch_lint}"

echo "=== Lint Fix for Ascend/pytorch ==="
echo "Target path: ${ASCEND_PATH}"

# 检查目录是否存在
if [ ! -d "${ASCEND_PATH}" ]; then
    echo "Error: ${ASCEND_PATH} does not exist"
    echo "Please run lint-runner.sh first or specify a valid path"
    exit 1
fi

# 复制配置文件（如果不存在）
if [ ! -f "${ASCEND_PATH}/.lintrunner.toml" ]; then
    cp "${LINT_CONFIG}/.lintrunner.toml" "${ASCEND_PATH}/"
fi
if [ ! -f "${ASCEND_PATH}/.clang-format" ]; then
    cp "${LINT_CONFIG}/.clang-format" "${ASCEND_PATH}/"
fi
if [ ! -d "${ASCEND_PATH}/lint-tools" ]; then
    cp -r "${LINT_TOOLS}" "${ASCEND_PATH}/"
fi

cd "${ASCEND_PATH}"

# 检查 lintrunner 是否安装
if ! command -v lintrunner &> /dev/null; then
    echo "Installing lintrunner..."
    pip install lintrunner
fi

# 初始化 linter
echo "Initializing linters..."
lintrunner init || true

# 执行自动修复
echo ""
echo "Running lint with auto-fix..."
echo "=========================================="

# 只运行 is_formatter = true 的 linter
lintrunner -a --take CLANGFORMAT,NEWLINE,SPACES,TABS 2>&1 || true

echo ""
echo "=========================================="
echo "Auto-fix completed!"
echo ""
echo "Note: Not all issues can be auto-fixed."
echo "Please review the changes and run lint-runner.sh to check remaining issues."