# Open Edit · 复刻 Higgsfield 两大功能 · Provider 扩展设计

> 目标:用 fal(按量付费)+ OpenRouter(文字大脑)+ 官方 Seedance(便宜空镜)替代 Higgsfield 会员,在本地工程复刻两个功能。
> 落点:全部改在 `engine/providers/`,是对现有多 provider 架构的**扩展**,不是重写。
> 前置:先完成上一轮的 P0 解耦(导演大脑搬进 engine,oe 不再依赖 backend)。

---

## 0. 分工(谁管什么)

| 层 | 工具 | 负责 |
|---|---|---|
| 文字大脑 | **OpenRouter** | AI 导演决策、反向分镜、prompt 改写。视频生成**不在**它范围 |
| 视频生成 | **fal** | 一个 key、一套代码,换模型=换端点字符串,纯按量,无订阅 |
| 便宜空镜 | **官方 Seedance** | 不涉人脸的镜头(食材/煎制/环境/产品),省钱 |

face/no_face 分流规则继续生效:涉真人脸的镜头走 fal 海外链路,空镜走国内 Seedance。

---

## 目标 1:角色 + 场景 + 提示词 → 电影感视频

### 1.1 用什么模型

**Kling 3.0**(fal 端点 `fal-ai/kling-video/v3/...`)。关键能力:
- **element referencing**:一张参考图锁住角色外形,跨每个镜头保持 on-model(这是"角色一致"的核心)
- **multi-character coreference**:3+ 角色同场景不串脸
- **多镜头 storyboard**:每镜独立 prompt → 正好对接你的 EDL
- 摄影机运动(dolly zoom / tracking / rack focus)+ 布料/头发/液体物理 → "像拍的不像生成的"
- 价格参考:标准档 ≈ $0.084/s,Pro ≈ $0.112/s(不含音频)

### 1.2 工程改动(小)

你现有 `kling-hq`(FLUX 出参考帧 → Kling i2v)逻辑保留,新增一个档:

```python
# engine/providers/fal.py — FAL_MODELS 增加
"kling-3-cinematic": {
    "kind": "t2v_ref",                         # 带角色参考图的文生视频
    "endpoint": "fal-ai/kling-video/v3/pro/text-to-video",  # 接入时核对最新端点
    "usd_per_s": 0.112,
    "commercial_ok": True,
    "supports_element_ref": True,              # 可传角色参考图锁脸
},
```

payload 关键字段(接入时按 fal 当时文档核对):
```python
{
  "prompt": "<本镜 prompt>",
  "duration": "5",                             # 3–15s
  "elements": [                                # 角色一致的核心
    {"frontal_image_url": "<角色正脸图>",
     "reference_image_urls": ["<侧面>", "<其他角度>"]}
  ],
  "aspect_ratio": "9:16",
}
```

### 1.3 链路(不改 oe 主流程)

```
prompt → [OpenRouter 导演] 选风格 + 反向排镜 → EDL(每镜带角色 slug)
       → 每镜调 kling-3-cinematic,带该角色的 element 参考图
       → render.py 风格化调色 + 组接(你现成)
       → 成片
```

角色参考图来源:`engine/characters/<slug>.json` 里存正脸 + 多角度图 URL(你 baba/yuer 已有骨架,补上参考图字段即可)。

---

## 目标 2:口播视频 + 提示词 → 自动换场景 / 换脸 / 换道具

这是 **video-to-video**,工程现在没有,要在 providers 新增一个能力类型。分两条链。

### 2A. 换场景 / 换道具(保留口播原音)→ Kling O1 Edit

**端点** `fal-ai/kling-video/o1/video-to-video/edit`,$0.168/s。特点:
- 自然语言编辑,**不需要 masking**
- 保留原始运动结构、镜头角度、空间关系
- 最多 4 个组合参考元素/图片 → 复杂的角色/环境替换
- **`keep_audio` 参数保留口播原音**(你的口型/节奏/音轨全保住)— 这条对口播是命门

```python
# engine/providers/fal.py — 新增能力类型
"kling-o1-edit": {
    "kind": "v2v_edit",                        # 视频→视频,自然语言编辑
    "endpoint": "fal-ai/kling-video/o1/video-to-video/edit",
    "usd_per_s": 0.168,
    "commercial_ok": True,
    "keep_audio_default": True,
},
```
payload:
```python
{
  "video_url": "<口播视频>",
  "prompt": "把背景换成<新场景>,桌上加<新道具>,保持人物动作与镜头不变",
  "elements": [...],          # 可选,最多 4 个参考
  "keep_audio": True,         # 保留口播原音
}
```

### 2B. 换脸 / 换人 → Kling Motion Control(Move / Replace)+ 首帧编辑

更彻底的换人,用两个专用模式:
- **Move**:把视频里人物动作迁到新场景(同时换角色 + 背景)
- **Replace**:只换视频里的角色,场景不变

**推荐工作流**(这是社区验证最稳的换脸链路):
```
1. 口播参考视频(单人、上半身/全身清晰,≤30s)
2. 提取首帧 → 用 Nano Banana Pro / Flux 改掉角色和背景(人物位置不变)
3. 参考视频 + 改好的首帧 → Kling Motion Control
4. 换声音(可选):你的口播本就是中文真人音,通常不用换;
   要换音色用豆包 TTS / 你太太唱歌那套替代 ElevenLabs voice changer
```

```python
# engine/providers/fal.py
"kling-motion-move": {
    "kind": "v2v_motion", "mode": "move",
    "endpoint": "fal-ai/kling-video/.../motion-control",   # 接入核对
    "usd_per_s": 0.168, "commercial_ok": True,
},
"kling-motion-replace": {
    "kind": "v2v_motion", "mode": "replace",
    "endpoint": "fal-ai/kling-video/.../motion-control",
    "usd_per_s": 0.168, "commercial_ok": True,
},
```

首帧编辑要新增一个图像编辑端点(Nano Banana Pro / Flux),作为 motion control 的前置步骤。

---

## 3. providers 架构改动总览

`engine/providers/base.py` 现在的 `GenSpec` 是为 t2v/i2v 设计的,要扩出 v2v 字段:

```python
@dataclass
class GenSpec:
    kind: str                 # t2v | i2v | t2v_ref | v2v_edit | v2v_motion
    prompt: str = ""
    image_url: str | None = None
    video_url: str | None = None        # 新增:v2v 源视频
    elements: list | None = None        # 新增:角色/参考元素(最多 4)
    keep_audio: bool = True             # 新增:v2v 保留原音
    duration: float = 5.0
```

`fal.py` 的 dispatch 按 `kind` 分支,新增三个分支:`t2v_ref`(目标1)、`v2v_edit`(目标2A)、`v2v_motion`(目标2B)。每个分支:submit → 轮询 queue → 取结果 URL → 下载(沿用现有 Seedance 轮询范式,只用标准库 urllib,不引依赖)。

---

## 4. 暴露给 Claude Code(MCP 工具新增)

`mcp_server.py` 在现有工具外补三个:

```python
@mcp.tool()
def oe_cinematic(prompt, character, scene, duration=5.0, provider="mock"):
    """目标1:角色+场景+提示词 → 电影感视频(Kling 3.0,角色一致)。"""

@mcp.tool()
def oe_restyle(video, prompt, keep_audio=True, provider="mock"):
    """目标2A:口播视频+提示词 → 换场景/换道具,保留原音(Kling O1 Edit)。"""

@mcp.tool()
def oe_reface(video, new_character, mode="replace", provider="mock"):
    """目标2B:口播视频 → 换脸/换人(Kling Motion Control,move=连背景一起换)。"""
```

provider=mock 时全程零成本占位;provider=fal 才花真钱。

---

## 5. 成本速查(按量,vs Higgsfield 月费)

| 功能 | 模型 | 单价 | 一条 8s 成片估算 |
|---|---|---|---|
| 目标1 电影感 | Kling 3.0 标准/Pro | $0.084–0.112/s | ≈ $0.67–0.90 |
| 目标2A 换场景 | Kling O1 Edit | $0.168/s | ≈ $1.34 |
| 目标2B 换脸 | Kling Motion Control | ≈ $0.168/s | ≈ $1.34 |
| 空镜(不涉脸) | 官方 Seedance fast | 便宜很多 | 走国内 API |

你只为实际生成的秒数付费——Higgsfield 月费贵在替你包了 UI/工作流,这层你用自己的 MCP 工具替掉。

---

## 6. 实现顺序(建议)

1. **先扩 base.py 的 GenSpec**(加 video_url / elements / keep_audio),这是所有新功能的地基。
2. **目标1 先做**(改动最小,复用现有 i2v 链),跑通"角色一致电影感",验证 element ref。
3. **目标2A**(Kling O1 Edit,单端点、最直接)。
4. **目标2B**(motion control + 首帧编辑链,最复杂,最后做)。
5. 每个端点接入时,**用 mock 跑通链路 → 接 FAL_KEY 真生成 QA 一次 → 核对当时 fal 文档的 payload schema**(端点字符串会变,代码里都标了"接入核对")。

---

## 7. 注意

- **端点字符串以接入当天 fal 文档为准**,本文标的端点是结构示意,fal 模型迭代快。
- v2v 的 `keep_audio` 对口播是命门,默认开。
- 换脸链路涉真人:你和太太是真实本人,走正规授权;不要拿这套去换他人/名人脸,合规与账号风险。
- OpenRouter 只管文字,别指望它生成视频。
