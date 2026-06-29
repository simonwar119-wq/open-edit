"""Open Edit v2 — backend（FastAPI 服务化内核）。

把 engine/ 的 plan_edl + render_edl 包成 SaaS 后端：
  上传素材 → 建项目 → 提交渲染 job → 后台 worker 跑流水线 → 轮询 → 下载成片。

Phase 1 用零云依赖的 dev 适配器（每个都有接口，生产可整体替换）：
  DB        SQLite        → 生产 Postgres（SQLAlchemy 同一套 models）
  存储       本地磁盘       → 生产 Cloudflare R2（Storage 接口）
  编排/队列   线程 worker    → 生产 Temporal（durable 工作流）
  风格选择   启发式         → 生产 Claude agent（orchestrator 接口）
"""
