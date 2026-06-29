# Higgsfield 复刻情报包 — 可直接抄进 open-edit

> 给「对话里一句话出电影级片」工作流复刻用。尽量保留原文（verbatim），分六大块。
> 主要来源：
> - GitHub skill（MIT 协议，**可直接 fork**）：<https://github.com/OSideMedia/higgsfield-ai-prompt-skill>
> - FrankX MCP 工作流：<https://www.frankx.ai/blog/ultimate-higgsfield-workflow-2026>
> - 官方 Seedance 2.0 prompt guide：<https://higgsfield.ai/blog/seedance-prompting-guide>
> - 官方相机预设页：<https://higgsfield.ai/camera-controls>
> - Kolbo 相机预设清单：<https://kolbo.ai/blog/higgsfield-suite-100-camera-presets>
> - 官方新手指南：<https://higgsfield.ai/blog/how-to-make-ai-videos-beginners-guide>

---

## 0. 一句话总览：这套体系怎么跑

Higgsfield 的「一句话出片」= **MCSLA 五层公式** 构造 prompt + **命名相机预设/Motion 预设** 当镜头语言宏 + **Soul ID** 锁角色一致性 + **Seedance 2.0 / Cinema Studio** 当生成引擎 + **DISCIPLINE 框架** 管迭代纪律。GitHub 上那个 skill 把整套打包成 20 个子技能 + 17 个模板，可直接 fork。

执行层分三条路（任选其一，prompt 构造层不变）：
- **CLI**（终端 agent 首选，Claude Code 用这个）：`higgsfield generate create kling3_0 --prompt "..." --aspect_ratio 16:9 --duration 8 --wait`
- **MCP**（claude.ai web / 桌面端）：连接器 URL `https://mcp.higgsfield.ai/mcp`
- **Bundled skills**：`npx skills add higgsfield-ai/skills`

---

## ① Higgsfield 完整出片工作流（分步）

### 1A. Claude Code + Higgsfield MCP 配置（来自 FrankX）

> 注意：FrankX 文章给的是 claude.ai 连接器配法，不是 Claude Code 的 `.mcp.json`。两个 URL 有出入，**以官方 README 的 `https://mcp.higgsfield.ai/mcp` 为准**。

FrankX 配置步骤：
1. 打开 Claude **Settings → Connectors**
2. 点 **Add custom connector**，命名 `Higgsfield`
3. 粘贴 server URL：`https://mcp.higgsfield.ai`（README 版本带 `/mcp` 后缀）
4. 点 **Connect**，OAuth 认证
5. 权限设为 **Always Allow**

> 配好后 Claude 能调平台上所有模型 —— Veo 3.1、Sora 2、Kling 3.0、Seedance 2.0、Wan 2.6、MiniMax Hailuo，加上自家 Soul 和 Cinema 模型。

FrankX 给的唯一示例 prompt（原文）：
> *"Generate a 6-second cinematic shot of rain on a neon street, Kling 3.0, 16:9."*

FrankX 的两条工作流（原文照搬）：

**短片工作流（Cinematic short-form）：**
1. Write shot list (three to six shots) — 写 3–6 镜的分镜表
2. Set keyframe with image model — 用图像模型定关键帧
3. Apply camera preset — 套相机预设
4. Route by cost (Kling for B-roll, Veo/Sora for hero shots) — 按成本路由（Kling 跑 B-roll，Veo/Sora 跑 hero 镜）
5. Cut and grade outside Higgsfield — 在外部剪辑调色

**角色一致系列（Soul ID）：**
1. Build Soul ID once — 建一次 Soul ID
2. Reference it in every shot — 每镜引用
3. Vary scene/camera, hold character — 变场景/镜头，锁角色
4. Batch the episode — 批量出整集

### 1B. skill 内部端到端链路（来自 README，原文）

```
USER:    "Make me a cinematic chase scene through a night market.
          Use my trained Soul character — reference_id abc123."
   ↓
THIS SKILL — higgsfield-ai-prompt-skill
   • routes to higgsfield-prompt + higgsfield-camera + higgsfield-soul
   • picks Kling 3.0 (character-focused, supports --soul-id)
   • applies MCSLA: model, camera preset, subject, look, action
   • appends shared negative constraints
   • outputs a production-grade Higgsfield prompt
   ↓
PRE-FLIGHT (optional, recommended for Veo / Kling / Sora / Seedance video):
   SCHEMA VERIFY:   higgsfield model get kling3_0      (CLI)
                    models_explore(action="get", model_id="kling3_0")  (MCP)
   COST ESTIMATE:   generate_video(..., get_cost: true)               (MCP)
                    higgsfield generate cost kling3_0 --prompt "..." --aspect_ratio 16:9 --duration 8  (CLI)
   ↓
HIGGSFIELD STACK — 三选一执行：
   CLI:   higgsfield generate create kling3_0 --prompt "..." --aspect_ratio 16:9 --duration 8 --wait
   Skills: /higgsfield:generate
   MCP:   Claude invokes the Higgsfield connector with the prompt as input
   ↓
USER:    Result URL returned. Iterate if needed.
```

> 关键不变量：**this skill 永远只产 prompt，Higgsfield stack 永远只负责生成调用**。三条执行路径都不回头碰 prompt 构造。

### 1C. 官方网页 image-to-video 新手 5 步（来自官方新手指南）

1. **Account Setup** — 注册免费账号，免费额度够测前几条，无需信用卡
2. **Upload or Create Your Image** — 上传高清图或用内置生图。图是整条视频的视觉锚，要清晰主体、干净背景、强光照
3. **Select Camera Preset/Motion Style** — 在 motion control 面板选镜头运动预设（新手友好，选一个平台自动配好）
4. **Write Your Prompt** — 打开 "Enhance" 按钮，平台自动把基础 prompt 扩成电影级描述
5. **Configure Settings and Generate** — 选宽高比（YouTube/影院用 16:9），点 generate

> 备注：原 Scribehow 两个链接现已失效（410/404），以上步骤来自官方等价指南。

---

## ② MCSLA 公式 + DISCIPLINE 框架（原文 + 解释）

### MCSLA 公式（原文表格）

> Every high-performing Higgsfield prompt is built on five layers. Think of it as the cinematographer's checklist — fill in each layer and the model has everything it needs.

| Letter | Element | Description | Example |
|--------|---------|-------------|---------|
| **M** | Model | Which generation engine | "Use Kling 2.6" |
| **C** | Camera | Named camera control | "FPV Drone shot weaving through the alley" |
| **S** | Subject | Who/what + appearance | "A woman in a sand-colored suit, sharp eyes" |
| **L** | Look | Style + color + lighting | "Cinematic, golden hour, anamorphic flare" |
| **A** | Action | What happens in the scene | "She turns slowly, wind lifting her coat" |

**关键操作规则（来自 prompt skill QUICK FACTS，原文要点）：**
- I2V：只描述「动/变」的东西，绝不描述图里已有的静态元素
- prompt 控制在 200 词内；Cinema Studio 硬上限 512 字符
- 1 镜 1 主动作，1–2 个次要动作封顶；快动作易崩 → 慢动作生成再后期加速（Fast Motion Trick）
- 绝不留泛化情绪（"sad"/"angry"）→ 拆成肌肉动作、呼吸、眼神、皮肤
- Soul ID/复现角色：每条 prompt 拆成 **Identity Block + Motion Block**，绝不混
- 子技能冲突优先级：**显式用户指令 > 场景原型 > 情绪同步**
- 宽高比是 per-model 枚举，写在 UI/header，**绝不写进 prompt 正文**
- 绝不在一镜内同时 Dolly In + Dolly Out
- 每次重生成只改**一个变量**
- Seedance：短 prompt（30–100 词）赢；Subject + Action 必须落在前 20–30 词
- 杀 slop 词（beautiful/stunning/epic/amazing）→ 换具体视觉/物理
- Seedance/CS 3.0 **无 negative-prompt 语法** → 用正向约束表达
- 引擎限制：跨镜最多追踪 ≤3 角色；出框=消失；离屏=不存在；避免反射镜头
- 每个 cut 必须**同时**改变景别 AND 相机性格（Double-Contrast Cut Rule）
- Age-blind 规则：绝不用 boy/girl/child/kid/young/teen/little，按角色/服装/动作描述
- 场景默认「已在进行中」（in medias res），除非用户说 "starts with…"/"ends with…"

### DISCIPLINE 框架 —— 9 模式 × 3 层（来自 DISCIPLINE.md，原文）

> 来源说明：源于 2026 Cannes 一部 90 分钟 AI 长片的生产周期（五技能、十五人、十四天）。三层：workflow（怎么写）、output（产什么）、architectural（多步怎么组合）。

**Tier 1 — Workflow Discipline（工作流纪律）**
1. **Pre-Prompt Confirmation Gate** — 写长 prompt 前先短确认意图；卡住时宁可问一个窄问题，别问三个开放问题
2. **Explicit-Stop Between Phases** — 多阶段工作流不塌缩成一次回复；每阶段产出一个下阶段消费的 artifact
3. **Inventory-Extraction Checklist** — 写之前先静默盘点：谁/哪里/做什么/什么相机/什么情绪
4. **Iteration-is-craft** — 迭代消耗就是工作本身。生产级 AI-cinema 跑在约 **1% 图片接受率 / 1.5% 视频接受率**；把每个被拒的 take 当失败，项目第 7 天就死
5. **Lock-before-generate** — 在 prompt 之前锁定 subject/scene/camera/lighting/coverage，不在迭代循环中临时定
6. **Plausibility-over-verification** — 别用训练知识猜「平台通常怎么工作」，跑那个就在手边的验证命令（如 `higgsfield model get kling3_0`）
7. **Falsifiable Success Criteria** — 生成前用可证伪的话定义「好输出」长什么样，给迭代循环一个停止条件
8. **Log-Every-Generation** — 每次生成（保留/拒绝/被flag）都进 ledger 一行，遵守「5 秒规则」：最多一条短命令或一个问题

**Tier 2 — Output Discipline（输出纪律）**
1. **Visual-Marker-Only** — 用可见标记（服装/体型/姿态/动作/发型）描述角色对象，不用专名/年龄标签/不可观察属性
2. **Triple-Redundant Runtime** — 时长出现在标题、meta header、每镜计时标签三处，必须一致且分镜求和=总时长
3. **Single-Variable Iteration** — 每次重生成只改一个变量，否则诊断不可能
4. **Systematic-vs-Stochastic Fork（Iterate or Batch）** — 系统性失误（每次同样崩）→ 迭代；随机性失误（约1.5%接受率下大多是方差）→ 锁 prompt 后 **batch-and-cull**（跑 N 个相同 roll 选最优）
5. **Vision-Grounded Diagnosis** — 手里有被拒帧时，用视觉 pass 从画面提 reject_reason；视觉只「建议」，人确认
6. **BAD/GOOD/GREAT** — 把质量梯度并排展示，对比才教得会
7. **Skill-with-baked-context** — skill 自带它需要的上下文（命名工具/决策标准/反模式目录/范例），不让用户补
8. **Anti-Bombast** — 生产指挥语域。避免营销腔/表演式紧迫/假自信/形容词堆。把 `epic/beautiful/cinematic masterpiece/ultra realistic/dramatic` 换成命名物理机制（`low-angle 35mm anamorphic medium shot`、`warm practical key light from screen-left`）

**Tier 3 — Architectural Discipline（架构纪律）**
1. **3-Stage Chain / 4-Phase Loop** — 多步分解成命名阶段：3 段链（character → image → video）或 4 段循环（script → assets → blocking → prompts）
2. **Closing-Block-Baked-Into-Every-Prompt** — 共享文本片段（如 negative constraints）追加到每条 prompt，定义一次、不重写地应用
3. **Strict-Order Workflow** — 顺序工作流强制次序，第 N+1 步在第 N 步批准前不能开始
4. **Pre-Delivery Discipline** — 交付前跑自修复 pass（对照常见失败模式清单），60–90 秒，省的钱跨迭代复利

---

## ③ Seedance 2.0 在 Higgsfield 里的各 prompt 模式

### 3A. Filter 模型（核心心智，来自 seedance skill，原文要点）

> Seedance 2.0 的内容过滤器 **不是关键词黑名单**，是一个把整条 prompt 当一个场景读、判断意图与上下文的语言模型。
> - **读起来像导演描述一个镜头的 prompt** → 倾向通过
> - **读起来像给朋友的便条的 prompt** → 倾向失败
>
> 实操规则：prompt 必须描述一个 **scene**，不是一个 **subject**。先修语域，再修词。

**Instant Fail vs Delayed Fail 诊断（原文表）：**

| 失败时机 | 含义 | 怎么办 |
|----------|------|--------|
| **< 10 秒（instant）** | 内容过滤器拒绝，prompt 没到 GPU | 改语域 + 去风险 token，别原样重试 |
| **> 30 秒（delayed）** | 基础设施/超时/复杂度，过滤器过了但渲染失败 | 降低动作密度、削减长度、重试 |

### 3B. 六槽公式（Six-Slot Formula，原文）

```
[Camera movement] + [Subject] + [Action] + [Setting] + [Style] + [Lighting]
```
> 六槽全有的 prompt 几乎不被 flag，因为过滤器有完整上下文。缺 3+ 槽就是 flag 来源。

**最小可用 Seedance prompt（原文）：**
> Slow dolly-in on a figure in a dark overcoat standing alone at the end of a rain-slick alley. Cold teal shadows, single practical streetlamp, shallow depth of field.

### 3C. 五种 Prompt Modes（平台机制，原文骨架）

**1. Reference-Based** — 围绕承载视觉身份的源图建场景，把主体放进新动作/场景/运动语境。任何需要跨镜一致角色的序列的主力模式。
```
[Source image role: "as the main character" / "as the starting frame"].
[Action the subject performs]. [Environment and atmosphere if not visible in source].
[Camera movement]. [Lighting cue if different from source].
```

**2. Continuation** — 从上一条生成的最后一帧往后延续时间，身份/服装/环境/情绪状态全部继承。只描述「接下来」发生什么，绝不描述「刚才」。
```
[Continuing from prior clip]. [New action that follows from the last frame].
[Camera direction for the continuation]. [Any state change — light shift, new beat].
```

**3. Expand Shot** — 扩展画布/空间范围，把帧边界往外推露出更多场景（不是时间延展、不是镜内 zoom-out）。
```
[Source frame reference]. Extend the scene [direction: outward / upward / leftward].
[What appears in the newly revealed area]. [Preserve the original subject/composition].
```

**4. Edit Shot** — 定点修改现有生成的特定元素，其余全锁。Keep Rule：永远在说改什么的同时说留什么。
```
Change [specific element] to [new state]. Keep [everything else] unchanged.
[Preserve identity, composition, lighting, and camera behavior from the original.]
```

**5. Transformation** — 单镜内的显式状态变化（主体/物体/环境在一镜时长内可见地变成别的）。必须是一条连续弧、不是 cut，要显式描述中间态。5–8 秒是甜区。
```
[Subject in starting state — full identity descriptors]. [Triggering moment or cue].
[Subject mid-transformation — what visibly changes, in observable physical terms].
[Subject in ending state — new identity descriptors].
[Camera behavior across the change]. [Lighting / palette shift if any].
```

**Mode Selection Rule（原文）：** Reference-Based 用于既有角色的新动作；Continuation 用于下一时间拍；Expand Shot 用于横向加宽；Edit Shot 用于补丁细节；Transformation 用于「变化本身就是内容」。如果你发现一条 prompt 横跨多个 mode —— 停，选一个，生成，再把输出当下个 mode 的输入。

### 3D. Continuation 五条规则（原文）

1. **Last-frame anchor** — 开头一句描述上一镜末帧相机看到什么（姿势/位置/视线方向）
2. **Identity anchor** — 把角色 identity block 逐字粘进来，不改写不缩短
3. **Prior clip as secondary memory** — 一句话点明刚发生什么（"following the door opening"），不细描
4. **Immediate continuation** — 从上一镜末帧的下一帧开始，无时间跳/淡入/隐性 cut（除非用户要）
5. **No action repeat** — 新 prompt 必须延展不循环；上镜末若是「拔枪」，续镜描述「拔枪之后干什么」

### 3E. 工作模式 vs Prompt 模式（两套分类，原文映射表）

| Working mode（用户意图） | Typical prompt mode(s)（平台机制） | Reference roles |
|---------------|---------------------------------------|----------------------------------------|
| Exploration   | Reference-Based, or pure T2V          | Character (optional)                   |
| Continuation  | Continuation                          | Character + Last-Frame                 |
| Bridging      | Reference-Based or Continuation       | Character + Last-Frame + Environment   |
| Repair        | Edit Shot, or fresh Reference-Based   | Character + (failed-shot reference)    |

**Reference Roles（4 种语义角色）：** Character（锁身份）/ Last-Frame（锚续镜起点）/ Environment（锁世界设定）/ Prop（锁特定复现物体）。句柄 `@Image1/@Image2/...` 按上传顺序分配，每镜固定角色分配。

### 3F. Seedance 引擎硬约束（来自 prompt skill，原文要点）

- **≤3 角色跨镜追踪**；超过 Seedance 丢失身份
- **出框=隐性 cut**：角色离框后本镜剩余时间内就没了，绝不在同一连续镜内编排「出框+再入框」
- **离屏=不存在**：状态变化必须在镜头上演示后才能引用
- **避免反射镜头**（刀/水洼/镜子）：Seedance 渲反射时会破坏场景几何
- **只描述看得见/听得到的**：无气味、味道、内心想法
- **Micro-expressions 当物理写**：✅ "jaw clenches, nostrils flare" ❌ "looks angry"
- **意图+命名技术，不写生物力学**：✅ "spinning back kick connects" ❌ 关节角度描述
- **Double-contrast cut rule（强制）**：每个 cut 同时改景别 AND 相机性格。景别尺度 `extreme wide → wide → medium → MCU → close-up → ECU`；相机性格 `Handheld | Static | Stabilized tracking | Crane | Aerial`，跨 cut 不重复

### 3G. 官方 Seedance 2.0 prompt structure（来自官方 guide）

官方推荐结构顺序：
1. **Shot specification upfront** — 镜数、总时长、宽高比写最前
2. **Camera behavior** — 相机在做什么 AND **不在做什么**
3. **Visual aesthetic** — 胶片质感、灯光、调色
4. **Location/environment**
5. **Character actions** — beat-by-beat 编排
6. **VFX details** — 用 `[VFX: description]` 括号记法
7. **SFX/audio**（可选）
8. **Timing breakdown** — 用时间戳分段

> 关键引用：*"Be explicit about what the camera is NOT doing. 'No cuts, no zoom, natural head movement' — that instruction alone is what keeps the perspective locked."*

**官方 worked prompt 片段（原文摘录，照搬当模板种子）：**

- **Transformation — The Burger（15s, 6 镜）：** *"Montage, multi-shot action Hollywood movie, don't use one camera angle or single cut, cinematic lighting, photorealistic, 35mm film quality... A pink-haired girl with glasses sits on the hood of a white pickup truck under a concrete overpass... A pale zombie sprints toward her from the shadows... The girl calmly sets down the burger, her body erupts into a massive pale tusked creature... devours the zombie whole, then shrinks back to human form and picks up the burger."*

- **Orb — Electro（15s, 1 连续镜）：** *"Single continuous shot, first-person POV perspective, the camera IS her eyes, hyper-chaotic handheld motion, completely unstabilized, violent raw human movement... her hand snaps forward catching a crackling violet lightning sphere... [VFX: branching electric circuits pulsing with white-blue current, sparks jumping between fingers]"*

- **POV — Gladiator（15s, 1 镜）：** *"One continuous shot, POV gladiator perspective in the Colosseum arena, no cuts, no zoom, natural head movement, a furious enemy warrior sprints straight toward the camera through thick dust and sunlight... grabs him mid-charge and slams him violently onto the sand, powerful impact, dust explosion"*

- **Fight — Train（15s, 1 镜）：** *"Single continuous shot 15s: The camera begins below the train roof level — an extreme low angle looking up from beneath the rushing steel edge... The FPV arm accelerates upward and crests the rooftop edge just as both female samurai sprint into frame from opposite ends of the carriage roof... the camera dropping to roof level and sweeping immediately into a full 360-degree orbit around both fighters"*

### 3H. 中文 prompt 注意

ZH prompt 硬上限 **1,800 字符**；ZH antislop 列表由 linter 强制。预检命令：
```
python3 seedance_lint.py --preflight --model seedance_2_0 "<prompt>"
```
原生 4K 仅 `mode=std`；`mode=fast` 封顶 480p/720p；Cinema Studio 内该模型封顶 1080p。

---

## ④ 100+ 相机预设全清单（DoP 预设库复刻用）

### 4A. 官方 camera-controls 页全名单（66 个，verbatim）

> 来源 <https://higgsfield.ai/camera-controls>，这是最全的命名预设清单：

```
General, Eyes In, Bullet Time, Aerial Pullback, Arc Left, Arc Right, BTS, Buckle Up,
Car Chasing, Car Grip, Crane Down, Crane Over The Head, Crane Up, Crash Zoom In,
Crash Zoom Out, Dolly In, Dolly Left, Dolly Out, Dolly Right, Dolly Zoom In,
Dolly Zoom Out, Double Dolly, Dutch Angle, Eating Zoom, Fisheye, Flying Cam Transition,
Focus Change, FPV Drone, Glam, Handheld, Head Tracking, Hero Cam, Hyperlapse, Incline,
Jib down, Jib up, Lazy Susan, Low Shutter, Mouth In, Object POV, Overhead, Pan Left,
Pan Right, Rapid Zoom In, Rapid Zoom Out, Road Rush, Robo Arm, Snorricam, Static,
Super Dolly In, Super Dolly Out, Through Object In, Through Object Out, Tilt Down,
Tilt up, Timelapse Glam, Timelapse Human, Timelapse Landscape, Whip Pan, Wiggle,
YoYo Zoom, 360 Orbit, Zoom In, Zoom Out, 3D Rotation
```

### 4B. 带运镜含义的预设库（来自 GitHub camera skill，原文表，复刻 DoP 库直接抄）

**Dolly Movements**
| 预设 | 含义 | 最适合 | Prompt 短语 |
|------|------|--------|-------------|
| Dolly In | 平滑直线推向主体 | 亲密、揭示、张力累积 | "Camera Dolly In toward her face" |
| Dolly Out | 平滑直线拉离主体 | 孤立、离去、扩展语境 | "Camera Dolly Out revealing the empty square" |
| Dolly Left | 向左横移轨道 | 跟随水平移动、揭示场景 | "Camera Dolly Left tracking alongside the runner" |
| Dolly Right | 向右横移轨道 | 跟随水平移动 | "Camera Dolly Right as the car accelerates" |
| Dolly Zoom In | 前推+变焦拉远同时（希区柯克眩晕） | 眩晕、震惊、顿悟 | "Dolly Zoom In — subject stays size as background rushes away" |
| Dolly Zoom Out | 后拉+变焦推近同时 | 压倒、孤立、世界逼近 | "Dolly Zoom Out — city swallows the figure" |
| Super Dolly In | 夸张快速冲向主体 | 突然震惊、紧急揭示 | "Super Dolly In on the handprint on the window" |
| Super Dolly Out | 夸张快速拉回 | 戏剧化揭示规模 | "Super Dolly Out to reveal the entire burning city" |

**Crane / Vertical**
| 预设 | 含义 | 最适合 |
|------|------|--------|
| Crane Up | 从地/主体高度升起 | 揭示范围、亲密→宏大 |
| Crane Down | 从高处下降 | 从上方引入地点、个人化 |
| Crane Over The Head | 正上方俯瞰、神视角 | 脆弱、监视、编排 |
| Levitation | 平滑向上漂浮、梦境感 | 神秘、超越、出体 |

**Orbit / Arc**
| 预设 | 含义 | 最适合 |
|------|------|--------|
| 360 Orbit | 绕主体整圈 | 情绪孤立、戏剧强调 |
| Arc | 绕主体半圆扫 | 揭示、情绪转折 |
| Lazy Susan | 慢转盘、主体居中 | 产品、角色介绍、服装展示 |
| Robo Arm | 精密机械弧、复杂路径 | 编排镜头、产品揭示 |

**Zoom Effects**
| 预设 | 含义 |
|------|------|
| Crash Zoom In | 快速突然推近 → 震惊、强调细节 |
| Crash Zoom Out | 快速突然拉远 → 断联、突然扩展语境 |

**Follow / Action**
| 预设 | 含义 |
|------|------|
| FPV Drone | 快速灵活无人机穿梭 → 追逐、空中动作、动能 |
| Action Run | 跟在奔跑主体后的低位跟拍 → 追逐、逃跑 |
| Handheld | 有机手持晃动感 → 纪录片真实、亲密、混乱 |
| Head Tracking | 锁定角色头部运动 → 第一人称强度、迷失 |
| Snorricam | 相机固定在演员身上、背景摇晃 → 压力、醉酒、强化情绪 |

**Specialty / Cinematic**
| 预设 | 含义 |
|------|------|
| Bullet Time | 主体冻结/慢动、相机环扫 → 动作高潮、冲击瞬间 |
| Dutch Angle | 对角倾斜 → 心理张力、不稳、恐惧 |
| Fisheye | 广角畸变 → 超现实、滑板、实验 |
| Whip Pan | 快速横向模糊摇 → 动态转场 |
| Overhead | 正顶俯视 → 编排、空间关系、脆弱 |

**Time-Based**
| 预设 | 含义 |
|------|------|
| Hyperlapse | 移动相机+延时合成 → 城市变迁、旅行 |
| Timelapse Human | 固定相机+人类活动快进 → 日常、城市脉搏 |
| Timelapse Landscape | 固定相机+自然延时 → 天气变化、四季、日出日落 |
| Low Shutter | 慢门、快速运动拖影 → 速度、紧迫、醉态 |

**Through-Object**
| 预设 | 含义 |
|------|------|
| Through Object In | 穿过窄物进入新空间 → 揭秘、创意转场 |
| Through Object Out | 从窄空间穿出露出外部 → 密闭→开阔转场 |
| Mouth In | 推入角色张开的嘴 → 超现实转场、进入记忆/梦 |

**Specialty Vehicle / Action**
| 预设 | 含义 |
|------|------|
| Car Chasing | 低位地面跟拍疾驰车辆 → 高速追逐 |
| Car Grip | 相机装车上随车 → 沉浸式车内 |
| Buckle Up | 颠簸湍流式晃动 → 颠簸、失控 |

**Pitch & Perspective — 相机角度**
Low Angle（仰拍，权力/英雄）、High Angle（俯拍，脆弱/渺小）、Eye Level（平视，对话）、Bird's-Eye View（正顶向下）、Worm's-Eye View（极低仰）、Ground Level（贴地）、Canted Angle Left/Right（荷兰倾斜左/右）、Static Oblique（斜角离轴）、Over-the-Shoulder OTS（过肩）、POV / First Person（第一人称）、Two-Shot（双人同框）、Cowboy Shot（牛仔位，大腿中以上）

**Shot Sizes（景别）**
Extreme Long Shot (ELS)、Long Shot / Wide Shot (LS/WS)、Medium Long Shot / Cowboy (MLS)、Medium Shot (MS)、Medium Close-Up (MCU)、Close-Up (CU)、Extreme Close-Up (ECU)、Insert Shot

### 4C. 相机组合规则（原文）

| 组合 | 效果 | 例子 |
|------|------|------|
| Dolly In + Dutch Angle | 逼近张力+不稳 | 反派揭示 |
| Crane Up + 360 Orbit | 史诗规模揭示+孤立 | 终战收尾 |
| FPV Drone + Crash Zoom In | 动能+突然聚焦 | 追逐高潮 |
| Handheld + Action Run | 原始真实+追逐紧迫 | 逃跑段落 |

**避免冲突运镜：** 别在同一镜组合 Dolly In + Dolly Out、Crane Up + Crane Down。
**顺序 vs 同时：** 同时=两运动并发；顺序=带时间戳分段（"Camera pans left from 0-3s tracking the character, holds, then pushes in on the face from 4-8s"）。
**Static pan vs glide：** pan 是固定位旋转，glide 是穿空间平移；生产实践多数覆盖偏好 static-pan。

### 4D. Camera-Emotion Sync（镜头=焦点角色情绪的替身，原文表）

| 焦点角色情绪 | 相机处方 |
|---|---|
| 愤怒/暴怒/张力/紧绷 | Handheld breathing，抖动不稳，碎呼吸节奏，双轴微抽搐，小幅，无规律。避免稳定器 |
| 冷静/掌控/自信 | Handheld breathing，平滑，稳定呼吸率，规律微幅。轻稳定但仍有生命 |
| 悲伤/脆弱 | Handheld，慢，低；更低呼吸频率，轻微下漂，操作者重量感更重 |
| 震惊/揭示 | Static + 极慢推近或拉远；揭示瞬间锐冻，之后 0.5-2s 极少运动 |
| 动作 | 60fps，180° 快门；干净动态+快门绑定动态模糊 |
| 终局/裁决 | Top-shot freeze，0.3-0.5s；正上方，时间停止，所有位置锁定 |
| 情绪崩溃/角色需要空间 | 从中/近景慢拉到广景 —— "leave the character alone"，给视觉距离=情绪空间 |

### 4E. Motion 预设库（VFX 宏，来自 motion skill，100+ 个，节选）

用法：`[Your scene description.] Apply the [Preset Name] preset.`

- **变身/身体类：** Animalization, Werewolf, Cyborg, Turning Metal, Disintegration, Gas Transformation, Clone Explosion, Monstrosity, X-Ray, Freezing, Tattoo Animation, Hair Style, Luminous Gaze, Black Tears, Head Off, Head Explosion, Duplicate, Ghoulgao
- **元素类：** Air/Water/Earth Bending, Earth Wave, Fire/Water/Earth/Air Element, Firelava, Explosion, Building Explosion, Plasma Explosion, Atomic, Flame On, Flame Transition, Northern Lights, Nature Bloom
- **转场类：** Raven, Splash, Flame, Melt, Smoke, Seamless, Jump, Hole, Roll, Fly Cam, Display Transition

---

## ⑤ 可直接抄进 open-edit 的 prompt 模板（原文照搬）

### 5A. T2V / I2V 骨架

**Text-to-Video：**
```
[Subject + appearance].
[Environment — location, time, weather, atmosphere].
[Action — what happens and how].
[Camera — named control].
[Look — style + color grade].
```
T2V 范例：
```
A lone astronaut stands on the surface of a red desert planet, helmet visor reflecting
twin moons rising on the horizon. Dust spirals slowly in the thin atmosphere.
She turns to face the camera, gloved hand raised in a slow salute.
Camera: slow Crane Up revealing the vast emptiness behind her.
Style: Cinematic, desaturated orange and deep blue, 2.35:1 anamorphic.
```

**Image-to-Video（只描述「动/变」）：**
```
[Reference the input image as the first frame].
[Describe what should move, change, or animate — not what is already visible].
[Camera — named control].
[Style/atmosphere cues].
```
I2V 范例：
```
Starting from the provided image as the first frame.
The woman's hair lifts gently in the wind. She blinks slowly and turns her gaze
slightly to the left, a faint smile forming.
Camera: subtle Dolly In toward her face.
Style: Cinematic, warm afternoon light, shallow depth of field.
```

### 5B. Identity / Motion 分离模板（Soul ID 必用）

```
Identity Block:
The Soul ID character — [face features], [hair], wearing [garments + accessories],
[build]. (NO motion, NO camera, NO temporal language)

Motion Block:
[Action]. Camera: [named preset] — [behavior]. [Environmental motion].
Style: [look], [color grade]. [aspect ratio]. (NO appearance repetition)
```

### 5C. 10 个 Genre Recipe 模板（来自 recipes skill，原文，全部 IP-safe）

**Recipe 1 — Action / Chase**（模式：Establish → Pursuit → Obstacle → Climax；模型 Kling 2.6/Sora 2）
```
[Subject description — clothing, build, energy] sprints through [environment].
Camera: Action Run — low behind them, matching pace.
[Obstacle appears — what is it]. They [dodge action], barely clearing it.
The camera Whip Pans to [pursuer/threat].
Bullet Time as [climax action — punch, leap, collision].
Style: Cinematic, high contrast, [warm/cold] tones. [Aspect ratio].
```

**Recipe 2 — Emotional Drama / Character Moment**（Dolly In, Arc, Head Tracking）
```
[Character — appearance, posture, state] is in [intimate environment].
[What they are doing — quiet action revealing emotion].
Camera: slow Dolly In toward [their face / hands / significant object].
[Something shifts — they react, realize, remember].
Style: [Cinematic / Super 8MM], [lighting]. [Color grade — warm/cool, contrast level].
```

**Recipe 3 — Product Advertisement**（Lazy Susan, Dolly In, Robo Arm）
```
[Product description — no brand name. Color, material, shape, size].
[Setting — surface, environment, lighting setup].
Camera: [Lazy Susan / Robo Arm] revealing [product feature].
[Hero moment — pour, cut, open, glow, activate — macro slow motion].
[Lifestyle context if relevant].
Style: Commercial ad quality, [clean/warm/dramatic] lighting. [Aspect ratio].
Sound: [product-specific audio cue].
```

**Recipe 4 — Sci-Fi / Futuristic**（Crane Up, FPV Drone, Super Dolly Out, Dutch Angle）
```
[Futuristic environment — city, facility, space, wasteland].
[Character — description, what they wear, what they carry].
[The situation — what's happening, what's the threat or goal].
Camera: [movement choice — crane up / FPV / orbit].
[Key visual moment — tech activating, weapon firing, transformation].
Style: [Cinematic / Anamorphic], [cold blue / neon / desaturated orange]. [Ratio].
Apply [motion preset] at [moment in scene].
```

**Recipe 5 — Horror / Supernatural**（模式：False calm → Wrong detail → Escalation → Reveal）
```
[Ordinary setting made unsettling — house, street, hospital].
[Character — alone, unaware].
[Wrong detail appears — something that shouldn't be there].
Camera: slow Dolly In toward [the wrong thing].
[Character notices. Reaction.] Camera: Dutch Angle.
Style: [VHS / Cinematic low key], [sickly tones / crushed blacks].
Apply [Horror Face / Raven Transition] preset at the reveal moment.
```

**Recipe 6 — Romance / Intimate**（Arc, Dolly In, Kiss）
```
[Two characters — brief appearance note each].
[Setting — intimate, warmly lit, specific].
[The moment — what are they doing, what is the tension].
Camera: [Arc / Dolly In / Kiss control].
[The beat — a look, a touch, a word].
Style: [Cinematic / Super 8MM], [warm golden / soft overcast] light. [Ratio].
```

**Recipe 7 — Documentary / Nature**（Crane Down, Timelapse Landscape, Overhead）
```
[Location — specific, vivid, real-feeling].
[Subject — animal, person, phenomenon].
[What is happening — natural behavior, unposed].
Camera: [observational movement — slow pan, timelapse, crane].
[Detail moment — close-up of something specific and visually striking].
Style: Cinematic, natural grade, [time of day], [weather]. [Ratio].
No artificial effects — pure observational documentary feel.
```

**Recipe 8 — Dance / Music Video**（360 Orbit, Dolly In/Out on beat, Overhead）
```
[Dancer/performer — description, outfit].
[Performance space — lighting, scale, atmosphere].
[Dance style / energy — specific movements to describe].
Camera: [movement, ideally synced to beats — orbit, dolly, overhead].
[Climax moment — signature move, camera impact].
Style: [Cinematic / Anamorphic], [color grade]. [Ratio].
Apply [Glow Trace / Live Concert] preset for additional visual energy.
```

**Recipe 9 — Transformation / Before & After**（Dolly In to trigger，尽量单连续镜）
```
[Subject in their before state — normal, restrained, plain].
[Trigger moment — what causes the transformation].
Camera: [movement toward the trigger moment].
[Transformation unfolds — describe the visual change].
[After state — what they become].
Style: [appropriate to transformation type]. [Ratio].
Apply [preset name] preset to execute the transformation effect.
```

### 5D. Seedance 多角色锚定模板（worked example，原文照搬当结构种子）

```text
At 0 seconds, two characters in frame.

Character A — [name] (Soul ID @Image1).
  Screen position: left third, x-position 30%, y-position 55%, frame occupancy 28%.
  Depth layer: midground.
  Body orientation: three-quarter toward [B], screen-right.
  Pose: [...]. Gaze: [...]. Contact points: [...]. State lock: [...].

Character B — [name] (Soul ID @Image2).
  Screen position: right third, x-position 70%, y-position 60%, frame occupancy 24%.
  Depth layer: midground. Body orientation / Pose / Gaze / Contact points / State lock: [...].

Cross-character relationships:
  Distance between A and B: ~3 meters, closing.
  Eyeline: A → B sustained; B → A intermittent.
  Crossing rule: neither crosses the central vertical axis of the frame in this shot.
  Negative space: centered between them, narrowing as A advances.

Camera: medium-two-shot, low angle (chest height), 35mm anamorphic lens, slow dolly-in 0.5m.
Setting: [environment + time + weather + light source + atmospheric particulates].
Aesthetic: [register, key/fill, palette, grain, VFX y/n].
Audio: [continuous ambient + timed SFX + breath + music y/n].
Continuity locks: [what stays fixed across the shot].
Final frame: [end-state description].
```

### 5E. 反 slop 词替换表 + 物理语言（原文，prompt 后处理直接用）

| Slop Word | 换成 |
|-----------|------|
| beautiful / stunning / amazing | 删，描述具体视觉 |
| epic | large-scale, sweeping, towering |
| dynamic | fast-tracking, whip-pan, handheld |
| energetic | sprinting, jumping, arms pumping |
| cinematic camera movement | slow dolly push / crane up / tracking shot |
| cool transition | match-cut / whip pan / smash cut |

物理语言（用可观察后果替代情绪词）：
- "powerful punch" → `fist connects, sweat flies off in slow motion, opponent's head snaps back`
- "dramatic entrance" → `door slams open, dust erupts from the frame, light floods the dark room`
- "fast car" → `tires spin, gravel sprays backward, chassis drops as acceleration kicks in`

无 negative prompt（用正向约束）：
- "no shaky camera" → `locked-off static camera, no movement`
- "no blur" → `sharp focus throughout, deep depth of field`
- "don't make it dark" → `bright, evenly lit, overcast daylight`

### 5F. 三幕动作节奏 + 程度副词

三幕：Charge-up（蓄力）→ Burst（爆发）→ Aftermath（物理后果）。
程度副词：`slowly, dramatically, violently, gently, frantically, deliberately, cautiously, explosively`。

### 5G. Genre 长度 & lead-with 目标（原文表）

| Genre | Lead With | Target Length |
|-------|-----------|---------------|
| Product / E-commerce | Subject | 30–50 words |
| Lifestyle / Social | Action | 40–60 words |
| Drama / Narrative | Scene | 60–100 words |
| Music Video | Style | 50–80 words |
| Landscape / Travel | Scene | 30–60 words |
| Commercial / Brand | Style | 40–70 words |
| Anime / Artistic | Style | 50–90 words |

### 5H. 6-Pass 诊断序列（不知道哪里错时按序排查，原文）

| Pass | 变量 | 问题 |
|------|------|------|
| 1 | Subject | 焦点元素是否描述无歧义？ |
| 2 | Action | 动作是否具体（基于物理）且本镜单一？ |
| 3 | Camera | 相机是否命名（预设或具体动词），非暗示？ |
| 4 | Style | look 是否锚定（palette/grade/lens/lighting），非纯形容词？ |
| 5 | Audio | 若有音频，是否当并行轨用具体声音描述？ |
| 6 | Output | 宽高比/时长/分辨率是否为本镜需求刻意设定？ |
> 多数失败落在 Pass 1–2（早期 token 权重大）。到 Pass 4 还没动结果 → 该结构重写，不是迭代。

---

## ⑥ 那个 GitHub skill 的结构 —— 能不能 fork/借鉴？

**结论：能直接 fork。** MIT 协议（`LICENSE`），v3.15.2（2026-06-22 更新），明确支持 Claude Code / Cowork / claude.ai Projects。安装：
```bash
git clone https://github.com/OSideMedia/higgsfield-ai-prompt-skill ~/.claude/skills/higgsfield
```

### 仓库结构（来自 git tree，全量路径）

**根级文档（最高价值，直接抄）：**
- `SKILL.md` — 主 dispatcher（路由到子技能，含 HARD RULES 预交付清单——DISCIPLINE 的唯一规范家）
- `DISCIPLINE.md` — 9 模式 3-3-3 框架（见 ②）
- `vocab.md`（480 行）— 全平台词汇表（含 Emotion as Visible Behavior 8 通道、Scene-physics lighting、Composition Vocabulary）
- `prompt-examples.md`（634 行）— 高质量范例 + Before/After 对
- `model-guide.md` / `image-models.md` — 模型对比表 + 决策流程图 + 定价层
- `production-benchmarks.md` — Cannes 90 分钟长片基准、接受率校准、可证伪成功标准
- `photodump-presets.md`

**20 个子技能（`skills/`）：**
prompt（MCSLA 核心）、camera（全相机预设）、motion（VFX 预设库）、seedance（+ENGINE-RULES.md +FAILURE-MODES.md）、cinema（CS 2.5/3.0/3.5，2013 行最大）、soul（Soul ID 一致性 +Character Anchor Block）、style、audio、models（+MODELS-DEEP-REFERENCE.md）、recipes、troubleshoot、assist、recall、pipeline、canvas、content-factory、marketing-studio、gpt-image-2、image-shots、mixed-media、moodboard、vibe-motion、workspaces、apps、stack（执行层共存规则）。`skills/shared/negative-constraints.md`=共享 artifact 防治表。

**17 个模板（3 类，`templates/`）：**
- 10 个 genre：01-cinematic-action-chase、02-product-ugc-showcase、03-horror-atmosphere、04-fashion-editorial、05-sci-fi-vfx、06-portrait-character-intro、07-landscape-establishing-shot、08-comedy-social-media、09-romantic-intimate、10-dance-music-performance
- 4 个 seedance 多角色协调：multi-character-anchor、single-character-position、top-down-map、worked-example-two-character
- 3 个 text-overlays：slogan、speech-bubble、subtitle
- （另有 `templates/character-design/` 6 个角色设计表：9-question-character-sheet、character-web、premise、story-spine、style-sheet、world-sheet）

**工具/基础设施（这部分值得借鉴，给 open-edit 加纪律层）：**
- `seedance_lint.py` — Seedance 预检 linter（content-filter 风险、结构违规、分辨率/时长不匹配、ZH 1800 字符上限、ZH antislop）
- `higgsfield_memory.py` — generation ledger（`log-gen` / `ratio` / `budget` / `log-route`），把「迭代次数→接受率→credit 预算」变成可查数据；`compute_ratio` / `fork_verdict` 自动判 iterate vs batch
- `db/ledger/` — append-only 生成账本，结构性 vs 随机性拒绝分类
- `specs/` — model-specs.yaml/json + image-model-specs（aspect_ratio 枚举、duration range、media roles），`refresh_specs.py` 周检 spec drift
- `validate.py` / `evals/`（cinema/models/prompt/seedance 用例）/ `tests/` — 防 spec 漂移的 CI

### 给 open-edit 的借鉴优先级（我的判断）

1. **直接抄文本资产：** MCSLA、DISCIPLINE、camera/motion 预设库、negative-constraints、10 genre + seedance 模板、anti-slop 表、6-Pass 诊断 —— 这些是纯 prompt 知识，无依赖，照搬即可。
2. **移植纪律工具：** `seedance_lint.py` 的预检思路 + `higgsfield_memory.py` 的 ledger（log-gen/ratio/budget）—— 这是把「1% 接受率下不烧死项目」工程化的核心，open-edit 应该有等价物。
3. **架构借鉴：** 「prompt 构造层 ⟂ 执行层」的硬分离 + 三执行路径（CLI/MCP/skills）+ specs 自动刷新 + ledger 驱动的 iterate/batch fork。
4. **注意：** 该 skill 只产 prompt 不做生成，执行靠 Higgsfield 官方 CLI/MCP（`github.com/higgsfield-ai/cli`、`github.com/higgsfield-ai/skills`）。open-edit 复刻时这层要换成自家生成核心（Soul=LoRA / 本地合成），但 prompt 层和纪律层可几乎照搬。

---

### 附：信息缺口
- 原 Scribehow 两个 image-to-video / beginner 步骤页已失效（HTTP 410/404），已用官方等价新手指南补齐（见 ①C）。
- Kolbo 页只点名 ~15 个预设（其余藏在「90+ more」），已用官方 camera-controls 页的 66 个全名单替代（见 ④A）。
- `vocab.md`、`cinema/SKILL.md`(2013行)、`prompt-examples.md` 体量大未全展开，需要时按文件名直接 fork 仓库取原文。
