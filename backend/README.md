# backend — Open Edit v2 SaaS 后端（Phase 1）

把 `engine/` 的 `plan_edl` + `render_edl` 包成 FastAPI 服务：
**上传素材 → 建项目 → 提交渲染 job → 后台 worker 跑流水线 → 轮询 → 下载成片**，带积分账本。

## 跑起来

```bash
cd open-edit
backend/.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8011
# 文档 / OpenAPI: http://127.0.0.1:8011/docs   （iOS/web 由此生成类型化 client）
```

首次启动自动建库（SQLite）+ 种一个 default org + $20 测试积分。

## 端到端（curl）

```bash
B=http://127.0.0.1:8011
curl -s $B/me                                   # org + 余额
curl -s $B/styles                               # 可用导演风格
PID=$(curl -s -X POST $B/projects -H 'Content-Type: application/json' \
  -d '{"title":"牛排短片","style_id":"auto","prompt":"牛排在铸铁锅上油花四溅，冷峻高级"}' | jq -r .id)
curl -s -X POST $B/projects/$PID/assets -F "file=@qmike样片1.MP4"     # 上传
JID=$(curl -s -X POST $B/projects/$PID/render -H 'Content-Type: application/json' \
  -d '{"target_duration":12,"provider":"mock","budget_usd":5}' | jq -r .id)
curl -s $B/jobs/$JID                             # 轮询：queued→planning→generating→rendering→done
curl -s $B/jobs/$JID/output -o out.mp4           # 下载成片
```

真生成：`provider:"fal"`。key 从 `AutoClip/api/.env` 的 `FAL_API_KEY` 自动加载（也可 `export FAL_API_KEY=...`）。
省钱：`export FAL_RESOLUTION=480p` 再启服务。

## 验证过的路径（2026-06-27）

- mock job：auto 选中 fincher，3 镜头(2上传+1生成)，11.9s，$0，余额不变。
- fal job：真 Seedance 2.0 生成 1 镜头，9.3s，`spent_usd=$0.20`，余额 $20→$19.80（账本扣减生效）。
- `generation_requests` 落 provider/model/cost/commercial_ok；`credit_ledger` 落 topup/spend。

## Phase 1 = dev 适配器，生产可整体替换

| 关注点 | Phase 1（零云依赖，能跑） | 生产替换 | 接口位置 |
|---|---|---|---|
| 数据库 | SQLite | Postgres（同一 SQLAlchemy models） | `db.py` / `DATABASE_URL` |
| 存储 | 本地磁盘 | Cloudflare R2（S3 兼容） | `storage.py` `Storage` 接口 |
| 队列/编排 | 线程池 worker | Temporal durable 工作流 | `worker.py` |
| 选风格 | 启发式关键词打分 | Claude agent（分析素材→选风格→规划缺口） | `orchestrator.py` `resolve_style` |
| 计费 | 自有积分账本 + reserve gate | + Stripe Billing/Meters 镜像 | `credits.py` |
| 认证 | 单 default org（无 auth） | 真多租户 auth | `main.py` `default_org` |

## 结构

```
backend/app/
├── main.py          FastAPI 路由（/me /styles /projects /…/assets /…/render /jobs/{id}[/output]）
├── config.py        路径/env（自动从 AutoClip/api/.env 借 FAL_API_KEY）
├── db.py            SQLAlchemy engine/session
├── models.py        organizations/users/projects/assets/render_jobs/generation_requests/credit_ledger
├── schemas.py       Pydantic（OpenAPI 来源）
├── storage.py       Storage 接口 + LocalStorage（R2 待接）
├── credits.py       reserve → spend → settle 账本
├── orchestrator.py  选风格（启发式；Claude 待接）+ 列风格
└── worker.py        后台 job 流水线（线程；Temporal 待接）
```

## 已知 Phase 1 取舍（下一步）
- 编排是线程池，进程重启丢未完成 job（Temporal 解决 durability）。
- reserve 是「余额≥预算」预检 + post-hoc 按 EDL 记账，非 mid-flight 逐次 gate（Temporal + 逐调用 gate 解决）。
- 无 auth、无 webhook（fal 走轮询）、无并发 backpressure。
- 风格选择是关键词启发式，不是真 Claude 看素材。
