#!/usr/bin/env python3
"""
extract_failure_logs.py - 提取 Ascend/pytorch CI build 阶段失败日志，供 AI 分析。

通过 `gh run view --log-failed` 获取失败 job 日志，解析按 job/step 分割，
提取关键错误行及上下文，输出结构化 JSON。

用法：
    python3 extract_failure_logs.py <run-id或url> [--output <目录>] [--repo Ascend/pytorch]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = "Ascend/pytorch"
LOG_DIR_DEFAULT = "/tmp/ci-analysis"

ERROR_PATTERNS = [
    r"##\[error\]",
    r"^error:",
    r"^Error:",
    r"^FAILED",
    r"fatal error:",
    r"CMake Error",
    r"No space left on device",
    r"Killed signal terminated program",
    r"error: patch failed",
    r"does not apply",
    r"redefinition of",
    r"no member named",
    r"unrecognized command-line option",
    r"Connection timed out",
    r"404 Not Found",
    r"ModuleNotFoundError",
    r"ImportError",
    r"Subprocess failed with return code",
    r"Process completed with exit code [1-9]",
]

MAX_CONTEXT_LINES = 50
MAX_LOG_SIZE = 200_000


def parse_run_id(raw: str) -> str:
    m = re.search(r"/runs/(\d+)", raw)
    return m.group(1) if m else raw.strip()


def get_run_info(run_id: str, repo: str) -> dict:
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/actions/runs/{run_id}",
             "--jq", "{run_name,run_url,head_branch,created_at,event}"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        info = json.loads(r.stdout)
        info.setdefault("run_url", f"https://github.com/{repo}/actions/runs/{run_id}")
        return info
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"警告：获取运行信息失败: {e}", file=sys.stderr)
        return {
            "run_name": f"Run {run_id}",
            "run_url": f"https://github.com/{repo}/actions/runs/{run_id}",
            "head_branch": "",
            "created_at": "",
            "event": "",
        }


def get_failed_jobs(run_id: str, repo: str) -> list[dict]:
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/actions/runs/{run_id}/jobs",
             "--jq", ".jobs[] | select(.conclusion==\"failure\") | {name,conclusion,steps:[.steps[]? | select(.conclusion==\"failure\") | {name,conclusion,number}]}"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        if not r.stdout.strip():
            return []
        jobs = json.loads(r.stdout)
        return jobs if isinstance(jobs, list) else [jobs]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"警告：获取失败 job 列表失败: {e}", file=sys.stderr)
        return []


def fetch_failed_logs(run_id: str, repo: str) -> str:
    print(f"正在获取运行 {run_id} 的失败日志...", file=sys.stderr)
    try:
        r = subprocess.run(
            ["gh", "run", "view", run_id, "--repo", repo, "--log-failed"],
            capture_output=True, text=True, timeout=120, check=True,
        )
        print(f"日志大小: {len(r.stdout)} 字节", file=sys.stderr)
        return r.stdout
    except subprocess.CalledProcessError as e:
        print(f"错误：获取失败日志失败: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return ""
    except subprocess.TimeoutExpired:
        print("错误：获取日志超时（120s）", file=sys.stderr)
        return ""


def parse_log_line(line: str) -> dict | None:
    parts = line.split("\t")
    if len(parts) >= 4:
        return {"job": parts[0], "step": parts[1], "timestamp": parts[2], "content": "\t".join(parts[3:])}
    if len(parts) == 3:
        return {"job": parts[0], "step": parts[1], "timestamp": "", "content": parts[2]}
    return None


def is_error_line(content: str) -> bool:
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


def segment_by_job(raw_log: str) -> dict[str, list[dict]]:
    jobs: dict[str, list[dict]] = {}
    for line in raw_log.splitlines():
        parsed = parse_log_line(line)
        if parsed:
            jobs.setdefault(parsed["job"], []).append(parsed)
        else:
            for job_name in jobs:
                jobs[job_name].append({"job": job_name, "step": "", "timestamp": "", "content": line})
    return jobs


def extract_errors(lines: list[dict]) -> list[dict]:
    errors = []
    line_contents = [l["content"] for l in lines]
    for i, content in enumerate(line_contents):
        if is_error_line(content):
            start = max(0, i - MAX_CONTEXT_LINES)
            end = min(len(line_contents), i + MAX_CONTEXT_LINES + 1)
            context = "\n".join(line_contents[start:end])
            if len(context) > MAX_LOG_SIZE:
                context = context[:MAX_LOG_SIZE] + "\n... (日志截断)"
            errors.append({
                "error_line": content,
                "step": lines[i].get("step", ""),
                "context": context,
                "line_index": i,
            })
    if not errors and line_contents:
        tail = "\n".join(line_contents[-100:])
        if len(tail) > MAX_LOG_SIZE:
            tail = tail[:MAX_LOG_SIZE] + "\n... (日志截断)"
        errors.append({
            "error_line": "(未匹配到已知错误模式，取日志末尾)",
            "step": "",
            "context": tail,
            "line_index": len(line_contents) - 1,
        })
    return errors


def build_failure_report(run_id: str, repo: str) -> dict:
    run_info = get_run_info(run_id, repo)
    failed_jobs = get_failed_jobs(run_id, repo)
    raw_log = fetch_failed_logs(run_id, repo)

    if not raw_log:
        return {
            "run_id": run_id,
            "run_info": run_info,
            "failed_jobs_meta": failed_jobs,
            "failures": [],
            "error": "无法获取失败日志",
        }

    job_segments = segment_by_job(raw_log)
    failures = []
    for job_name, lines in job_segments.items():
        job_meta = next((j for j in failed_jobs if j["name"] == job_name), None)
        failed_steps = [s["name"] for s in (job_meta or {}).get("steps", [])]
        errors = extract_errors(lines)
        if errors:
            failures.append({
                "job_name": job_name,
                "failed_steps": failed_steps,
                "errors": errors,
                "total_log_lines": len(lines),
            })

    return {
        "run_id": run_id,
        "run_info": run_info,
        "failed_jobs_meta": failed_jobs,
        "failures": failures,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    run_id = parse_run_id(sys.argv[1])
    output_dir = Path(LOG_DIR_DEFAULT)
    repo = DEFAULT_REPO

    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])
        elif arg == "--repo" and i + 1 < len(sys.argv):
            repo = sys.argv[i + 1]

    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_failure_report(run_id, repo)

    output_file = output_dir / "failures.json"
    output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存至: {output_file}", file=sys.stderr)
    print(f"失败 job 数: {len(report['failures'])}", file=sys.stderr)
    for f in report["failures"]:
        print(f"  - {f['job_name']}: {len(f['errors'])} 个错误", file=sys.stderr)


if __name__ == "__main__":
    main()
