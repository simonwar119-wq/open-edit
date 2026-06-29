# Taxonomy 知识库结构总览

> 本文件是 `taxonomy/` 的导航图。字段标准见 `00-schema-v1.md`。  
> 更新时间：2026-05-13

---

## 知识库逻辑结构

```
taxonomy/
├── 00-overview.md          ← 本文件：目录导航
├── 00-schema-v1.md         ← 字段标准（所有文件的枚举值从这里取）
│
├── 01-scine-translated/    单镜头属性（SCINE 翻译 + 扩展）
├── 02-editing-techniques/  剪辑手法（Open Edit 核心贡献，学术界空白）
├── 03-styles/              风格档案（四层结构，含 Layer 4 反向分镜）
└── 04-ffmpeg-recipes/      FFmpeg 可执行参数模板
```

---

## 各模块说明

### 01-scine-translated/（单镜头属性库）

**来源：** SCINE（arXiv:2509.26555）76 节点层级树 + Open Edit 扩展  
**覆盖：** 景别 / 角度 / 运镜 / 灯光 / 焦距 / 色彩 / 构图 / 景深  
**用途：**
- 模式 A：分析用户素材的镜头属性
- 模式 B：生成分镜表时指定每个镜头的属性
- 知识基础：所有风格档案的参数层（Layer 2）引用此模块的枚举值

**标准字段枚举：** 见 `00-schema-v1.md` 第 1–2 节

---

### 02-editing-techniques/（剪辑手法库）

**来源：** Open Edit 独有，学术界空白（所有论文只研究单镜头，不研究镜头之间关系）  
**覆盖：** 切法 / 转场 / 节奏模式 / 叙事结构

```
02-editing-techniques/
├── 01-cuts/                J-cut, L-cut, match-cut, jump-cut...
├── 02-transitions/         hard-cut, whip-pan, speed-ramp, cross-dissolve...
├── 03-rhythm-patterns/     beat-sync, breath-rhythm, accelerando...
└── 04-narrative-structures/ hook-3s, reveal-payoff, in-medias-res...
```

**用途：**
- 模式 A：识别用户素材中出现的剪辑手法，匹配推荐风格
- 模式 B：在分镜表中为每个镜头标注应采用的剪辑手法

**每个手法文件结构：** frontmatter（schema）+ 定义 + 参数 + FFmpeg recipe 链接 + 使用场景 + 来源出处

---

### 03-styles/（风格档案库）

**分支：**
```
03-styles/
├── from-shotdeck/          基于 ShotDeck 数据统计生成（电影/广告镜头属性分布）
└── custom-analysis/        人工 + Doubao Vision 拆解（短视频创作者风格）
```

**每个风格文件必须含四层：**

| Layer | 名称 | 作用 | 主要字段 |
|-------|------|------|---------|
| Layer 1 | 描述层 | 建立直觉，给人读 | 氛围描述、代表作、适用场景 |
| Layer 2 | 参数层 | 形容词翻译成数字 | 色温、时长、运镜类型、转场比例… |
| Layer 3 | 执行层 | 给工具直接用 | FFmpeg filtergraph、DaVinci 配置 |
| Layer 4 | 反向分镜层 | 模式 B 的入口 | shot_blueprint（镜头类型、叙事结构、MVP 清单、风格守卫）|

**`layer4_ready: false` 的档案不进入生产 pipeline。**

---

### 04-ffmpeg-recipes/（FFmpeg 参数模板库）

```
04-ffmpeg-recipes/
├── color-grading/          调色命令（暖色/冷色/电影感/LUTS 模拟）
├── transitions/            转场命令（whip-pan, speed-ramp, dissolve）
└── styles/                 完整风格的组合命令
```

**每个 recipe 文件必须：**
- 标注测试通过的 FFmpeg 版本
- 所有参数有注释说明（单位 + 含义）
- 链接到对应的手法或风格档案

---

## 两个模式的调用路径

### 模式 A（素材驱动）

```
用户素材
  → 01-scine-translated/ 识别镜头属性
  → 02-editing-techniques/ 识别剪辑手法
  → 03-styles/ 匹配最相近风格
  → 04-ffmpeg-recipes/ 输出剪辑 plan
```

### 模式 B（风格驱动 / 导演模式）

```
用户选定风格 → 03-styles/{style}.md Layer 4
  → shot_blueprint.shot_types → 生成镜头拍摄清单
  → shot_blueprint.narrative_structure → 生成拍摄顺序和比例建议
  → shot_blueprint.mvp_shot_list → 生成最小可用拍摄方案
  → 用户拍摄
  → shot_blueprint.style_guards → AI 验收素材
  → 04-ffmpeg-recipes/styles/ → 剪辑输出
```

---

## 当前档案状态

### Style 档案
| 档案 | 路径 | Layer4 | 状态 |
|-----|------|--------|------|
| Qmike Cinematic | `03-styles/custom-analysis/qmike-style-guide.md` | ❌ 待升级 | 有 Layer 1-3，需补 Layer 4 + 字段规范化 |

### Editing Techniques 档案（✅ 已全部填充，28个文件）

| 子目录 | 文件数 | 状态 |
|-------|-------|------|
| `01-cuts/` | 8 | ✅ 含 splitscreen-match-cut 新增 |
| `02-transitions/` | 6 | ✅ 含 cross-dissolve, speed-ramp, whip-pan 等 |
| `03-rhythm-patterns/` | 7 | ✅ 含 beat-sync, accelerando, decelerando 等 |
| `04-narrative-structures/` | 7 | ✅ 含 hook-3s, reveal-payoff, circular-ending 等 |

> **P2 任务：** 用 `00-schema-v1.md` 的字段标准升级 `qmike-style-guide.md`，作为所有后续档案的标杆样例。

---

## 知识库增长路线图

```
当前（2026-05-13）：
  ✅ schema 设计完成（00-schema-v1.md）
  ✅ editing-techniques 批量填充完成（28文件，来自Nike/Apple/Honda/Qmike分析）
  ⚠️ qmike 样例待升级
  ⏳ 风格档案批量创建待启动

近期（待确认）：
  → 你审阅第一批 editing-techniques 档案质量，反馈修正
  → qmike-style-guide.md 升级为四层结构（匹配schema v1字段标准）
  → splitscreen-match-cut 入库验证（Nike 样例跑通）

中期：
  → 03-styles/from-shotdeck/：王家卫、Wes Anderson 等电影导演（需ShotDeck抓取）
  → 03-styles/custom-analysis/：李子柒、Tasty 等短视频创作者
  → 04-ffmpeg-recipes/ 与每条手法全部对齐

长期：
  → app/pipeline/directed/ 接入 Layer 4 实现模式 B
```
