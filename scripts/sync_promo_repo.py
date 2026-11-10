#!/usr/bin/env python3
"""同步主站公开数据 → GitHub 推广仓 link-kuajing/myhaiwan-airport-reviews
数据源: site/assets/data/airports.json + tools.json (仅主站已公开内容)
红线: 不写任何 token/key/内部台账; 不写万达云; 跑路预警只用"失联/风险观察"措辞; 链接全部指向 myhaiwan.com
"""
import json, os, subprocess, sys, datetime

PROJ = os.path.expanduser("~/coding-projects/proj-4")
REPO = "/tmp/promo-repo"
SITE = "https://myhaiwan.com"
STOP_LIST = ("万达云",)  # 全站停推

RENDER_ONLY = "--render-only" in sys.argv  # Actions 兜底模式: 从仓内 data/ 读取

def load(name):
    path = (os.path.join(REPO, "data") if RENDER_ONLY else os.path.join(PROJ, "site/assets/data")) + "/" + name
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    data = load("airports.json")
    airports = [a for a in data.get("airports", [])
                if a.get("name") and not any(s in (a.get("name") or "") for s in STOP_LIST)]
    airports.sort(key=lambda a: (a.get("monthly_low") is None, a.get("monthly_low") or 1e9))
    try:
        tools = load("tools.json").get("tools", [])
    except Exception:
        tools = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = data.get("updated_at") or ts

    os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
    for fn, src in (("airports.json", data), ("tools.json", load("tools.json"))):
        with open(os.path.join(REPO, "data", fn), "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False, indent=2)

    def rows(lst, lim=None):
        out = []
        for a in (lst[:lim] if lim else lst):
            lo = a.get("monthly_low"); hi = a.get("monthly_high")
            price = f"¥{lo:g} ~ ¥{hi:g}/月" if lo else "—"
            flag = "🟢" if a.get("service_status") == "normal" else "🟡 观察中"
            out.append(f"| {a['name']} | {flag} | {price} | {a.get('speed') or '—'} | {a.get('media') or '—'} |")
        return "\n".join(out)

    header = "| 机场 | 状态 | 最低价区间 | 标称速度 | 流媒体 |\n|---|---|---|---|---|"

    table = f"""# 机场价格总表（完整版）

> 数据快照：{updated} · 共 {len(airports)} 家 · 完整详情与最新状态见主站：[{SITE}/reviews]({SITE}/reviews/)

{header}
{rows(airports)}

---
*本表由脚本自动生成，每日同步。价格与状态以 [myhaiwan.com]({SITE}/) 实时页面为准。*
"""

    readme = f"""# 海外机场评测与跑路预警 · myhaiwan.com

> 独立观察 {len(airports)} 家机场的价格、线路与运行状态。**本仓是数据镜像，完整评测请访问 [myhaiwan.com]({SITE})。**

## 它能帮你做什么

- 每日更新的机场价格总表，最低 ¥{min([a['monthly_low'] for a in airports if a.get('monthly_low')] or [0]):g}/月 起
- 跑路/失联风险观察名单，避免年付踩坑
- 客户端工具（Clash 系等）版本追踪与下载指引

## 本月低价榜 TOP 5

{header}
{rows(airports, 5)}

## 导航（全部在主站）

| 页面 | 链接 |
|---|---|
| 🏠 首页·今日推荐 | [myhaiwan.com]({SITE}/) |
| 📋 完整价格总表 | [myhaiwan.com/reviews]({SITE}/reviews/) |
| ⚠️ 跑路预警名单 | [myhaiwan.com/paolu]({SITE}/paolu/) |
| 🛠 客户端工具下载 | [myhaiwan.com/tools]({SITE}/tools/) |

## 仓库文件

- [TABLE.md](TABLE.md) — 全量价格总表
- [paolu.md](paolu.md) — 失联/风险观察名单
- [tools.md](tools.md) — 客户端工具清单
- `data/` — 结构化数据（JSON）

---
*数据每日 05:10 自动同步自主站公开接口快照，仅供参考；购买前请以服务商官网为准。*
"""

    paolu = f"""# ⚠️ 失联 / 风险观察名单

> 本名单仅记录**公开可查的客观状态变化**（官网无法访问、服务中断等），不构成对任何服务商的指控。
> 判定与最新详情见主站：[myhaiwan.com/paolu]({SITE}/paolu/)

## 观察口径

- **失联**：官网/面板连续多日无法访问，且无官方公告
- **风险观察**：出现用户反馈异常、服务降级、公告变更等信号，尚待确认

## 当前名单

| 机场 | 状态 | 最近更新 | 说明 |
|---|---|---|---|
"""
    risky = [a for a in airports if a.get("service_status") not in ("normal",)]
    if risky:
        for a in risky:
            st = a.get("service_status")
            label = "失联" if st in ("lost", "down", "offline") else "风险观察"
            paolu += f"| {a['name']} | {label} | {a.get('updated_at','—')} | 见[主站详情]({SITE}/paolu/) |\n"
    else:
        paolu += "\n*暂无处于观察状态的服务商。历史案例与避坑指南见 [myhaiwan.com/paolu]({SITE}/paolu/)。*\n"
    paolu += f"""
---

*状态由脚本基于主站公开数据自动生成，每日更新。任何服务商状态以官方公告为准。*
"""

    toolsmd = f"""# 🛠 客户端工具清单

> 下载链接、版本与配置教程见主站：[myhaiwan.com/tools]({SITE}/tools/)

| 工具 | 平台 | 最新版本 | 发布日期 |
|---|---|---|---|
"""
    for t in tools:
        toolsmd += f"| {t.get('name')} | {'/'.join(t.get('platforms', []))} | {t.get('version','—')} | {t.get('released','—')} |\n"
    toolsmd += f"""
---

*版本每日同步。下载与安装教程：[myhaiwan.com/tools]({SITE}/tools/)*
"""

    files = {"README.md": readme, "TABLE.md": table, "paolu.md": paolu, "tools.md": toolsmd}
    for fn, content in files.items():
        with open(os.path.join(REPO, fn), "w", encoding="utf-8") as f:
            f.write(content)

    if RENDER_ONLY:
        print("render-only done")
        return
    env = dict(os.environ)
    with open(os.path.join(PROJ, "ops/secrets.env")) as f:
        for line in f:
            if line.startswith("GH_TOKEN_PROMO="):
                env["GH_TOKEN_PROMO"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    tok = env.get("GH_TOKEN_PROMO")
    if not tok:
        sys.exit("ERROR: GH_TOKEN_PROMO not found")

    def run(*args, **kw):
        return subprocess.run(list(args), cwd=REPO, env=env, capture_output=True, text=True, **kw)

    run("git", "config", "user.name", "promo-sync-bot")
    run("git", "config", "user.email", "promo-sync@users.noreply.github.com")
    run("git", "add", "-A")
    st = run("git", "status", "--porcelain")
    if not st.stdout.strip():
        print("No changes to commit.")
        return
    msg = f"📊 数据自动同步 @ {ts}"
    r = run("git", "commit", "-m", msg)
    print(r.stdout, r.stderr)
    push_url = f"https://x-access-token:{tok}@github.com/link-kuajing/myhaiwan-airport-reviews"
    r = run("git", "push", push_url, "main")
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        sys.exit("push failed")
    print("SYNC OK")

if __name__ == "__main__":
    main()
