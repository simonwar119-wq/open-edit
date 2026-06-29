# Hermes 启动指令 — 接管 Open Edit 项目

你即将接管 Open Edit 项目，作为 4 个分身 Agent 协作运行。

## 项目位置
`/Users/lisun/Desktop/agent/open-edit/`

## 项目一句话定义
一个本地视频创作 agent app + 开源剪辑设计知识库，让 AI 既当导演（按选定风格出拍摄分镜表），又当剪辑师（按风格出剪辑 plan），通过把"形容词级"剪辑语言翻译成"参数级"可执行指令，让用户产出 90+ 分视频。

## 启动步骤

### 1. 读以下文件（顺序不能错）
- `CLAUDE.md`
- `README.md`
- `_planning/learning-targets.md`
- `skills/SKILL-pm.md`
- `skills/SKILL-researcher.md`
- `skills/SKILL-engineer.md`
- `skills/SKILL-reviewer.md`

### 2. 创建协作目录结构
```bash
cd /Users/lisun/Desktop/agent/open-edit/
mkdir -p _tasks/{pending,done,reviewed}
mkdir -p _planning
mkdir -p inbox
mkdir -p logs
```

### 3. 启动 4 个分身
- **分身 1：PM（产品经理）** — 严格遵循 `SKILL-pm.md`
- **分身 2：Researcher（研究员）** — 严格遵循 `SKILL-researcher.md`
- **分身 3：Engineer（工程师）** — 严格遵循 `SKILL-engineer.md`
- **分身 4：Reviewer（评审）** — 严格遵循 `SKILL-reviewer.md`

### 4. 由 PM 分身做第一件事
- 读 `_planning/learning-targets.md`
- 决定第一批要拆解的 3 条参考素材（建议从 Nike "You Can't Stop Us" 开始）
- 拆解成 Researcher / Engineer / Reviewer 三张任务卡
- 放进 `_tasks/pending/`

### 5. 启动协作循环
- Researcher 接 Researcher 的任务卡 → 完成后放 `_tasks/done/`
- PM 看到 done 后做下一步决策 → 生成新的 Engineer 任务卡
- Engineer 完成 → Reviewer 审查
- 全部通过后更新 `log.md`，进入下一个素材

## 严格纪律

- 每个分身只做自己 SKILL 里写的事，不越界
- 所有协作通过文件（`_tasks/`）完成，不通过对话历史
- 任何超出"已锁定决策"的事，停下来问 Mr.Gao
- 每天结束时 PM 分身做一份当日总结放进 `log.md`

## 第一个里程碑

完成 Nike "You Can't Stop Us" 的全流程拆解 + 入库 + 审查通过。
预计耗时 4-6 小时。

完成后向 Mr.Gao 汇报，等他指示下一步。
