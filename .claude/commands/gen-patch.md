针对已分析的兼容性问题，生成修复 patch 文件并更新 CI workflow 使其在构建时自动打入。

## 前置条件

- 已有 `/analyze-failure` 的分析结果，明确了受影响的文件和 API 变化
- 已在本地克隆了 Ascend/pytorch（位于 `/root/ascend_pytorch_tmp` 或临时目录）
- 如未克隆，先执行：`git clone --depth=1 https://github.com/Ascend/pytorch.git /tmp/ascend_pytorch_fix`

## 执行步骤

### 1. 理解 API 变化

- 找到 PyTorch nightly 安装的对应头文件（在 `$(python3 -c "import torch,os;print(os.path.dirname(torch.__file__))")/include/` 下）
- 对比 Ascend/pytorch 源码与新头文件，确认 API 签名、结构体成员、虚函数原型的具体差异

### 2. 修改源码

在 Ascend/pytorch 克隆副本中直接编辑受影响文件，原则：
- **最小改动**：只修改导致编译失败的部分，不重构周边逻辑
- **保持语义**：Ascend 的自定义数据结构和逻辑要保留，只调整与 PyTorch 接口的衔接部分
- **命名冲突优先解决**：若有 typedef/using 遮蔽问题，通过重命名 Ascend 侧的类型解决（而非修改 PyTorch 侧）

### 3. 生成 patch 文件

```bash
cd <ascend_pytorch克隆目录>
git diff > /root/pytorch-npu/patches/NNNN-<简短描述>.patch
```

命名规则：`patches/NNNN-fix-<受影响模块>-<问题简述>.patch`（NNNN 为四位序号）

### 4. 验证 patch 可以应用

```bash
# 在一个干净克隆上测试
git clone --depth=1 https://github.com/Ascend/pytorch.git /tmp/patch_test
git apply --directory=/tmp/patch_test /root/pytorch-npu/patches/NNNN-xxx.patch
echo "patch apply: $?"
```

### 5. 更新 issue 文档

在对应的 `issues/YYYY-MM-DD-NNN-xxx.md` 中填入 `对应 patch` 字段。

### 6. 确认 workflow 已包含 patch 应用步骤

检查 `.github/workflows/nightly-build.yml` 中是否存在以下步骤（若无则添加）：

```yaml
- name: Apply compatibility patches
  id: patch
  run: |
    for p in "${GITHUB_WORKSPACE}/patches"/*.patch; do
      [ -f "$p" ] || continue
      echo "Applying patch: $(basename $p)"
      if git apply --directory=ascend_pytorch "$p"; then
        echo "  ✅ OK"
      else
        echo "  ❌ FAILED (may already be merged upstream)"
      fi
    done
```

### 7. 提交

```bash
cd /root/pytorch-npu
git add patches/ issues/ .github/workflows/nightly-build.yml
git commit -m "Add patch and issue for <问题简述>"
git push
```

### 8. 触发验证

```bash
gh workflow run nightly-build.yml --repo kerer-ai/pytorch-npu
gh run watch --repo kerer-ai/pytorch-npu
```

观察新 run 是否通过，确认 patch 有效。

## 注意事项

- patch 格式为标准 `git diff` 输出（unified diff），不含 `--stat` 等额外信息
- 若 patch 已被 Ascend/pytorch 官方合入，`git apply` 会失败，CI 会静默跳过并在 summary 中标注，此时可将 patch 文件删除
- 每个 patch 只修复一个独立问题，便于退役和追踪
