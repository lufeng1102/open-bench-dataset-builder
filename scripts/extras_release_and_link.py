#!/usr/bin/env python
"""把已 push 到临时版本的附加文件发布成正式版本，校验后把源文件替换成平台软链。

用法：
    python scripts/extras_release_and_link.py <job.json> [--release-msg MSG] [--no-link]

job.json 格式（每项一个数据集）：
    [{"name": "<不带 _phy_ 前缀的数据集名>",
      "workdir": "<本地 _phy_* 工作目录>",
      "files": ["<本次上传的源文件绝对路径>", ...]}]

流程严格按仓库约定：
    ds-cli release -> 轮询 ds-cli version 直到临时版本消失 -> 逐文件 md5 比对 -> 删源文件建软链。
md5 不一致时该数据集直接跳过，不删任何文件。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

DS_POOL = "/hpc_stor08/ds//g001/store002/ds_pool"
NO_PROXY_ENV = {k: "" for k in
                ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY")}


def run_ds_cli(args, cwd=None, timeout=1800):
    """执行 ds-cli 命令，强制清空代理环境变量。"""
    env = dict(os.environ)
    for k in NO_PROXY_ENV:
        env.pop(k, None)
    p = subprocess.run(["ds-cli"] + args, cwd=cwd, env=env, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def query_version(platform_name):
    """返回 (最新版本号, 最新正式版本号)；查询失败返回 (None, None)。"""
    rc, out = run_ds(["version", "-n", platform_name], timeout=600)
    if rc != 0:
        return None, None
    latest = re.search(r"最新版本号[:：]\s*(\S+)", out)
    formal = re.search(r"最新正式版本号[:：]\s*(\S+)", out)
    return (latest.group(1) if latest else None,
            formal.group(1) if formal else None)


def extras_dir(platform_name, version):
    """正式版本目录有两种布局，都要认。"""
    for d in (f"{DS_POOL}/{platform_name}/extras/{version}",
              f"{DS_POOL}/{platform_name}/extras/version/{version}"):
        if os.path.isdir(d):
            return d
    return None


def md5(path):
    out = subprocess.run(["md5sum", path], stdout=subprocess.PIPE, check=True).stdout
    return out.decode().split()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--release-msg", default="追加附加文件")
    ap.add_argument("--no-link", action="store_true", help="只发布和校验，不删源文件")
    ap.add_argument("--relink-parent", action="store_true",
                    help="产物在 fa_v2/ 这类子目录时，改为重指上级目录的同名入口，不动产物本身")
    ap.add_argument("--skip-release", action="store_true",
                    help="发布申请已提交过时使用，避免对同一数据集重复申请")
    ap.add_argument("--poll-interval", type=int, default=300, help="轮询发布状态的间隔秒数")
    ap.add_argument("--overall-timeout", type=int, default=8 * 3600,
                    help="等待全部发布完成的总超时秒数")
    args = ap.parse_args()

    jobs = json.load(open(args.job))
    failed = []

    # 先统一提交发布申请：平台异步处理，集中提交后一起等，比逐个串行等快得多
    print("--- 提交发布申请", flush=True)
    for job in [] if args.skip_release else jobs:
        name, platform = job["name"], f"_phy_{job['name']}"
        latest, formal = query_version(platform)
        if latest is None:
            print(f"  !! {name} 查询版本失败"); failed.append(name); continue
        if latest == formal:
            print(f"  -- {name} 无临时版本，已是 {formal}"); continue
        rc, out = run_ds(["release", "-m", args.release_msg], cwd=job["workdir"], timeout=1800)
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        print(f"  {name} release rc={rc}: {tail}", flush=True)

    # 平台发布是排队串行处理的，谁先发完就先处理谁，不按固定顺序死等
    pending = [j for j in jobs if j["name"] not in failed]
    deadline = time.time() + args.overall_timeout
    while pending and time.time() < deadline:
        ready = []
        for job in pending:
            latest, formal = query_version(f"_phy_{job['name']}")
            if latest and formal and latest == formal:
                ready.append((job, formal))
        if not ready:
            print(f"--- 仍有 {len(pending)} 个待发布，{args.poll_interval}s 后重查", flush=True)
            time.sleep(args.poll_interval)
            continue

        for job, formal in ready:
            pending.remove(job)
            handle(job, formal, args, failed)

    for job in pending:
        print(f"!! {job['name']} 发布超时未完成"); failed.append(job["name"])

    if failed:
        print("\n以下数据集未完成，需人工检查：")
        for n in failed:
            print(f"  - {n}")
        sys.exit(1)
    print("\n全部完成")


def handle(job, formal, args, failed):
    """对已发布出正式版本的数据集做 md5 校验并替换软链。"""
    name, files = job["name"], job["files"]
    platform = f"_phy_{name}"
    print(f"=== {name}\n    正式版本 {formal}", flush=True)

    ed = extras_dir(platform, formal)
    if not ed:
        print("    !! 找不到 extras 目录，跳过"); failed.append(name); return

    # 先全部比对通过，再统一删除，避免部分删除后才发现不一致
    pairs = []
    for src in files:
        dst = os.path.join(ed, os.path.basename(src))
        base = os.path.basename(src)
        if os.path.islink(src):
            print(f"    -- 已是软链，跳过 {base}"); continue
        if not os.path.isfile(dst):
            print(f"    !! 平台缺文件 {dst}"); failed.append(name); return
        if os.path.getsize(src) != os.path.getsize(dst):
            print(f"    !! 大小不一致 {base}"); failed.append(name); return
        if md5(src) != md5(dst):
            print(f"    !! md5 不一致 {base}"); failed.append(name); return
        print(f"    md5 OK {base}", flush=True)
        pairs.append((src, dst))

    if args.no_link:
        return

    if args.relink_parent:
        relink_parent(pairs)
        return

    for src, dst in pairs:
        os.remove(src)
        os.symlink(dst, src)
    print(f"    已替换 {len(pairs)} 个软链", flush=True)


def relink_parent(pairs):
    """产物放在 fa_v2/ 这类子目录时，把上级目录的同名入口重指到平台新版本。

    上级是软链的直接重指（软链不含数据）；是实体文件的，只有内容与平台新版本一致才
    换成软链，否则保留原文件并告警——它可能是另一版产物，不能默默删掉。
    """
    relinked = kept = 0
    for src, dst in pairs:
        link = os.path.join(os.path.dirname(os.path.dirname(src)), os.path.basename(src))
        if os.path.islink(link):
            os.remove(link)
        elif os.path.exists(link):
            if md5(link) != md5(dst):
                print(f"    -- 上级实体文件与新版不一致，保留不动 {link}")
                kept += 1
                continue
            os.remove(link)
        os.symlink(dst, link)
        relinked += 1
    msg = f"    上级目录已重指 {relinked} 个软链"
    if kept:
        msg += f"，保留 {kept} 个不一致的实体文件"
    print(msg, flush=True)


if __name__ == "__main__":
    main()
