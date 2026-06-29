# Open Edit 统一分类法 v1

> 基于 7 套学术/行业分类体系的对比梳理，定义 Open Edit taxonomy/ 的字段标准。  
> 所有 taxonomy/ 文件的参数字段**必须使用本文档定义的枚举值**，不允许自造词。  
> 版本：v1.0 | 创建：2026-05-13

---

## 0. 分析来源

| 来源 | 类型 | 核心维度 | 节点数量 |
|-----|------|---------|---------|
| CineTechBench (arXiv:2505.15145) | 学术评测基准 | scale, angle, composition, movement, lighting, color, focal_length | 7 维 ~60 子类 |
| SCINE (arXiv:2509.26555) | 最完整层级分类 | Setup, Event, Lighting, Camera | 76 叶节点 |
| CineLOG (arXiv:2512.12209) | 运镜分类最细 | 17 类运镜 + 15 类电影类型 | 32 类 |
| Cinematic2K/CameraDiff (arXiv:2412.12223) | 运镜 + 强度 | 14 类运镜 × 5 强度 | 20 细分 |
| FullShots/LWSRNet (Scientific Reports) | 大规模标注 | 8 类运镜 + 6 类景别 | 14 类 |
| MovieShots/SGNet (arXiv:2008.03548) | 基础分类 | 4 类运镜 + 5 类景别 | 9 类 |
| ShotDeck | 行业标注 | shot size, angle, movement, lighting, color, lens, set, costume, mood | 9 维 |

**关键发现：** 所有论文的共识集中在"单个镜头的属性"（景别/角度/运镜/灯光/色彩/焦距）。没有一篇论文覆盖**剪辑手法**（J-cut、L-cut、match-cut 等）和**叙事结构**。这正是 Open Edit 的空白填补空间，也是 `taxonomy/02-editing-techniques/` 存在的理由。

---

## 1. 共识维度（所有/大多数来源认同）

这些维度是稳定知识，直接采用，不需要决策。

---

### 1.1 Shot Scale（景别）

**共识程度：** ★★★★★（所有来源）  
**Open Edit 标准：** 采用 SCINE 的 8 级，最细粒度，兼容所有简化版本。

| 代码 | 中文 | 英文 | 画面范围 |
|-----|------|------|---------|
| `ECU` | 大特写 | Extreme Close-Up | 面部局部（眼、口）或物体细节 |
| `CU` | 特写 | Close-Up | 面部全部 / 物体主体 |
| `MCU` | 中特写 | Medium Close-Up | 胸部以上 |
| `MS` | 中景 | Medium Shot | 腰部以上 |
| `MFS` | 中全景 | Medium Full Shot | 膝盖以上 |
| `FS` | 全景 | Full Shot | 全身 |
| `LS` | 远景 | Long Shot | 人 + 环境，人占 1/3 以下 |
| `ELS` | 大远景 | Extreme Long Shot | 以环境为主，人极小或不可见 |

**向下兼容：** MovieShots（5类）= CU/MS/FS/LS/ELS；FullShots（6类）= CU/MS/FS/LS/ELS + ECU。

---

### 1.2 Camera Angle（拍摄角度）

**共识程度：** ★★★★☆（CineTechBench / SCINE / ShotDeck）  
**Open Edit 标准：** 采用 CineTechBench 的 8 类，加入 SCINE 的 Overhead。

| 代码 | 中文 | 英文 | 说明 |
|-----|------|------|------|
| `eye-level` | 平视 | Eye Level | 摄影机与主体视线同高 |
| `high-angle` | 俯拍 | High Angle | 摄影机高于主体向下拍 |
| `low-angle` | 仰拍 | Low Angle | 摄影机低于主体向上拍 |
| `birds-eye` | 鸟瞰 | Bird's-Eye View | 正上方 90° 俯拍 |
| `worms-eye` | 虫视 | Worm's-Eye View | 正下方 90° 仰拍 |
| `dutch-angle` | 荷兰角 | Dutch Angle / Canted | 摄影机倾斜，水平线不水平 |
| `ots` | 过肩 | Over-the-Shoulder | 从一人肩后拍另一人 |
| `pov` | 主观视角 | Point-of-View | 模拟角色眼睛看到的视角 |

---

### 1.3 Camera Movement（运镜）

**共识程度：** ★★★★★（所有来源，但粒度差异最大）  
**Open Edit 标准：** 采用 CineLOG 的 17 类，最完整，且区分了 Zoom In/Out、Crane Up/Down 等方向细分。

| 代码 | 中文 | 英文 | 说明 | FFmpeg 可模拟 |
|-----|------|------|------|-------------|
| `static` | 固定 | Static | 摄影机不动（主体可动） | ✅ |
| `pan-left` | 左摇 | Pan Left | 水平向左旋转 | ✅ |
| `pan-right` | 右摇 | Pan Right | 水平向右旋转 | ✅ |
| `tilt-up` | 上仰 | Tilt Up | 垂直向上旋转 | ✅ |
| `tilt-down` | 下俯 | Tilt Down | 垂直向下旋转 | ✅ |
| `dolly-forward` | 前推 | Dolly Forward | 摄影机物理前移 | ✅（zoom 模拟） |
| `dolly-backward` | 后拉 | Dolly Backward | 摄影机物理后移 | ✅（zoom 模拟） |
| `truck` | 横移 | Lateral Track / Truck | 摄影机平行横向移动 | ✅ |
| `arc` | 环绕 | Arc / Orbit | 绕主体圆弧运动 | ⚠️（后期模拟） |
| `crane-up` | 升镜 | Crane Up | 摄影机垂直上升 | ✅ |
| `crane-down` | 降镜 | Crane Down | 摄影机垂直下降 | ✅ |
| `handheld` | 手持 | Handheld | 无支撑手持，自然抖动 | ✅（模拟抖动） |
| `steadicam` | 斯坦尼康 | Steadicam | 机械稳定器，流畅跟随 | ✅（稳定后模拟） |
| `zoom-in` | 推焦 | Zoom In | 焦距变化，非物理移动 | ✅ |
| `zoom-out` | 拉焦 | Zoom Out | 焦距变化，向外 | ✅ |
| `whip-pan` | 甩镜 | Whip Pan | 极速水平旋转，画面模糊 | ✅ |
| `rack-focus` | 焦点转移 | Rack Focus / Pull Focus | 焦点从一个主体移到另一个 | ✅ |

**运动强度（来自 Cinematic2K）：** 在描述运镜时可附加强度参数：
`intensity: slow | medium | fast | rapid`

---

### 1.4 Lighting（灯光）

**共识程度：** ★★★★☆（CineTechBench / SCINE / ShotDeck）  
**Open Edit 标准：** 采用 SCINE 的四维结构，比 CineTechBench 的平铺更利于 agent 查询。

#### 灯光风格 `lighting.style`
| 代码 | 中文 | 说明 |
|-----|------|------|
| `high-key` | 高调 | 整体明亮，阴影极少 |
| `low-key` | 低调 | 主体明亮，大面积阴影，戏剧感 |
| `naturalistic` | 自然主义 | 模拟真实自然光效果 |
| `stylized` | 风格化 | 刻意的、非写实的灯光设计 |
| `chiaroscuro` | 明暗对照 | 极端明暗对比（Rembrandt 风格） |

#### 光源类型 `lighting.source`
| 代码 | 说明 |
|-----|------|
| `natural` | 太阳、月亮等自然光 |
| `artificial` | 灯具（摄影棚/实景灯） |
| `practical` | 场景内的真实光源（台灯、霓虹、屏幕） |
| `mixed` | 多种光源混合 |

#### 光线方向 `lighting.direction`
`front` / `side` / `back` / `top` / `under` / `rim`

#### 光线质感 `lighting.quality`
`hard` / `soft` / `diffused`

#### 色温 `lighting.color_temperature`
数值优先（开尔文 K），枚举备用：`warm（>5000K）` / `neutral（4000–5000K）` / `cool（<4000K）`

---

### 1.5 Focal Length / Lens（焦距/镜头）

**共识程度：** ★★★★☆（CineTechBench / SCINE / ShotDeck）  
**Open Edit 标准：** 数值优先，枚举作补充。

| 代码 | 中文 | 焦距范围（全画幅等效） | 视觉特征 |
|-----|------|------------------|---------|
| `wide` | 广角 | < 35mm | 透视夸张，景深深，空间感强 |
| `normal` | 标准 | 35–70mm | 接近人眼视角 |
| `telephoto` | 长焦 | > 70mm | 压缩空间，浅景深 |
| `macro` | 微距 | 任意（近摄） | 极近距离细节 |
| `fisheye` | 鱼眼 | < 14mm | 圆形畸变，超广视野 |
| `anamorphic` | 变形镜头 | 任意 | 椭圆 bokeh，水平耀斑 |

---

### 1.6 Color（色彩）

**共识程度：** ★★★☆☆（CineTechBench / ShotDeck，但学术分类较粗）  
**Open Edit 标准：** 分三层表达，越精确越好。

| 层级 | 字段 | 值类型 | 示例 |
|-----|------|-------|------|
| 色温（数值） | `color.temperature_k` | 整数 | `5200` |
| 调色倾向（枚举） | `color.palette` | 枚举 | `warm` / `cool` / `neutral` / `desaturated` / `monochromatic` / `teal-orange` / `noir` |
| 主色调（HEX） | `color.dominant_hex` | 字符串列表 | `["#F5E6CA", "#3A2A1A"]` |
| 饱和度偏移 | `color.saturation_offset` | 整数（-100~+100） | `-20`（降饱和） |
| 对比度偏移 | `color.contrast_offset` | 整数（-100~+100） | `-15`（低对比） |

---

## 2. 边缘维度（仅部分来源提到，需决策）

---

### 2.1 Composition（构图）

**出处：** CineTechBench（仅此一家显式定义），ShotDeck 隐式包含。  
**Open Edit 决策：** ✅ 纳入，作为风格档案的可选字段。构图是"每一帧为什么好看"的答案，对模式 B（分镜表）必要。

| 代码 | 中文 | 说明 |
|-----|------|------|
| `rule-of-thirds` | 三分法 | 主体在 1/3 或 2/3 线上 |
| `center-framing` | 中心构图 | 主体居中，常配合对称 |
| `symmetrical` | 对称 | 画面左右或上下对称 |
| `leading-lines` | 引导线 | 线条将视线引向主体 |
| `frame-in-frame` | 框架中的框架 | 窗/门/树枝等形成天然画框 |
| `deep-space` | 深空间 | 强调前/中/后三个景深层次 |
| `shallow-space` | 浅空间 | 平面化，背景不可辨 |
| `negative-space` | 负空间 | 大面积留白衬托主体 |

---

### 2.2 Depth of Field（景深）

**出处：** SCINE。  
**Open Edit 决策：** ✅ 纳入，用数值（光圈等效值）优先，枚举备用。

| 字段 | 值类型 | 示例 |
|-----|-------|------|
| `dof.aperture_equiv` | 数值（f/x.x） | `f/1.8` |
| `dof.style` | 枚举 | `deep` / `shallow` / `rack` |

---

### 2.3 Aspect Ratio（画幅比例）

**出处：** SCINE。  
**Open Edit 决策：** ✅ 纳入，作为风格档案的元信息字段（影响模式 B 的分镜格式）。

| 代码 | 比例 | 主要用途 |
|-----|------|---------|
| `9:16` | 0.5625 | 短视频 / TikTok / Reels / Shorts |
| `1:1` | 1.0 | Instagram 正方形 |
| `16:9` | 1.778 | YouTube 横屏 / 传统视频 |
| `1.85:1` | 1.85 | 电影院宽银幕 |
| `2.35:1` | 2.35 | 变形镜头电影（超宽） |
| `4:3` | 1.333 | 复古电视比例 |

---

### 2.4 Genre / Context（适用场景）

**出处：** CineLOG（15 类电影类型）、ShotDeck（mood/tone）。  
**Open Edit 决策：** ✅ 纳入，但使用短视频导向的分类，不用电影类型。

| 代码 | 说明 |
|-----|------|
| `food` | 美食、烹饪、餐饮 |
| `travel` | 旅行、风景、城市探索 |
| `lifestyle` | 日常生活、vlog |
| `portrait` | 人像、情绪 |
| `sport` | 运动、健身 |
| `brand` | 商业广告、品牌宣传 |
| `narrative` | 有情节的短片 |
| `music` | MV、音乐视频 |

---

## 3. Open Edit 独有维度（所有论文均未覆盖）

这是 Open Edit 对影视知识库的核心贡献，必须自己定义。

---

### 3.1 Editing Technique Type（剪辑手法类型）

对应 `taxonomy/02-editing-techniques/`。论文只标注单镜头，从不标注**镜头之间的剪辑关系**。

#### 3.1.1 Cut（切法）

| 代码 | 中文 | 定义 |
|-----|------|------|
| `straight-cut` | 直切 | 两个镜头直接相接，无任何过渡 |
| `j-cut` | J 剪 | 下一个镜头的音频先于画面进入 |
| `l-cut` | L 剪 | 上一个镜头的音频延续进入下一画面 |
| `match-cut` | 匹配剪辑 | 两个镜头在形状/动作/色彩上有视觉匹配 |
| `jump-cut` | 跳切 | 同一主体的时间跳跃，刻意制造不连续感 |
| `smash-cut` | 硬切 | 从安静/慢节奏突然切到快/强烈的镜头 |
| `cross-cut` | 交叉剪辑 | 在两个同时发生的场景之间交替切换 |
| `eyeline-match` | 视线匹配 | 角色看向某方向 → 切到被看的事物 |
| `splitscreen-match` | 分屏匹配 | 多画面同框，通过动作/构图匹配连接 |

#### 3.1.2 Transition（转场）

| 代码 | 中文 | 持续时长（典型） | FFmpeg |
|-----|------|--------------|--------|
| `hard-cut` | 硬切 | 0s | ✅ |
| `cross-dissolve` | 叠化 | 0.3–0.8s | ✅ |
| `whip-pan-transition` | 甩镜转场 | 0.1–0.2s | ✅ |
| `speed-ramp` | 速度坡道 | 0.3–0.8s | ✅ |
| `zoom-transition` | 推拉转场 | 0.1–0.3s | ✅ |
| `match-cut-transition` | 匹配转场 | 0s（视觉连续） | ✅ |
| `light-flash` | 白闪 | 0.1–0.3s | ✅ |
| `blackout` | 黑场 | 0.3–1.0s | ✅ |
| `dip-to-color` | 渐变至色块 | 0.3–0.5s | ✅ |

#### 3.1.3 Rhythm Pattern（节奏模式）

| 代码 | 中文 | 定义 |
|-----|------|------|
| `beat-sync` | 节拍同步 | 剪辑点与音乐节拍对齐 |
| `breath-rhythm` | 呼吸节奏 | 快剪 + 长呼吸帧交替 |
| `accelerando` | 渐快 | 镜头时长逐渐缩短，制造紧张感 |
| `decelerando` | 渐慢 | 镜头时长逐渐增长，走向平静 |
| `montage-burst` | 蒙太奇爆发 | 极短镜头密集切换（<0.5s/镜头） |

#### 3.1.4 Narrative Structure（叙事结构）

| 代码 | 中文 | 定义 |
|-----|------|------|
| `hook-3s` | 三秒钩子 | 前 3 秒必须抓住观众 |
| `reveal-payoff` | 铺垫-揭示 | 先藏信息，后揭示 |
| `problem-solution` | 问题-解决 | 呈现冲突 → 展示结果 |
| `chronological` | 线性叙事 | 按时间顺序 |
| `in-medias-res` | 倒叙开场 | 从结果/高潮开始，再补充前因 |

---

### 3.2 Shot Duration（镜头时长）

**所有论文均未标注**（只研究"什么"，不研究"多久"）。  
**Open Edit 字段：**

| 字段 | 类型 | 说明 |
|-----|------|------|
| `duration.avg_s` | 浮点数 | 风格的平均镜头时长（秒） |
| `duration.min_s` | 浮点数 | 最短镜头时长 |
| `duration.max_s` | 浮点数 | 最长镜头时长 |
| `duration.asl` | 浮点数 | Average Shot Length，Cinemetrics 标准指标 |

---

### 3.3 Audio-Visual Relationship（声画关系）

**所有论文均不涉及**（纯视觉研究）。  
**Open Edit 字段：**

| 字段 | 枚举值 | 说明 |
|-----|-------|------|
| `audio.music_drive` | `strong` / `moderate` / `weak` | 音乐驱动剪辑节奏的程度 |
| `audio.sync_type` | `beat-sync` / `lyric-sync` / `free` | 剪辑点与音乐的对齐方式 |
| `audio.sound_design` | `ambient` / `minimal` / `rich` | 音效层的丰富程度 |
| `audio.bpm_range` | 整数范围 | 适配的音乐 BPM 区间，如 `[90, 120]` |

---

### 3.4 Shot Blueprint Fields（反向分镜层 — 模式 B 专用）

**本维度是 Open Edit 对行业的独特贡献，全球无参照。**

每个风格档案的 Layer 4 必须包含以下结构化字段：

```yaml
shot_blueprint:
  shot_types:                    # 该风格需要的镜头类型清单
    - id: "{镜头类型代码}"
      scale: "{景别代码}"          # 1.1 节枚举
      angle: "{角度代码}"          # 1.2 节枚举
      movement: "{运镜代码}"       # 1.3 节枚举
      movement_intensity: "{强度}" # slow/medium/fast/rapid
      duration_s: [min, max]       # 时长区间
      count_per_video: [min, max]  # 每条视频建议数量
      composition: ["{构图代码}"]  # 2.1 节枚举（可多选）
      dof_style: "{景深代码}"      # 2.2 节枚举
      content_brief: "{内容要求}"  # 拍什么
      shooting_notes: "{拍摄要点}" # 怎么拍
      failure_signals:             # 什么情况说明拍错了
        - "{失败信号1}"
        - "{失败信号2}"

  narrative_structure:           # 叙事结构模板
    hook:
      shot_type_ids: []
      duration_pct: 0            # 占总视频时长百分比
    body:
      shot_type_ids: []
      duration_pct: 0
    climax:
      shot_type_ids: []
      duration_pct: 0
    close:
      shot_type_ids: []
      duration_pct: 0

  mvp_shot_list:                 # 最小可用镜头集
    min_shots: 0
    shots:
      - "{镜头简述}"

  style_guards:
    pass_signals:
      - "{合格信号}"
    fail_signals:
      - "{失败信号}"
```

---

## 4. 维度采用决策总表

| 维度 | 采用 | 来源 | 字段前缀 | 优先级 |
|-----|------|------|---------|-------|
| Shot Scale（景别） | ✅ 必须 | SCINE（8级） | `scale` | P0 |
| Camera Angle（角度） | ✅ 必须 | CineTechBench（8类） | `angle` | P0 |
| Camera Movement（运镜） | ✅ 必须 | CineLOG（17类） | `movement` + `movement_intensity` | P0 |
| Lighting（灯光） | ✅ 必须 | SCINE（4维） | `lighting.*` | P0 |
| Focal Length / Lens（焦距） | ✅ 必须 | SCINE（6类） | `lens` | P0 |
| Color（色彩） | ✅ 必须 | 数值优先 | `color.*` | P0 |
| Composition（构图） | ✅ 推荐 | CineTechBench（8类） | `composition` | P1 |
| Depth of Field（景深） | ✅ 推荐 | SCINE | `dof.*` | P1 |
| Aspect Ratio（画幅） | ✅ 推荐 | SCINE | `aspect_ratio` | P1 |
| Genre / Context（场景） | ✅ 推荐 | 自定义 | `genre` | P1 |
| Shot Duration（时长） | ✅ 必须 | Open Edit 独有 | `duration.*` | P0 |
| Editing Technique（手法） | ✅ 必须 | Open Edit 独有 | `technique_type` | P0 |
| Transition（转场） | ✅ 必须 | Open Edit 独有 | `transition.*` | P0 |
| Rhythm Pattern（节奏） | ✅ 推荐 | Open Edit 独有 | `rhythm.*` | P1 |
| Narrative Structure（叙事） | ✅ 推荐 | Open Edit 独有 | `narrative.*` | P1 |
| Audio-Visual（声画关系） | ✅ 推荐 | Open Edit 独有 | `audio.*` | P1 |
| Shot Blueprint（反向分镜） | ✅ 必须 | Open Edit 独有（模式B） | `shot_blueprint.*` | P0 |
| Film Genre（电影类型） | ❌ 不采用 | CineLOG | — | — |
| Set Design / Costume | ❌ 不采用 | SCINE / ShotDeck | — | — |
| Mood / Tone（情绪词汇） | ⚠️ 仅描述层 | ShotDeck | Layer 1 only | — |

> **不采用原因：** Film Genre 服务电影分类，与短视频创作无关。Set Design / Costume 是拍摄条件而非风格特征，不利于 agent 参数化调用。Mood/Tone 是形容词，只允许出现在 Layer 1 描述层，不允许进入 Layer 2 参数层。

---

## 5. 枚举值快查索引

使用方式：在 taxonomy/ 文件的 YAML frontmatter 或参数层表格中，**只使用以下代码值**，不自造词。

```
scale:      ECU | CU | MCU | MS | MFS | FS | LS | ELS
angle:      eye-level | high-angle | low-angle | birds-eye | worms-eye | dutch-angle | ots | pov
movement:   static | pan-left | pan-right | tilt-up | tilt-down | dolly-forward | dolly-backward |
            truck | arc | crane-up | crane-down | handheld | steadicam | zoom-in | zoom-out |
            whip-pan | rack-focus
intensity:  slow | medium | fast | rapid
light_style: high-key | low-key | naturalistic | stylized | chiaroscuro
light_source: natural | artificial | practical | mixed
light_dir:  front | side | back | top | under | rim
light_quality: hard | soft | diffused
lens:       wide | normal | telephoto | macro | fisheye | anamorphic
dof:        deep | shallow | rack
aspect:     9:16 | 1:1 | 16:9 | 1.85:1 | 2.35:1 | 4:3
genre:      food | travel | lifestyle | portrait | sport | brand | narrative | music
cut:        straight-cut | j-cut | l-cut | match-cut | jump-cut | smash-cut | cross-cut |
            eyeline-match | splitscreen-match
transition: hard-cut | cross-dissolve | whip-pan-transition | speed-ramp | zoom-transition |
            match-cut-transition | light-flash | blackout | dip-to-color
rhythm:     beat-sync | breath-rhythm | accelerando | decelerando | montage-burst
narrative:  hook-3s | reveal-payoff | problem-solution | chronological | in-medias-res
composition: rule-of-thirds | center-framing | symmetrical | leading-lines | frame-in-frame |
             deep-space | shallow-space | negative-space
```

---

## 6. 与 Qmike 风格档案的对应关系

当前 `qmike-style-guide.md` 已有 Layer 1–3，但字段不符合本 schema。升级时的字段映射：

| 当前描述 | → | schema 字段 | 值 |
|---------|---|------------|-----|
| "warm golden-hour" | → | `color.palette` | `warm` |
| "5200–5800K" | → | `color.temperature_k` | `5200–5800` |
| "f/1.4–f/2.8 equivalent" | → | `dof.aperture_equiv` | `f/1.4–f/2.8` |
| "0.8–1.5s per shot" | → | `duration.avg_s` | `1.1` |
| "80% hard cuts" | → | `transition.hard_cut_pct` | `80` |
| "slow push-in" | → | `movement` + `intensity` | `dolly-forward` + `slow` |
| "rule of thirds" | → | `composition` | `[rule-of-thirds, negative-space]` |

---

*版本：v1.0 | 创建：2026-05-13*  
*下次更新：Nike 广告样例跑完后，基于实测结果验证并修订*
