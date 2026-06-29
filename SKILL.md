# SKILL.md — Open Edit 项目宪法

> 所有 agent（Web Claude / Cowork / Hermes / Claude Code）在改任何文件之前必须读这份文档。  
> 违反规则 → 停下来 → 问 Mr.Gao。  
> 本文件本身需要 Mr.Gao 审批才能修改。

> **⚠️ v2 转向（2026-06-27 Mr.Gao 授权）：** 项目升级为 **生成即核心的 SaaS + 原生 iOS App**。
> 旧锁定决策「CLI 起步/本地 app」与「NOT generative」**已被覆盖**——详见 `CLAUDE.md` 第 8 节 v2 修订与 plan 文件。
> 新增顶层目录已授权：`engine/`（Python CLI 内核，Phase 0）、`backend/`（FastAPI 服务化）、`web/`、`ios/`（SwiftUI）。
> 第 8 节「目录权威结构」以此为准扩展。taxonomy 四层架构、模式 A/B、Python 优先、严格派纪律不变。

---

## 0. Pre-flight Checklist（每次工作前必须过）

```
□ 读过 CLAUDE.md 吗？（双模式架构、四层数据、护城河是模式 B）
□ 读过本 SKILL.md 吗？（到这里说明你在读）
□ 看过 log.md 吗？（了解上次在哪停下来）
□ 任务是新建文件还是修改文件？
  → 新建：是否符合第 2 节命名规范？
  → 修改：是否需要同步更新 log.md？
□ 这个任务涉及风格档案吗？
  → 是：是否包含四层结构（含 Layer 4 反向分镜层）？
□ 这个任务会影响其他 agent 正在操作的文件吗？（见第 6 节冲突处理）
```

---

## 1. 项目核心原则（每条都是硬约束）

1. **模式 B 不能丢失。** 任何时候都要记住项目有两个模式。设计 schema、写档案、改架构，必须同时服务模式 A（素材驱动）和模式 B（风格驱动 / 反向生成分镜）。只看到模式 A 就是把项目降级了。

2. **四层结构，缺一不可。** 每个风格档案（`taxonomy/03-styles/` 下）必须包含：
   - Layer 1：描述层
   - Layer 2：参数层
   - Layer 3：执行层
   - **Layer 4：反向分镜层（模式 B 的前提，最不能省）**

3. **参数化优先于形容词化。** 能写 `1.2s` 就不写"较短"。能写 `5200K` 就不写"偏暖"。能写 `FFmpeg filtergraph` 就不写"可以用 FFmpeg 处理"。

4. **可调用 > 可阅读。** 文件首先服务 agent 调用，其次才是人阅读。frontmatter 字段必须机器可解析。

5. **出处可验证。** 每条手法/参数必须有来源（论文/影片/创作者/实测）。不允许凭空捏造参数。

6. **"解析学习"第一性，"出片"第二性。** 新增任何功能/文件时，优先问：这有没有充实知识库？出片 pipeline 是之后的事。

---

## 2. 文件命名规范

### 2.1 目录命名

- 顶层 `taxonomy/` 子目录用数字前缀控制排序：`01-`、`02-`、`03-`、`04-`
- 子目录用小写 kebab-case：`editing-techniques`、`custom-analysis`
- 禁止使用中文目录名

### 2.2 文件命名

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 风格档案 | `{creator/film}-style-guide.md` | `qmike-style-guide.md` |
| 剪辑手法 | `{technique-name}.md` | `j-cut.md`、`speed-ramp.md` |
| FFmpeg recipe | `{technique-name}.md` | `whip-pan-blur.md` |
| SCINE 翻译 | `{xx}-{name}.md`（数字前缀） | `01-setup.md` |
| 参考论文 metadata | `{arxiv-id}-{short-name}.md` | `2509.26555-scine.md` |
| 日志/报告 | 小写 kebab-case | `log.md`、`research-corpus-report.md` |

### 2.3 禁止

- 禁止文件名含空格
- 禁止使用中文文件名
- 禁止 `new_`、`v2_`、`final_` 这类版本后缀（用 git 管理版本）

---

## 3. Frontmatter Schema（必须符合的格式）

### 3.1 风格档案（`taxonomy/03-styles/`）

```yaml
---
name: {kebab-case-style-name}
description: |-
  一句话描述这个风格的核心特征和使用场景。
  英文优先（供跨语言 agent 调用），可附中文说明。
category: style
subcategory: {custom-analysis | from-shotdeck}
source:
  creator: {创作者名/影片名}       # 出处
  reference_works:                 # 代表作（至少1个）
    - "{作品名 or URL}"
  analysis_method: {manual | vision-api | shotdeck}
triggers:                          # agent 识别关键词
  - "{触发词1}"
  - "{触发词2}"
layer4_ready: {true | false}       # 是否已有反向分镜层（模式B需要）
last_updated: {YYYY-MM-DD}
---
```

**`layer4_ready: false` 的档案是不完整档案，不允许进入生产 pipeline。**

### 3.2 剪辑手法（`taxonomy/02-editing-techniques/`）

```yaml
---
name: {technique-name}
description: |-
  一句话定义这个手法。
category: {cut | transition | rhythm-pattern | narrative-structure}
complexity: {low | medium | high}    # 实现难度
requires_audio: {true | false}
ffmpeg_available: {true | false}     # 是否有对应 recipe
source:
  origin: "{出处：电影/创作者/学术论文}"
  first_documented: "{参考来源}"
last_updated: {YYYY-MM-DD}
---
```

### 3.3 FFmpeg Recipe（`taxonomy/04-ffmpeg-recipes/`）

```yaml
---
name: {recipe-name}
for_technique: {对应的手法名}
ffmpeg_version_tested: "{版本号}"    # 测试通过的 FFmpeg 版本
platform_tested: {macOS | Linux | Windows}
complexity: {low | medium | high}
last_updated: {YYYY-MM-DD}
---
```

### 3.4 任务卡（`_tasks/` 下所有文件）

```yaml
---
type: task
id: {kebab-case-id}
profile: {pm | researcher | engineer | reviewer}  # 分配给哪个分身
status: {pending | active | blocked | done}        # 当前状态
priority: {p0 | p1 | p2 | p3}                      # 优先级
parent_task: ~                                      # 父任务 ID（可为空）
depends_on: []                                      # 依赖的任务 ID 列表
context_summary: |-
  一句话描述这个任务要干什么。
created: {YYYY-MM-DD}
assigned_to: ~                                      # 当前谁在做
blocked_reason: ~                                   # 卡住原因（status=blocked 时必填）
last_updated: {YYYY-MM-DD}
---
```

**status 转换规则：**
```
created → pending → active → done
                  ↓
               blocked → active（解除后回到 active）
```
- `pending`：已创建但依赖未满足，或尚未分配
- `active`：正在执行，`assigned_to` 必填
- `blocked`：卡住等人决策，`blocked_reason` 必填
- `done`：已完成，`_tasks/done/` 下归档

**文件位置规则：**
- 待处理任务 → `_tasks/pending/{id}.md`
- 进行中任务 → `_tasks/active/{id}.md`
- 已完成任务 → `_tasks/done/{id}.md`
- 已审核任务 → `_tasks/reviewed/{id}.md`
- 不允许跨 status 目录放置文件

### 3.5 扫街报告（`_scout/` 下所有文件）

```yaml
---
type: scout-report
id: {kebab-case-id}
target: {影片名 or 手法类别 or 风格名}
method: {vision-analysis | manual-analysis | shotdeck-export}
verified_count: {N}            # 本报告验证了多少条目
total_examined: {N}            # 本报告检查了多少条目
coverage_pct: {NN}             # 百分比（int，如 68）
gaps_found:                     # 发现的缺口清单
  - "{缺口描述}"
key_findings: |-                # 关键发现，3–5 条要点
  - 发现1
  - 发现2
next_steps:                     # 下一步行动
  - "{下一步}"
last_updated: {YYYY-MM-DD}
---
```

---

## 4. 风格档案四层结构规范

每个 `taxonomy/03-styles/` 下的风格文件必须包含以下四个 Section，顺序固定：

```markdown
## Layer 1: 描述层（Description）
## Layer 2: 参数层（Parameters）
## Layer 3: 执行层（Execution）
## Layer 4: 反向分镜层（Shot Blueprint — 模式B专用）
```

### Layer 1: 描述层

- **目的：** 给人（和 agent）建立直觉。
- **必须包含：**
  - 整体视觉氛围（2–3句）
  - 标志性特征列表（可量化的优先）
  - 适用题材/场景
  - 代表性参考作品

### Layer 2: 参数层

- **目的：** 把 Layer 1 的形容词翻译成数字。
- **必须包含（适用的项）：**

| 参数类别 | 必须提供的字段 |
|---------|-------------|
| 色彩 | 色温（K）、色调、对比度偏移、饱和度偏移 |
| 镜头 | 平均镜头时长（s）、最大/最小值 |
| 运动 | 主要运镜方式 + 速度参数 |
| 构图 | 主要景别分布（%）、画幅比例 |
| 转场 | 各类转场使用比例（%）+ 时长（s） |
| 音频 | 音乐类型、音效处理、声画关系 |

### Layer 3: 执行层

- **目的：** 给 FFmpeg/DaVinci 直接可用的指令。
- **必须包含：**
  - 调色的 FFmpeg filtergraph 模板（或 DaVinci 节点配置）
  - 主要转场的 FFmpeg 命令
  - 速度处理命令（如有）
- **格式要求：** 代码块必须注明参数含义，不允许裸命令无注释。

```bash
# 示例格式
ffmpeg -i input.mp4 \
  -vf "eq=contrast=0.9:saturation=0.75:brightness=0.05,\
       colortemperature=temperature=5500" \
  # contrast: -10% | saturation: -25% | warm shift to 5500K
  output.mp4
```

### Layer 4: 反向分镜层（Shot Blueprint）

**这是模式 B 的核心。这一层的目的是：给定此风格，AI 能生成一张完整的拍摄计划表。**

必须包含：

#### 4.1 镜头类型清单

| 镜头类型 | 景别 | 角度 | 运动 | 参考时长 | 数量建议 | 内容要求 | 拍摄要点 | 失败信号 |
|---------|------|------|------|---------|---------|---------|---------|---------|
| 例：开场建立镜 | 广角/全景 | 低角度仰拍 | 缓慢推进 | 3–5s | 1–2个 | 环境/氛围 | 光线要侧逆光 | 正面平光=失败 |

**每个风格至少定义 5 种不同的镜头类型。**

#### 4.2 叙事结构模板

用于指导拍摄顺序和比例：

```
开场（Hook）：XX 类镜头，占总时长 YY%
主体（Body）：XX 类镜头，占总时长 YY%
高潮（Climax）：XX 类镜头，占总时长 YY%
收尾（Close）：XX 类镜头，占总时长 YY%
```

#### 4.3 最小可用素材集（MVP Shot List）

"如果只能拍 N 个镜头，必须拍哪些？"用于快速拍摄场景。

```
最少可用：{N} 个镜头
1. {镜头描述}
2. {镜头描述}
...
```

#### 4.4 风格守卫（Style Guards）

"这些信号表示拍摄方向错了"——让 AI 在素材验收时能判断是否符合风格。

```
✅ 合格信号：{1–3 条视觉特征，可量化}
❌ 失败信号：{1–3 条常见错误，对应 Layer 1 的违反}
```

---

## 5. 何时停下来问 Mr.Gao

以下情况**必须停下来问**，不允许自行决定：

| 情况 | 原因 |
|-----|------|
| 要删除任何现有文件 | 不可逆操作 |
| 要修改 SKILL.md 本身 | 项目宪法需要人审批 |
| 要修改 CLAUDE.md | 项目上车手册，修改影响所有 agent |
| 要改变 taxonomy/ 的目录结构 | 影响所有 agent 的文件引用 |
| 参数值无法从论文/影片/实测中找到出处 | 不允许猜测参数 |
| 一个任务预计需要创建超过 10 个文件 | 先对齐范围 |
| 发现 log.md 里有正在进行中的任务且不清楚状态 | 避免覆盖其他 agent 的工作 |
| 模式 B 的 Layer 4 字段设计有不确定性 | 核心护城河，不允许随意设计 |

**其他所有情况：直接执行，完成后更新 log.md。**

---

## 6. Git Commit 规范

### 格式

```
{type}({scope}): {subject}

{body - 可选，说明 why，不说 what}
```

### type 枚举

| type | 用途 |
|------|------|
| `feat` | 新增知识条目、新功能 |
| `add` | 新增文件（非功能性，如新论文、新参考） |
| `update` | 更新现有内容（参数修正、补充字段） |
| `fix` | 修正错误（错误参数、错误引用） |
| `refactor` | 目录/命名/结构调整（内容不变） |
| `docs` | 文档类（SKILL.md、CLAUDE.md、README.md） |
| `script` | 工具脚本（scripts/ 下） |
| `log` | 仅更新 log.md |

### scope 枚举

`taxonomy`、`references`、`scripts`、`app`、`docs`、`root`

### 示例

```
feat(taxonomy): add j-cut technique with ffmpeg recipe

update(taxonomy): upgrade qmike style to 4-layer schema with shot blueprint

docs(root): write SKILL.md project constitution

add(references): add FullShots dataset metadata
```

### 禁止

- 禁止 `update stuff`、`fix things`、`WIP` 这类无信息 commit
- 禁止一个 commit 混合多个不相关的文件修改
- 禁止直接 commit 到 main，除非是 solo 工作且改动量小

---

## 7. 多 Agent 冲突处理

### 冲突预防

- 每个 agent 开始工作前检查 `log.md`，确认没有其他 agent 正在操作同一文件
- `inbox/` 是各 agent 的通讯中介：放入 `inbox/{agent-name}-{date}-{topic}.md`
- 大规模批量操作前在 log.md 写入"Lock: {agent} 正在操作 {路径}，预计完成：{时间}"

### 冲突发生时

1. **两个 agent 都修改了同一文件** → 人工合并，保留两者有价值的内容，不允许 force push 覆盖
2. **Schema 不一致** → 以 SKILL.md 第 3 节为准，不以任何单个文件为准
3. **发现某个文件违反本规范** → 修正它，并在 log.md 记录修正原因

### inbox/ 使用规则

- 文件名格式：`{from-agent}-{YYYY-MM-DD}-{topic}.md`
- 每个 inbox 文件要有接收方标注：`To: {agent-name}`
- 读取后标注 `Status: read` 并在下次 log 更新时归档

---

## 8. 目录权威结构（当前版本）

```
open-edit/
├── taxonomy/
│   ├── 01-scine-translated/         SCINE 76 节点中文翻译
│   ├── 02-editing-techniques/       剪辑手法库
│   │   ├── 01-cuts/                 J-cut、L-cut、Match-cut...
│   │   ├── 02-transitions/          Whip pan、Speed ramp、Cross dissolve...
│   │   ├── 03-rhythm-patterns/      Beat-sync、Breath rhythm...
│   │   └── 04-narrative-structures/ 3-second hook、Reveal-payoff...
│   ├── 03-styles/                   风格模板库（每个含四层含 Layer 4）
│   │   ├── from-shotdeck/           ShotDeck 数据导出
│   │   └── custom-analysis/         人工/Vision 拆解（当前仅 qmike）
│   └── 04-ffmpeg-recipes/           FFmpeg 可执行参数模板（全部待填充）
│       ├── color-grading/
│       ├── cuts/
│       ├── transitions/
│       └── audio-sync/
├── _tasks/                           任务卡系统（按状态分目录）
│   ├── pending/                      待处理任务
│   ├── active/                       进行中任务
│   ├── done/                         已完成任务
│   └── reviewed/                     已审核任务
├── _scout/                           扫街报告库（手法验证/影片分析）
├── app/                             （待设计）本地 agent app
│   ├── pipeline/
│   │   ├── adaptive/                模式 A：素材驱动
│   │   └── directed/                模式 B：风格驱动（核心差异化）
│   └── analysis/                    学习 pipeline（参考视频 → 提取参数）
├── inbox/                           Agent 间通讯文件（每日清零）
├── outputs/                         pipeline 产出的剪辑 plan
├── references/                      原始研究语料
│   ├── papers/
│   ├── repos/
│   ├── web/
│   ├── INDEX.md
│   └── raw-claims.md
├── scripts/                         工具脚本
├── CLAUDE.md                        项目上车手册（新 agent 先读）
├── SKILL.md                         本文件
├── README.md                        对外说明
└── log.md                           历史进度日志
```

**创建新目录之前必须核对此结构，不允许在未列出的位置新建顶层目录。**

---

## 9. 知识质量标准

### 9.1 合格标准（允许合并进 taxonomy/）

- [ ] Frontmatter 完整且符合第 3 节 schema（可用 `scripts/validate-frontmatter.py` 自动校验）
- [ ] 所有参数有出处标注
- [ ] 风格档案：`layer4_ready: true`（含完整 Layer 4）
- [ ] FFmpeg recipe：已在本地测试通过（注明测试版本）
- [ ] 无形容词参数（"较快"/"偏暖"等）

### 9.2 不合格标准（退回修改）

- Frontmatter 缺失或字段不全
- 参数无出处，只有描述层
- 风格档案缺少 Layer 4
- FFmpeg 命令未经测试
- 中文文件名/目录名

### 9.3 frontmatter 自动校验

项目根目录下应维护一个 `scripts/validate-frontmatter.py`，用 Python yaml 模块+regex 遍历 taxonomy/ 下所有 .md 文件，自动检查：

1. 每个文件是否包含 YAML frontmatter
2. frontmatter 字段是否符合对应 file type 的 schema（第 3 节）
3. 必填字段是否缺失
4. 枚举字段是否在允许范围内（如 `status` 是否在 `draft | verified | locked` 中）
5. 检测到非法字段/格式 → 输出到 stderr，exit code = 1

**什么时候必须跑：**
- 每次 `_tasks/` 下某任务"ready for review"时
- 批量修改 taxonomy/ 后提交 git 前
- 新 agent 第一次接项目时先跑一次确认当前状态

### 9.4 FFmpeg Recipe 填充状态

当前 `taxonomy/04-ffmpeg-recipes/` 仅有目录骨架（全是 `.gitkeep` 占位符），**无任何可执行命令**。

填充优先级（对应手法文件的 ffmpeg_available 字段）：

| 优先级 | 手法 | 原因 |
|--------|------|------|
| P0 | color-grading 通用 LUT | 模式 B 调色 pipeline 的入口 |
| P0 | cross-dissolve、fade-to-black | 最基础转场，所有视频必用 |
| P1 | whip-pan、speed-ramp、montage-burst | 风格化的标志性转场 |
| P2 | 其余 cuts/ 和 transitions/ | 手法完整需要 |
| P3 | audio-sync/ | 音频处理独立模块 |

**一条 recipe 被标记 ffmpeg_available: true 前，必须有人在 Mac M4 Pro 上实际跑通过。**

---

## 10. log.md 更新规范

每次工作结束时，在 `log.md` 表格末尾追加一行：

```markdown
| {YYYY-MM-DD} | {做了什么，具体文件名} | {做了什么决定，或"无新决定"} | {下次接续什么} |
```

**不允许修改已有行。** 历史记录只增不改。

### 10.1 任务卡同步规则

log.md 有更新时，必须同步对应 `_tasks/` 下的状态：

| log.md 行为 | 对应 _tasks/ 操作 |
|-------------|------------------|
| 开启了新工作项 | 创建 `_tasks/pending/{id}.md` |
| 正在执行某项 | 移动文件到 `_tasks/active/{id}.md`，更新 frontmatter status |
| 完成某项 | 移动文件到 `_tasks/done/{id}.md`，status → done |
| 审核通过 | 移动文件到 `_tasks/reviewed/{id}.md` |
| 任务卡住了 | 更新 frontmatter status → blocked，填写 blocked_reason |

**规则：log.md 和 _tasks/ 的状态应始终保持同步。如果发现不一致，以 _tasks/ 下文件的 frontmatter 为准。**

---

*SKILL.md 版本：1.1*  
*创建：2026-05-13 by Cowork*  
*最后更新：2026-05-13 by Hermes（补 _tasks/_scout schema、frontmatter 校验脚本规范、ffmpeg-recipes 填充优先级、log-task 同步规则）*  
*下次审核：ffmpeg-recipes 开始填充时*
