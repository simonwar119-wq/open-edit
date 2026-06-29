---
name: qmike-cinematic-travel
description: |-
  Warm cinematic travel content style — golden-hour color grading, soft film grain, 
  layered composition with natural light. Purpose-built for vertical social media 
  (Instagram Reels, TikTok, YouTube Shorts). Combines establishing architecture 
  shots, candid street documentary, and intimate lifestyle portraiture.
category: style
subcategory: custom-analysis
source:
  creator: Qmike (Instagram @qmike)
  reference_works:
    - "THE COLORS OF INDIA (Agra, Jaipur, Jodhpur, Udaipur travel series)"
    - "Lifestyle/fashion personal content (wardrobe, morning routine)"
  analysis_method: vision-api
triggers:
  - "warm travel"
  - "cinematic lifestyle"
  - "golden hour documentary"
  - "vertical travel content"
  - "India travel edit"
layer4_ready: true
last_updated: 2026-05-13
---

# Qmike Cinematic Travel Style Guide

## Layer 1: 描述层（Description）

**整体视觉氛围：**
暖色基调的旅行/生活方式视听风格，以金色阳光、暖大地色调、柔和的褪色电影质感为核心特征。画面介于精心构图的旅行摄影和生活纪录片之间——既有对地标建筑和城市风貌的精心构图展示，也有人物在日常环境中的自然、不做作的抓拍。节奏不急不缓，让观众既能感受目的地氛围，又能与创作者建立亲密感。

**标志性特征：**
- 暖调褪色色彩分级（金色阳光+轻微褪色饱和度）
- 柔和的胶片颗粒感（模拟复古电影质感）
- 前景物遮挡构图（创造窥视感和景深层次）
- 黄金时刻/暖色室内光线作为主光源
- 垂直9:16画幅（社交媒体原生）
- 静态镜头vs轻微手摇交替

**适用题材：**
旅行Vlog、目的地推广、生活方式内容、个人品牌建立、服装/穿搭展示

**代表性参考作品：**
- THE COLORS OF INDIA（斋浦尔/焦特布尔/阿格拉系列）
- 个人衣橱穿搭/日常生活短视频

---

## Layer 2: 参数层（Parameters）

| 参数类别 | 字段 | 值 | 说明 |
|---------|------|-----|------|
| **色彩** | `color.temperature_k` | 5200-6200 | 暖色调，偏向黄金时刻色温 |
| | `color.palette` | `warm` | 暖色主调 |
| | `color.saturation_offset` | -15 to -25 | 轻微褪色，降低饱和度 |
| | `color.contrast_offset` | -10 to -20 | 降低对比度，柔和高光 |
| | `color.dominant_hex` | `["#F4A460", "#D2691E", "#FFF8DC", "#87CEEB"]` | 暖橙/沙色/米白/淡蓝 |
| **镜头时长** | `duration.avg_s` | 2.5-4.0 | 中等偏慢的剪辑节奏 |
| | `duration.min_s` | 1.0 | 最短视频片段（过渡性镜头） |
| | `duration.max_s` | 6.0 | 最长单镜头（建立镜头） |
| **运镜** | `movement` | `static`（≈70%）, `handheld`（≈20%）, `truck`（≈5%）, `dolly-forward`（≈5%） | 以静态镜头为主，辅以轻微手持和缓慢推轨 |
| | `movement_intensity` | `slow` | 所有移动均为慢速、平稳 |
| **构图** | `composition` | `[rule-of-thirds, negative-space, deep-space, frame-in-frame]` | 三分法为主，前景遮挡制造深度 |
| **景别分布** | `scale` | LS（25%）、MS（30%）、MCU（20%）、CU（15%）、ECU（10%） | 建筑=远景/全景，人物=中景/中特写，细节=特写/大特写 |
| **拍摄角度** | `angle` | `eye-level`（60%）、`high-angle`（25%）、`low-angle`（15%） | 平视为主，俯拍用于街拍和物品，仰拍用于建筑 |
| **景深** | `dof.style` | `shallow`（70%）、`deep`（30%） | 人像/细节用浅景深，建筑用深景深 |
| | `dof.aperture_equiv` | `f/1.4-f/2.8`（人像），`f/8-f/11`（建筑） | |
| **画幅** | `aspect_ratio` | `9:16` | 垂直社交媒体格式 |
| **转场分布** | `transition.hard_cut_pct` | 85 | 硬切为主 |
| | `transition.cross_dissolve_pct` | 15 | 叠化用于节奏过渡和结尾 |
| **灯光风格** | `lighting.style` | `naturalistic` | 自然光为主 |
| | `lighting.source` | `natural` | 太阳光/窗户自然光 |
| | `lighting.direction` | `side`（60%）、`back`（25%）、`front`（15%） | 侧光为主，强调立体感 |
| | `lighting.quality` | `soft` / `diffused` | 柔光/漫射光 |
| **焦距** | `lens` | `normal`（24-70mm等效）, `telephoto`（70-200mm等效用于街拍） | 标准焦段为主 |
| **音频** | `audio.music_drive` | `moderate` | 音乐衬托氛围，不主导剪辑节奏 |
| | `audio.sync_type` | `free` | 非精确对齐节拍点 |
| | `audio.sound_design` | `ambient` | 保留环境音增强真实感 |

---

## Layer 3: 执行层（Execution）

### 3.1 基础调色命令（暖色褪色质感）

```bash
# 暖色调 + 轻微褪色 + 柔和对比
ffmpeg -i input.mp4 \
  -vf "eq=contrast=0.85:saturation=0.75:brightness=0.05:gamma=1.1,\
       colortemperature=temperature=5800,\
       vignette=PI/4:max_eval=frame" \
  # contrast: -15% | saturation: -25% | gamma: +10% | warm shift to 5800K
  # vignette: 暗角效果增强电影感
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  output.mp4
```

### 3.2 胶片颗粒模拟

```bash
# 添加柔和胶片颗粒
ffmpeg -i input.mp4 \
  -vf "noise=alls=8:allf=t+u,\
       eq=saturation=0.85:contrast=0.9" \
  # noise: 8% 随机噪点 | allf=t+u: 时间+均匀分布（更像真实胶片）
  output.mp4
```

### 3.3 前景遮挡模糊效果（标志性手法）

```bash
# 模拟前景物体虚化，增强景深感
ffmpeg -i input.mp4 \
  -vf "gblur=sigma=8:enable='between(t,0,0.5)',\
       eq=contrast=0.85:saturation=0.8" \
  # 在片段前0.5秒添加高斯模糊
  # 实际拍摄中可通过近距离前景物体自然实现
  output.mp4
```

### 3.4 基本转场

```bash
# 叠化转场（用于地点转换）
ffmpeg -i clip1.mp4 -i clip2.mp4 \
  -filter_complex "xfade=transition=fade:duration=0.5:offset=3.5" \
  # duration: 0.5s | offset: 在clip1的3.5秒处开始过渡
  output.mp4
```

### 3.5 文字叠加（地点标签）

```bash
# 左下角地点标签（Qmike常用手法）
ffmpeg -i input.mp4 \
  -vf "drawtext=text='JAIPUR, INDIA':fontfile=/System/Library/Fonts/Helvetica.ttc:\
       fontsize=18:fontcolor=white:borderw=1:bordercolor=black@0.5:\
       x=20:y=h-th-40:enable='between(t,0,3)'" \
  output.mp4
```

---

## Layer 4: 反向分镜层（Shot Blueprint — 模式B专用）

> 适用于创建"暖色调旅行/生活方式"风格的视频。
> `layer4_reproducible: full` — 普通创作者可用自然光+基础设备复现。

### 4.1 镜头类型清单

| 镜头类型 | 景别 | 角度 | 运动 | 参考时长 | 数量建议 | 内容要求 | 拍摄要点 | 失败信号 |
|---------|------|------|------|---------|---------|---------|---------|---------|
| **NE1: 地标建立镜头** | LS / ELS | low-angle / eye-level | static | 3-5s | 2-3个 | 目的地标志性建筑/景观全景 | 必须在黄金时刻（日出后1h或日落前1h）拍摄；侧光让建筑纹理立体；天空保留1/3以上负空间 | 正午顶光照=失败；画面边缘有行人/杂物闯入=失败 |
| **NE2: 人物场景融合** | MS / MFS | eye-level | static | 3-4s | 2-4个 | 创作者在场景中的自然状态（倚栏、漫步、凝视） | 人物占frame 1/3，场景占2/3；侧逆光勾勒轮廓；前景留遮挡物制造景深层次 | 人物背光无轮廓=失败；画面单调无层次=失败 |
| **NE3: 街拍纪实** | CU / MS | high-angle | handheld slow | 2-3s | 2-3个 | 当地人的自然状态、街头细节、市井气息 | 从高处俯拍，利用前景遮挡（栏杆/植物边缘）；保持不打扰；等待"决定性瞬间" | 被拍摄者发现镜头=失败；画面抖动明显=失败 |
| **NE4: 细节特写** | ECU / CU | eye-level / high-angle | static | 1.5-2.5s | 2-3个 | 食物、纹理、建筑细节、衣物面料 | 浅景深f/1.4-2.8；柔和自然光为主光源；构图简洁，突出质感 | 背景杂乱不可辨=观察环境没选好；过曝丢失细节=失败 |
| **NE5: 个人肖像** | MCU / CU | eye-level | static | 2-4s | 1-2个 | 创作者的面部/半身，有情绪表达 | 侧光或窗光；背景干净不过曝；眼神看向远方而非镜头（自然感）；微微仰角显自信 | 眼神直接对镜头=出戏；平光无立体感=失败 |
| **NE6: 过渡空镜** | ECU / CU | varied | static / handheld | 1-2s | 3-5个 | 天空、树叶、水面倒影、光影变化 | 拍满5-10条备选，后期在缺少转场素材时插入 | 画面过暗或过曝=不可用 |

### 4.2 叙事结构模板

```
开场（Hook）：NE1（地标建立），1-2个镜头，占总时长15%
  → 快速建立目的地印象，用标题文字点明地点
主体（Body）：NE2 + NE3 + NE4 + NE5交替，占总时长65%
  → 人物场景融合 → 街拍纪实 → 细节特写 → 个人肖像
  → 节奏：慢→中→慢，中间插入1-2个节奏变化
高潮（Climax）：NE2 + NE5，占总时长10%
  → 最佳光线下的最佳场景+人物最佳状态镜头
收尾（Close）：NE1（不同角度）或NE6，占总时长10%
  → 从近景拉远或空镜头淡出，留余韵
```

### 4.3 最小可用素材集（MVP Shot List）

```
最少可用：6个镜头
1. NE1: 地标建立镜头（广角，黄金时刻侧光）
2. NE2: 人物在场景中眺望（中景，侧逆光）
3. NE4: 一个当地细节特写（食物/纹理/建筑细节）
4. NE5: 创作者半身肖像（柔和窗光或侧光）
5. NE3: 街拍纪实（俯拍，自然状态）
6. NE6: 过渡空镜（树叶/天空/光影）
```

### 4.4 风格守卫（Style Guards）

```
✅ 合格信号：
  - 暖色褪色调色（色温5200-6200K，饱和度-15%至-25%）
  - 自然光为主，无明显人工光源
  - 静态或极慢稳定的运镜
  - 前景遮挡制造景深层次
  - 人物与场景比例约1:2

❌ 失败信号：
  - 冷色调或蓝色调过重
  - 对比度过高，高光溢出或阴影死黑
  - 手持抖动明显（超过轻微自然晃动）
  - 人物正对镜头，像游客自拍
  - 正午顶光拍摄，人物脸上有刺眼阴影
  - 水平线不水平（无艺术意图的歪斜）
  - 画面中闯入无关人物/现代元素（电线杆/汽车/广告牌）
```
