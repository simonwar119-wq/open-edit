---
name: grading-standard
for_technique: color-grading-policy
ffmpeg_version_tested: "8.1.2"
platform_tested: macOS
complexity: medium
last_updated: 2026-06-27
---

# 调色标准 —— 何时调色、何时保原色（Grading Standard）

## 问题（为什么需要这个标准）

风格库的 CDL + 创意 LUT 是为**原始/未调色素材**设计的。如果对一段**已经调好色的成片素材**再套一遍创意 LUT，会二次调色 → 色彩冲突 → 画面诡异。
实测：qmike 印度样片本身是暖色电影感成片，套上 fincher 的 bleach-bypass LUT 后变得灰暗、肤色发青、失真。

> 核心原则：**调色是为了"统一画面 + 补足平素材"，不是无脑给每一帧盖一层 LUT。**

## 标准（按 clip 分级，写进 EDL 的 `clip.grade.mode`）

| 来源 | 判定 | grade.mode | 处理 |
|---|---|---|---|
| **生成镜头**（fal/Seedance 等） | 永远是原始输出 | `style` | 套风格完整 CDL + 创意 LUT |
| **上传素材**（默认） | 任何成片/带色素材 | `preserve` | **只归一化尺寸/帧率，不动颜色** |
| **上传素材 · 近纯灰 Log** | 饱和度 < 0.05（几乎确定是 raw/log） | `style` | 套风格 CDL + LUT |

> **关键修正（2026-06-27）**：早期用「饱和度 < 0.12」判定"平片"，但**成片也可能刻意低饱和**（qmike样片2 饱和度 0.11，是成片却被误判重调色 → 又变诡异）。
> 饱和度单一指标不可靠 → **默认一律 preserve 上传素材**；只有近纯灰(< 0.05)的真 log 才破例。
> 真有一批 raw/log 素材想统一调色 → 显式 `grade_scope="all"`。

## 开关（`grade_scope`，job 级，默认 `auto`）

| grade_scope | 行为 | 用途 |
|---|---|---|
| `auto`（默认） | 按上表逐 clip 判定 | 通用：保护好素材、调平素材、调生成镜头 |
| `all` | 所有 clip 都套 `style` | 用户明确要"全片统一重调色"（素材都是平片时） |
| `none` | 所有 clip 都 `preserve` | 只组接不调色 |

## 执行（render.py）

`color_chain(color, fps, W, H, mode)`：
- `mode="preserve"` → 只 `fps,scale,crop,setsar,format`，**无 CDL、无 LUT**。
- `mode="style"` → `colorchannelmixer(slope) + eq(power/offset/saturation) + lut3d(创意LUT@intensity)`。

```bash
# preserve（保原色，仅归一化）
ffmpeg -i in.mp4 -vf "fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,format=yuv420p" out.mp4

# style（套风格）—— 见 cdl-lut-grade.md
ffmpeg -i in.mp4 -vf "<base>,colorchannelmixer=...,eq=...,lut3d=file=look.cube:interp=tetrahedral" out.mp4
```

## 已验证（2026-06-27）

qmike 印度样片重渲：上传镜头 `grade=preserve`（画面与原片一致，肤色/暖调保留），生成镜头 `grade=style`。修复"调完变诡异"。

## 待办（v2 — 连贯性 match-grade）

当前 preserve 的上传镜头与 style 的生成镜头并置，色调可能不完全统一。下一步：从上传素材测出平均色调（亮度/饱和/白平衡），给生成镜头推导一份**匹配上传**的轻 CDL（mode `match`），让生成镜头"长得像"用户的真实素材，而不是反过来把素材改成生成镜头的样子。
