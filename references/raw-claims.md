# Raw Claims — 剪辑手法分类清单（未加工原材料）

> ⚠️ 本文件是原始语料 dump，不做任何分析、比较、验证。
> 下一步由 Claude 做深度对比梳理。

---

## 1. CineTechBench — 7 维度电影摄影分类法

来源：arXiv:2505.15145

### 7 个核心维度（Core Dimensions）
1. Shot Scale（景别）
2. Shot Angle（拍摄角度）
3. Composition（构图）
4. Camera Movement（运镜）
5. Lighting（灯光）
6. Color（色彩）
7. Focal Length（焦距）

### 各维度子类（需从论文 Table/Figure 中提取详细清单）

#### Shot Scale
- Extreme Close-Up
- Close-Up
- Medium Close-Up
- Medium Shot
- Medium Full Shot
- Full Shot
- Long Shot
- Extreme Long Shot

#### Shot Angle
- High Angle
- Low Angle
- Eye Level
- Dutch Angle / Canted
- Bird's-Eye View
- Worm's-Eye View
- Over-the-Shoulder
- Point-of-View (POV)

#### Camera Movement
- Static / Fixed
- Pan (Left / Right)
- Tilt (Up / Down)
- Dolly / Tracking (Forward / Backward / Lateral)
- Zoom (In / Out)
- Dolly Zoom (Vertigo Effect)
- Handheld
- Steadicam
- Crane / Jib
- Whip Pan
- Truck

#### Composition
- Rule of Thirds
- Center Framing
- Symmetrical
- Asymmetrical
- Leading Lines
- Frame within Frame
- Deep Space
- Shallow Space
- Dutch Angle Composition

#### Lighting
- High Key
- Low Key
- Natural Light
- Artificial Light
- Hard Light
- Soft Light
- Backlight
- Side Light
- Three-Point Lighting
- Practical Light
- Chiaroscuro

#### Color
- Warm Palette
- Cool Palette
- Monochromatic
- Complementary
- Analogous
- Desaturated
- High Saturation
- Technicolor
- Noir

#### Focal Length
- Wide Angle (< 35mm)
- Normal (35mm–70mm)
- Telephoto (> 70mm)
- Fisheye
- Macro

> 注：以上子类部分来自标准电影摄影教科书，CineTechBench 论文中具体标注了哪些子类需要在论文正文校对。

---

## 2. SCINE — 76 节点层级分类法

来源：arXiv:2509.26555

### 4 大支柱（Pillars）

#### A. Setup（场景设置）
- Location / Environment
  - Interior
  - Exterior
  - Fantasy / CGI
- Props
  - Key Props
  - Background Props
- Set Dressing
- Time Period
  - Historical
  - Contemporary
  - Futuristic
- Weather / Atmosphere
  - Rain
  - Snow
  - Fog
  - Sunny
  - Cloudy
  - Night

#### B. Event（事件/叙事）
- Action / Motion
  - Character Action
    - Standalone (walk, run, sit, etc.)
    - Interactive (fight, hug, talk, etc.)
  - Object Motion
    - Natural (wind, water, etc.)
    - Mechanical (vehicle, machine, etc.)
- Portrayed As
  - Emotion / Expression
  - Age
  - Gender
  - Occupation
- Interaction Type
  - Solo
  - Duo
  - Group
  - Crowd

#### C. Lighting（灯光）
- Lighting Style
  - Naturalistic
  - Stylized
  - High Key
  - Low Key
- Light Source
  - Natural (sun, moon)
  - Artificial (practical, studio)
  - Mixed
- Light Direction
  - Front
  - Side
  - Back
  - Top
  - Under
- Light Quality
  - Hard
  - Soft
  - Diffused
- Color Temperature
  - Warm
  - Cool
  - Neutral
  - Mixed

#### D. Camera（镜头）
- Shot Scale
  - Extreme Long Shot
  - Long Shot
  - Full Shot
  - Medium Full Shot
  - Medium Shot
  - Medium Close-Up
  - Close-Up
  - Extreme Close-Up
- Camera Angle
  - High Angle
  - Low Angle
  - Eye Level
  - Dutch Angle
  - Overhead
  - POV
- Camera Movement
  - Static
  - Pan
  - Tilt
  - Dolly / Track
  - Truck
  - Pedestal
  - Crane
  - Handheld
  - Steadicam
  - Zoom
  - Rack Focus
- Lens / Focal Length
  - Wide
  - Normal
  - Telephoto
  - Macro
  - Fisheye
  - Anamorphic
- Depth of Field
  - Deep Focus
  - Shallow Focus
  - Rack Focus
- Aspect Ratio
  - 1.33:1 (Academy)
  - 1.85:1 (Widescreen)
  - 2.35:1 (Anamorphic)
  - 16:9 (HD)
  - 4:3
  - 1:1 (Square)
  - 9:16 (Vertical)

> 总计：76 个叶子节点（leaf-level nodes），论文 Figure 2 有完整树状图。

---

## 3. Cinematic2K / CameraDiff — 20 种细分类别

来源：arXiv:2412.12223

### 20 种细分类别（20 Fine-Grained Categories）
（需从论文正文提取完整列表，以下为已知类别）

#### Camera Movement Patterns
- Static Shot（固定镜头）
- Pan Left（左摇）
- Pan Right（右摇）
- Tilt Up（上摇）
- Tilt Down（下摇）
- Tracking Forward（前进）
- Tracking Backward（后退）
- Lateral Tracking（横移）
- Crane Up（升）
- Crane Down（降）
- Zoom In（推）
- Zoom Out（拉）
- Handheld Shake（手持抖动）
- Whip Pan（甩镜头）

#### Motion Intensity Levels
- Static (no motion)
- Slow
- Medium
- Fast
- Rapid

> 注：论文全名 "CameraDiff: Learning Camera Motion Priors for Video Generation"，20 个细分类别包含 14 种运镜模式 + 6 种强度层级。需阅读 paper.pdf 确认精确列表。

---

## 4. FullShots / LWSRNet — 8 类运镜 + 6 类景别

来源：DOI:10.1038/s41598-023-43281-w （Scientific Reports）
参考书：Daniel Arijon, "Grammar of the Film Language" (1976)

### 8 类运镜（Shot Movement / Camera Motion）
1. Static / Fixed（固定镜头）
2. Pan（摇镜头）
3. Tilt（俯仰）
4. Zoom（变焦）
5. Dolly / Track（推拉/轨道）
6. Handheld（手持）
7. Steadicam（斯坦尼康）
8. Crane（升降）

（原始分类为4类：Static, Pan, Tilt, Zoom — FullShots 扩展至8类，在论文"Shot categories"节有详细定义）

### 6 类景别（Shot Scale）
1. Extreme Long Shot（大远景）
2. Long Shot（远景）
3. Full Shot（全景）
4. Medium Shot（中景）
5. Close-Up（特写）
6. Extreme Close-Up（大特写）

（原始分类为5类：无 Extreme Close-Up — FullShots 增加至6类）

### 数据集规模
- 27,000 个镜头
- 19 部电影
- 专业标注（movement + scale）

---

## 5. MovieShots / SGNet — 5 类景别 + 4 类运镜

来源：arXiv:2008.03548

### 5 类景别（Shot Scale）
1. Long Shot (LS) — 远景
2. Full Shot — 全景
3. Medium Shot — 中景
4. Close-Up — 特写
5. Extreme Close-Up — 大特写

### 4 类运镜（Shot Movement / Camera Motion）
1. Static — 固定镜头（camera is fixed but subject may move）
2. Pan — 摇镜头（camera rotates horizontally/vertically）
3. Zoom — 变焦（focal length change）
4. Tracking / Dolly — 跟拍（camera physically moves）

### 数据集规模
- 46,000+ 个镜头
- 7,858 部电影
- 论文 Table 1 有与其它数据集的对比

---

## 6. CineLOG — 17 类运镜 + 15 类电影类型

来源：arXiv:2512.12209

### 17 类运镜（Camera Movements）
1. Static
2. Pan
3. Tilt
4. Pan-Tilt Combo
5. Zoom In
6. Zoom Out
7. Dolly Forward
8. Dolly Backward
9. Lateral Track / Truck
10. Arc / Orbit
11. Crane Up
12. Crane Down
13. Handheld
14. Steadicam
15. Whip Pan
16. Crash Zoom
17. Rack Focus / Pull Focus

### 15 类电影类型（Film Genres）
1. Action
2. Adventure
3. Comedy
4. Drama
5. Horror
6. Sci-Fi
7. Romance
8. Thriller
9. Mystery
10. Fantasy
11. Animation
12. Documentary
13. Musical
14. Western
15. War

### 标注格式
- 〈Shot Init, Camera Movement, Shot End〉 三元组
- 每个运镜有初始/结束视角描述

---

## 7. Seedance 1.0 — ByteDance 视频生成技术报告

来源：arXiv:2506.09113

（论文主要关注视频生成质量，非专门分类法研究。可能包含的镜头控制维度待 Claude 阅读后提取。）

---

## 8. Open-Sora 2.0

来源：arXiv:2503.09642

（主要关注开源视频生成模型架构，非分类法研究。）

---

## 9. Open-Sora Plan

来源：arXiv:2412.00131

（主要关注视频生成高效化方案，非分类法研究。）

---

## 10. Camera Artist

来源：arXiv:2604.09195

（推测包含自动运镜控制方面的分类体系，待 Claude 阅读后提取。）

---

## 11. LAVE

来源：arXiv:2402.10294

（Learned Action and View Embeddings，涉及视角控制，具体分类待 Claude 提取。）

---

## 12. Prompt-Driven Agentic Video Editing

来源：arXiv:2509.16811

（基于提示词驱动的智能视频编辑，涉及剪辑知识应用，具体分类待提取。）

---

## 13. Cutscene Agent

来源：arXiv:2604.25318

（多智能体协作生成过场动画，涉及镜头组合规则，具体分类待提取。）

---

## 14. MiraData

来源：arXiv:2407.06358

（大规模视频数据集+细粒度标注，包含的标注维度待 Claude 提取。）

---

## 已知的交叉引用分类体系（未下载论文）

### ShotDeck 标注体系
ShotDeck（https://shotdeck.com）包含电影画面的帧级标注，涵盖：
- Shot Size（景别）
- Camera Angle（角度）
- Camera Movement（运镜）
- Lighting Style（灯光风格）
- Color Palette（色板）
- Lens Type（镜头类型）
- Set Design（场景设计）
- Costume（服装）
- Mood / Tone（情绪）

标注格式完整，约 150,000+ 张电影剧照。

### MovieNet 分类
来源：MovieNet — arXiv:1906.01527
- 3 个层次：Scene（场景）→ Shot（镜头）→ Frame（帧）
- Shot-level 标注包含 shot types 和 camera motions

### CineStyle
（待确认 DOI/arXiv ID）
- 电影风格分类
- 涉及色彩、灯光、景深的风格维度

### Cinemetrics
来源：Cinemetrics 理论（不是论文，是电影学术分析框架）
- Shot Length Distribution（镜头长度分布）
- Average Shot Length (ASL)
- Cut Frequency
- Motion Magnitude
- Color Variance

---

## 核心分类维度对比（仅列维度名，不做分析）

| 论文 | 分类维度 |
|------|---------|
| CineTechBench | scale, angle, composition, movement, lighting, color, focal length |
| SCINE | Setup, Event, Lighting, Camera (76 leaf nodes) |
| Cinematic2K | 20 fine-grained camera motion categories |
| FullShots | 8 movement + 6 scale categories |
| MovieShots | 5 scale + 4 movement categories |
| CineLOG | 17 camera movements + 15 genres |
| ShotDeck | shot size, angle, movement, lighting, color, lens, set, costume, mood |

---

## 未解决的开放问题（供 Claude 下一步梳理时参考）

1. CineTechBench 每个维度下的具体子类清单需要从论文 Table/Figure 精确提取
2. Cinematic2K 的 20 个细分类别的精确命名需要确认
3. SCINE 的 76 个叶子节点中，哪些与 Open Edit Library 的 editing-techniques/ 对应，哪些不相关
4. ShotDeck 的数据格式是否可以直接映射到 style 模板中
5. MovieShots 和 FullShots 的标注 schema 差异点（是否可以合并为标准标注格式）
6. CineLOG 的 17 类运镜是否有 FFmpeg 可执行参数映射
