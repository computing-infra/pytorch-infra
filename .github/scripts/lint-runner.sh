#!/bin/bash
# 本地测试 lint 检查的脚本
# 用法: ./lint-runner.sh [ascend_pytorch_path]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LINT_CONFIG="${REPO_ROOT}/lint-config"
LINT_TOOLS="${REPO_ROOT}/lint-tools"

# Ascend/pytorch 目录
ASCEND_PATH="${1:-/tmp/ascend_pytorch_lint}"

echo "=== Lint Runner for Ascend/pytorch ==="
echo "Repository root: ${REPO_ROOT}"
echo "Target path: ${ASCEND_PATH}"
echo ""

# 检查或克隆 Ascend/pytorch
if [ ! -d "${ASCEND_PATH}" ]; then
    echo "Cloning Ascend/pytorch..."
    git clone --depth=1 https://gitcode.com/Ascend/pytorch.git "${ASCEND_PATH}"
else
    echo "Using existing Ascend/pytorch at ${ASCEND_PATH}"
fi

# 复制配置文件
echo "Copying lint configuration..."
cp "${LINT_CONFIG}/.lintrunner.toml" "${ASCEND_PATH}/"
cp "${LINT_CONFIG}/.clang-format" "${ASCEND_PATH}/"

# 复制 linter 工具
echo "Copying lint tools..."
cp -r "${LINT_TOOLS}" "${ASCEND_PATH}/"

# 进入目标目录
cd "${ASCEND_PATH}"

# 获取 commit 信息
COMMIT=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
echo "Scanning commit: ${COMMIT_SHORT}"

# 检查 lintrunner 是否安装
if ! command -v lintrunner &> /dev/null; then
    echo "Installing lintrunner..."
    pip install lintrunner
fi

# 初始化 linter
echo "Initializing linters..."
lintrunner init || true

# 执行 lint
echo ""
echo "Running lint checks..."
echo "=========================================="

set +e
lintrunner --force-color --tee-json=lint.json 2>&1 | tee lint_output.txt
LINT_EXIT_CODE=$?
set -e

echo ""
echo "=========================================="

# 分析结果
if [ -f lint.json ] && [ -s lint.json ]; then
    # 统计
    ERRORS=$(jq '[.[] | select(.severity == "error")] | length' lint.json 2>/dev/null || echo "0")
    WARNINGS=$(jq '[.[] | select(.severity == "warning" or .severity == "advice")] | length' lint.json 2>/dev/null || echo "0")

    echo ""
    echo "=== Lint Summary ==="
    echo "Errors: ${ERRORS}"
    echo "Warnings: ${WARNINGS}"
    echo ""

    if [ "${ERRORS}" != "0" ] || [ "${WARNINGS}" != "0" ]; then
        echo "Top 20 issues:"
        jq -r '.[] | select(.severity == "error" or .severity == "warning") | "\(.path):\(.line): \(.code): \(.description[:80])"' lint.json | head -20
    fi

    echo ""
    echo "Full results saved to: ${ASCEND_PATH}/lint.json"
    echo "Raw output saved to: ${ASCEND_PATH}/lint_output.txt"
else
    echo "No lint issues found!"
fi

exit ${LINT_EXIT_CODE}