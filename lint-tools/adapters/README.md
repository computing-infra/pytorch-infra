# Linter Adapters

本目录包含从 PyTorch 仓库复制并适配的 linter 适配器脚本，用于 Ascend/pytorch 代码静态扫描。

## 文件说明

| 文件 | 功能 |
|------|------|
| `grep_linter.py` | 通用 grep linter，用于模式匹配检查 |
| `newlines_linter.py` | 换行符检查（确保使用 LF） |
| `clangformat_linter.py` | C++ 代码格式化检查 |
| `flake8_linter.py` | Python PEP8 代码检查 |
| `ruff_linter.py` | Python 综合检查 + 格式化（替代 flake8 + isort） |
| `codespell_linter.py` | 拼写错误检查 |
| `shellcheck_linter.py` | Shell 脚本检查 |
| `actionlint_linter.py` | GitHub Actions workflow 检查 |
| `s3_init.py` | 从 S3 下载 clang-format/clang-tidy 预编译二进制 |
| `s3_init_config.json` | S3 二进制下载配置（URL 和 SHA256 哈希） |

## 来源

这些脚本从 [pytorch/pytorch](https://github.com/pytorch/pytorch) 仓库的 `tools/linter/adapters/` 目录复制。

## 使用方式

通过 lintrunner 调用，配置文件位于 `lint-config/.lintrunner.toml`。