#!/usr/bin/env bash
# clone_sources.sh - 浅克隆 pytorch 和 torch_npu 源码供 AI 分析。
#
# 用法：clone_sources.sh [输出目录]
# 默认输出目录：/tmp/sources
set -euo pipefail

OUTPUT_DIR="${1:-/tmp/sources}"
PYTORCH_DIR="${OUTPUT_DIR}/pytorch"
TORCH_NPU_DIR="${OUTPUT_DIR}/torch_npu"

mkdir -p "$OUTPUT_DIR"

echo "=== 克隆 pytorch 源码 (main, --depth=1) ==="
if [[ -d "$PYTORCH_DIR/.git" ]]; then
    echo "pytorch 已存在，跳过克隆"
else
    git clone --depth=1 --no-tags --single-branch \
        --branch main \
        https://github.com/pytorch/pytorch.git \
        "$PYTORCH_DIR"
    echo "pytorch 克隆完成"
fi

echo "=== 克隆 torch_npu 源码 (master, --depth=1) ==="
if [[ -d "$TORCH_NPU_DIR/.git" ]]; then
    echo "torch_npu 已存在，跳过克隆"
else
    git clone --depth=1 --no-tags --single-branch \
        --branch master \
        https://gitcode.com/Ascend/pytorch.git \
        "$TORCH_NPU_DIR"
    echo "torch_npu 克隆完成"
fi

echo "=== 源码路径 ==="
echo "PYTORCH_SRC=$PYTORCH_DIR"
echo "TORCH_NPU_SRC=$TORCH_NPU_DIR"

echo "=== 目录大小 ==="
du -sh "$PYTORCH_DIR" "$TORCH_NPU_DIR" 2>/dev/null || true
