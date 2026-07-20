#!/usr/bin/env python3
"""
scan_failures.py - 扫描 Ascend/pytorch 的 pytorch_ci_trigger.yml 运行。

查找最近实际执行了 `forward / build / pytorch_and_torch-npu_build` job 的运行：
- 如果最新一次 build 成功 → 正常结束，无需分析
- 如果最新一次 build 失败 → 返回该运行供分析（去重由 check_duplicate.py 负责）

只有 PR closed 事件才可能触发 build（需 merged + target main），
因此预过滤只检查 (closed) 运行以减少 API 调用。

用法：
    python3 scan_failures.py [--hours 72] [--json]
"""

import json
import subprocess
import sys
import time

REPO = "Ascend/pytorch"
WORKFLOW_FILE = "pytorch_ci_trigger.yml"
BUILD_JOB_NAME = "forward / build / pytorch_and_torch-npu_build"
FORWARD_JOB_PREFIX = "forward /"
MAX_PAGES = 5


def gh_api(endpoint: str, jq: str | None = None) -> list | dict | str | int | None:
    cmd = ["gh", "api", endpoint]
    if jq:
        cmd += ["--jq", jq]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        if not r.stdout.strip():
            return []
        return json.loads(r.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"gh api 调用失败: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return []


def get_workflow_id() -> str | None:
    result = gh_api(
        f"repos/{REPO}/actions/workflows",
        jq=".workflows[] | select(.path | endswith(\"{}\")) | .id".format(WORKFLOW_FILE),
    )
    if isinstance(result, list) and result:
        return str(result[0])
    if isinstance(result, (int, str)):
        return str(result)
    return None


def list_closed_runs(workflow_id: str, hours: int) -> list[dict]:
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - hours * 3600))
    all_closed = []
    for page in range(1, MAX_PAGES + 1):
        result = gh_api(
            f"repos/{REPO}/actions/workflows/{workflow_id}/runs"
            f"?per_page=100&page={page}&created=>={since}",
            jq="[.workflow_runs[] | {id,run_name,name,conclusion,created_at,head_branch,event,html_url}]",
        )
        if not isinstance(result, list) or not result:
            break
        page_closed = [r for r in result if "closed" in (r.get("name") or r.get("run_name") or "")]
        all_closed.extend(page_closed)
        print(f"  第 {page} 页: {len(result)} 条运行, {len(page_closed)} 条 closed", file=sys.stderr)
        if len(result) < 100:
            break
    all_closed.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return all_closed


def get_run_jobs(run_id: str) -> list[dict]:
    result = gh_api(
        f"repos/{REPO}/actions/runs/{run_id}/jobs",
        jq="[.jobs[] | {name,conclusion,status}]",
    )
    return result if isinstance(result, list) else []


def find_build_job(jobs: list[dict]) -> dict | None:
    for job in jobs:
        if job.get("name") == BUILD_JOB_NAME:
            return job
    return None


def find_failed_forward_jobs(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if j.get("name", "").startswith(FORWARD_JOB_PREFIX) and j.get("conclusion") == "failure"]


def has_forward_jobs(jobs: list[dict]) -> bool:
    return any(j.get("name", "").startswith(FORWARD_JOB_PREFIX) for j in jobs)


def get_run_name(run_id: str) -> str:
    info = gh_api(f"repos/{REPO}/actions/runs/{run_id}", jq="{run_name,name}")
    if isinstance(info, dict):
        return info.get("run_name") or info.get("name") or f"Run {run_id}"
    return f"Run {run_id}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="扫描 pytorch_ci_trigger.yml build 执行结果")
    parser.add_argument("--hours", type=int, default=72, help="扫描最近 N 小时（默认 72）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    workflow_id = get_workflow_id()
    if not workflow_id:
        msg = f"未找到 workflow {WORKFLOW_FILE}"
        if args.json:
            print(json.dumps({"error": msg, "action": "none"}))
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    print(f"Workflow ID: {workflow_id}", file=sys.stderr)
    print(f"扫描最近 {args.hours} 小时的 (closed) 运行...", file=sys.stderr)

    closed_runs = list_closed_runs(workflow_id, args.hours)
    print(f"找到 {len(closed_runs)} 个 (closed) 运行", file=sys.stderr)

    for run in closed_runs:
        run_id = str(run["id"])
        run_name = run.get("run_name") or run.get("name") or get_run_name(run_id)
        run["run_name"] = run_name

        jobs = get_run_jobs(run_id)

        if not has_forward_jobs(jobs):
            print(f"  {run_id} ({run_name}): 无 forward job（PR 未合并或非 main）", file=sys.stderr)
            continue

        build_job = find_build_job(jobs)
        failed_forward = find_failed_forward_jobs(jobs)
        failed_names = [j["name"] for j in failed_forward]

        if not failed_forward:
            build_status = build_job.get("conclusion") if build_job else "skipped"
            print(f"  {run_id} ({run_name}): 无失败 forward job（build={build_status}），继续查找", file=sys.stderr)
            continue

        print(f"  {run_id} ({run_name}): 失败 jobs={failed_names}", file=sys.stderr)
        print(f"发现失败: {run_id} ({run_name})", file=sys.stderr)
        run["failed_jobs"] = failed_names
        if args.json:
            print(json.dumps({
                "action": "analyze",
                "run": run,
            }, ensure_ascii=False, indent=2))
        else:
            print(run_id)
        return

    print("未找到有失败的 forward 运行", file=sys.stderr)
    if args.json:
        print(json.dumps({"action": "skip", "reason": "no_build_run_found"}))


if __name__ == "__main__":
    main()
