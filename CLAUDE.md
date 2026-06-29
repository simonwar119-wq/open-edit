# CLAUDE.md — Open Edit 项目接手说明

> 给接手这个项目的 Claude 实例（Web Claude / Claude Code / Hermes / 任何后续 agent）读的"上车手册"。
> 读完这份你就能无缝续上之前的对话。

---

## 1. 你是谁、在做什么

你正在协助 **Mr.Gao（高牧洪）** 推进一个叫 **Open Edit** 的项目。

**项目一句话定义：**
一个本地视频创作 agent app + 开源剪辑设计语言知识库，让 AI 既能当**导演**（出拍摄分镜）也能当**剪辑师**（出剪辑 plan），把"形容词级"的剪辑语言翻译成"参数级"的可执行指令。

**对标对象：** Open Design（`~/Desktop/Agent/projects/open-design/`）— 一个设计系统+技能组合的本地 web app。
**Open Edit 的定位：** 把 open-design 的"设计系统"模型平移成"剪辑风格系统"，TAM 大 10 倍（抖音/YouTube/TikTok 几亿创作者）。

---

## 2. 项目的两个核心模式（关键设计）

这是项目最重要的设计，所有 agent 接手都必须理解：

### 模式 A：素材驱动（适配模式）
用户已有素材 → AI 分析 → 推荐风格 → 用户选 → AI 出剪辑 plan → 成片
目标用户：小白（90% 市场），目标质量：60 分素材产出 75 分作品。

### 模式 B：风格驱动（导演模式 / 核心差异化）
用户选定风格 → AI 反向生成拍摄分镜表
（N 个镜头、每个镜头的时长/景别/角度/内容/拍摄要点/失败信号）
→ 用户按分镜表拍摄 → AI 校验素材 → AI 剪辑 → 90+ 分成片
目标用户：专业团队、品牌方、Mr.Gao 自己（10% 市场，高客单价）。
**护城河**：全球无人做。剪映永远不会做模式 B，因为它服务最大公约数。

两个模式共享同一个知识库（taxonomy/），调用方向相反：
- 模式 A：素材 → 风格（被动适配）
- 模式 B：风格 → 素材（主动规划）

**重要：** 设计 `taxonomy/03-styles/` 下任何一个风格档案时，**必须包含"反向生成分镜"的字段**——这是模式 B 能跑起来的前提。

---

## 3. 两个核心闭环

**学习闭环（项目的灵魂，护城河）：**
参考视频 → ShotDeck/Vision/学术数据集 → 提取参数 → 沉淀进 taxonomy/

**应用闭环（项目的应用，赚钱的部分）：**
用户输入 → 调用 taxonomy/ → 出分镜（模式B）或剪辑plan（模式A）
→ FFmpeg/DaVinci 执行 → 用户反馈 → 回流学习闭环

没有学习闭环，应用闭环就是空架子。**"解析学习"是第一性的，"出片 pipeline"是第二位的。**

---

## 4. 项目当前进度

### ✅ 已完成

**骨架搭建：**
- 目录骨架（taxonomy/ 等）、README.md、.gitignore、SKILL.md（占位）
- Git 仓库已 init

**研究语料收集（2026-05-13）：**
- ✅ 14 篇学术论文 PDF（CineTechBench、SCINE、Cinematic2K、FullShots、MovieShots、CineLOG、Seedance 1.0、Open-Sora 2.0/Plan、Camera Artist、LAVE、Prompt-Driven Video Editing、Cutscene Agent、MiraData）
- ✅ 3 个 GitHub 仓库（ShotClassification、movie_shot_classification_dataset、shotdeck-scraper）
- ✅ 4 个相关网页快照
- ✅ `references/INDEX.md`（总索引）
- ✅ `references/raw-claims.md`（**关键产出** — 所有论文的分类清单原文，未经加工）
- ✅ `research-corpus-report.md`（完成报告）

**风格模板原型：**
- ✅ Qmike 风格模板 `taxonomy/03-styles/custom-analysis/qmike-style-guide.md`（9 段）
  - ⚠️ **需要升级**：当前版本只有"描述层"和部分"参数层"，**缺少模式 B 需要的"反向生成分镜"字段**。这是下一步要补的。

**网站推广项目集成：**
- ✅ `open-design-site-builder-skill.md` 已在网站推广项目中引用

### ⏳ 当前最核心待办

按优先级：

**P0 - 写 SKILL.md（项目宪法）**
包含：
- 文件命名规范
- Markdown frontmatter schema（描述层/参数层/执行层 + 反向分镜层）
- 工作前必读的 pre-flight checklist
- 何时停下来问 Mr.Gao
- Git commit 规范
- 多 agent 冲突处理

**P1 - 设计风格档案的统一 Schema（含"反向分镜"字段）**
基于 `references/raw-claims.md` 的论文分类法对比，设计一份统一 schema，让每个 style 文件包含：
- 描述层（形容词）
- 参数层（数字）
- 执行层（FFmpeg 命令）
- **反向分镜层（给模式 B 用）**：这个风格的成片需要几类镜头？每类多长？什么角度？什么内容？什么时机？

**P2 - 用新 Schema 升级 Qmike 风格模板**
把 `qmike-style-guide.md` 改造成完整四层结构，作为所有后续风格档案的标杆样例。

**P3 - 设计 app 层架构**
特别是 `app/pipeline/directed/`（模式 B 的实现），这是项目核心差异化。
参考 open-design 的目录哲学，但要补一个 `app/analysis/` 模块（学习 pipeline）。

**P4 - 批量填充**
- 其他 style 占位文件（王家卫、Wes Anderson、李子柒、Tasty 等）
- editing-techniques/ 下手法文件（J-cut、Speed Ramp 等）

---

## 5. 工作区位置

**项目根目录：** `/Users/lisun/Desktop/agent/open-edit/`

**References（研究语料）：** `/Users/lisun/Desktop/agent/open-edit/references/`
- `papers/` — 14 篇论文 PDF + metadata
- `repos/` — 3 个 GitHub 仓库
- `web/` — 4 个网页快照
- `INDEX.md` — 总索引
- `raw-claims.md` — 分类清单原材料（供 Web Claude 梳理用）

**相关项目（参考用，不要修改）：**
- `/Users/lisun/Desktop/Agent/projects/open-design/` — 兄弟开源项目
- `/Users/lisun/Desktop/Agent/网站推广项目/open-design/` — open-design 的完整 clone

---

## 6. 协作 Agent 矩阵

| Agent | 位置 | 强项 | 用途 |
|---|---|---|---|
| **Web Claude** | claude.ai 网页 | 战略、研究、跨域综合、写规范文档 | 设计 schema、写 SKILL.md、对比梳理论文分类法、做关键决策 |
| **Cowork** | 桌面 app | 能读本地文件、跨应用操作 | 接手 Web Claude 的设计，落地到本地文件 |
| **Hermes** | VS Code / 微信 | 文件操作、终端命令、便宜的批量任务 | 收集语料、跑脚本、Doubao/DeepSeek 调用、微信沟通 |
| **Claude Code** | VS Code | 写代码、改文件、跑长任务 | 主力工程、文件批量操作、无人值守过夜任务 |

**重要纪律：**
- 所有持久知识在文件里，不在对话历史里
- Agent 之间通讯通过文件，不通过 Mr.Gao 转述
- SKILL.md 是法律，每次工作前必读
- inbox/ 每天清零，否则堆死

---

## 7. Mr.Gao 的背景（影响你的回答方式）

- **职业**：专业厨师 + 餐厅老板（牛排馆 + 越南粉店）+ 美食内容创作者（Mr.Gao 的厨房，YouTube/小红书/抖音/TikTok/IG 全平台）
- **技术能力**：能用 Claude Code + Hermes，熟悉 Python/FFmpeg/DaVinci，Mac M4 Pro 24GB
- **审美背景**：前职业歌手 15 年，对节奏和情绪敏感
- **沟通偏好**：直接、决断、要可复制粘贴的输出、不要 fluffy 解释、不要重复啰嗦
- **设备**：主摄 Fujifilm X100VI，剪辑 DaVinci Resolve Studio 20，coding 环境 Python 3.11 + FFmpeg
- **终极目标：变现赚钱。** 所有工作以"最终能帮用户赚钱/降本/提竞争力"为标准决策

---

## 8. 设计决策已锁定（直接执行，不要再讨论）

> **⚠️ v2 转向修订（2026-06-27 by Mr.Gao 明确授权）**
> 本项目升级为 **生成即核心的 AI 电影短片工具：SaaS + 原生 iOS App**。以下三条**覆盖**旧锁定决策：
> - **覆盖旧 #9（CLI 起步/本地 app）** → 产品形态 = SaaS（Web 薄客户端）+ **原生 SwiftUI iOS App**；后端 **Python/FastAPI + Temporal + R2**。Phase 0 仍从 CLI 纵切起步以最便宜验证内核，但终态是服务化。
> - **覆盖旧「NOT generative / 仅 FFmpeg·DaVinci」** → **生成 API 是核心卖点**：AI 自动调 Seedance/Kling/HeyGen（经 fal.ai + PiAPI + 直连）产出镜头，再由风格库一键剪辑调色合成。
> - **护城河话术**：区别于 Higgsfield——生成只是**输入**，**风格化自动剪辑 + CDL/LUT 调色 + 合成成片**才是壁垒。
>
> **保留不变**：taxonomy 四层数据架构、模式 A/B、Python 优先、SKILL.md 严格派、学习闭环。执行蓝图见 `~/.claude/plans/agent-ai-open-edit-saas-ios-app-agent-p-replicated-peacock.md`。下面旧决策保留作历史，被上面三条覆盖处以本修订为准。

1. **项目定位**：私有 pipeline 资产 + 开源社区项目（MIT 协议）
2. **双模式架构**：模式 A（素材驱动）+ 模式 B（风格驱动，核心差异化）共存，共享同一知识库
3. **SKILL.md 严格度**：严格派——任何 agent 改文件前必须读 SKILL，违反规则就停下来问
4. **风格库分两支**：`from-shotdeck/`（自动生成）+ `custom-analysis/`（人工/Vision 拆解）
5. **ShotDeck 数据获取**：Claude in Chrome + Mr.Gao 会员账号合法浏览（不爬虫）
6. **数据架构**：四层——描述层、参数层、执行层、**反向分镜层（模式 B 关键）**
7. **目录命名**：顶层目录用数字前缀（01-、02-）控制排序
8. **"解析学习"第一性，"出片"第二性**
9. **CLI 起步**：先 CLI 工具，未来再加 web UI
10. **Python 优先**：FFmpeg/Vision/Whisper 生态都在 Python，不用 TS
11. **风格分类哲学**：全世界导演/剪辑师风格就那几大类。目标是把这些类型提取并参数化，不是逐个分析创作者

---

## 9. 必读文件索引（进项目后按此顺序读）

1. **`CLAUDE.md`**（本文件）← 你现在在读
2. **`README.md`** — 项目对外定位（已更新为双模式版本）
3. **`log.md`** — 历史进度（每次工作后更新）
4. **`SKILL.md`** — 项目宪法（待写，P0 任务）
5. **`references/INDEX.md`** — 研究语料索引
6. **`references/raw-claims.md`** — 论文分类清单原材料
7. **`taxonomy/00-overview.md`** — 知识库结构总览
8. **`taxonomy/01-scine-translated/00-scine-overview.md`** — SCINE 翻译
9. **`taxonomy/03-styles/custom-analysis/qmike-style-guide.md`** — 第一个风格档案（待升级到四层结构）

---

## 10. 沟通原则

- 不要重复确认，他说了就直接做
- 一次最多问一个关键问题
- 给可复制粘贴的指令，不给"你可以这样做"的描述
- 承认局限：拿不到的资料就说拿不到，不要编
- 中文回复，但代码/路径/技术名词保持英文
- **时刻把自己想得更开阔** — 遇到边界问题先问自己：这是不是又把问题想窄了？特别注意：之前的 agent 多次漏掉模式 B（导演模式），把项目降级成"普通 AI 剪辑器"。如果你也只看到模式 A，那就是把问题想窄了。

---

*文件最后更新：2026-05-13 由 Mr.Gao 明确项目定义后更新（加入双模式架构 + 四层数据 + 反向分镜层概念）*
