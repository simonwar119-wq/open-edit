---
name: life-of-riza-warm-daily
description: |-
  Warm slow-paced lifestyle vlog with cinematic daily-life visuals — soft low-contrast 
  color grading, natural light, filmic warmth with orange/yellow/beige palette, ASMR 
  environmental sound design with lo-fi background music, minimal dialogue. Purpose-built 
  for vertical social media (Instagram Reels, TikTok, YouTube Shorts). Combines first-person 
  POV (driving, walking, cooking) and third-person observed perspective for immersive 
  everyday storytelling.
category: style
subcategory: custom-analysis
source:
  creator: Life of Riza
  reference_works:
    - "https://www.youtube.com/shorts/rby9meEHt9I"
    - Typical warm daily vlog series (cooking, commute, daily routines)
  analysis_method: vision-screenshot + researcher-report
triggers:
  - "warm daily vlog"
  - "cozy lifestyle"
  - "cinematic daily life"
  - "ASMR cooking"
  - "slow living aesthetic"
  - "film look lofi"
layer4_ready: true
last_updated: 2026-05-14
---

# Life of Riza Style Guide — 温暖慢节奏生活vlog

## Layer 1: 描述层（Description）

**整体视觉氛围：**
温暖的慢节奏生活 vlog / 电影感日常风格。以自然光为主光源、低对比度柔光调色、浅景深、胶片感暖调（橙/黄/米色系）为核心视觉特征。画面兼具沉浸感和亲密感——第一人称 POV 视角让观众获得"在场"体验（开车、走路、做饭），第三人称被拍视角则赋予日常动作一种被他者凝视的电影质感。剪辑节奏舒缓，每镜头 2-5 秒，不赶不拖，像在呼吸。

**标志性特征：**
- 暖调柔光调色（低饱和度、高宽容度，胶片感褪色质感）
- 自然光主导——窗户光、晨光、黄昏光
- 浅景深（f/1.8-f/2.8等效），强调细节和质感
- 第一人称 POV（开车/走路/做饭）与第三人称被拍交替
- 极少对白，声音设计以 ASMR 环境音（雨声/风声/烹饪声）+ Lo-fi 背景音乐为主
- 固定镜头与手持慢移交替，无剧烈运镜
- 画面干净，构图简洁，善用负空间和自然框架

**情感基调：**
治愈、沉浸、生活感——让观众感到"很舒服、不想跳走"。

**适用题材：**
日常生活 vlog、烹饪/美食制作、晨间/晚间日常、独居生活、城市漫步、咖啡/阅读时光

**代表性参考作品：**
- Life of Riza YouTube Shorts（代表性视频：https://www.youtube.com/shorts/rby9meEHt9I）
- 类似创作者：nobody（韩国日常 vlogger）、celine choi、mins_coffee

---

## Layer 2: 参数层（Parameters）

| 参数类别 | 字段 | 值 | 说明 |
|---------|------|-----|------|
| **色彩** | `color.temperature_k` | 4800-6200 | 暖色调，偏向暖白/金黄 | 
| | `color.palette` | `warm` | 暖色主调 |
| | `color.saturation_offset` | -20 to -30 | 低饱和度，褪色感 |
| | `color.contrast_offset` | -15 to -25 | 低对比度，柔和过渡 |
| | `color.dominant_hex` | `["#F5E6CA", "#E8D5B7", "#C4956A", "#8B7355", "#4A4A4A"]` | 米白/暖杏/卡其/暖棕/柔灰 |
| **镜头时长** | `duration.avg_s` | 3.0-4.0 | 舒缓节奏，平均每镜头 3-4 秒 |
| | `duration.min_s` | 1.5 | 最短镜头（细节切入/过渡） |
| | `duration.max_s` | 5.0 | 最长单镜头（建立/沉浸镜头） |
| | `duration.asl` | 3.5 | Average Shot Length 指标 |
| **运镜** | `movement` | `static`（≈50%）, `handheld`（≈30%）, `steadicam`（≈15%）, `pan-right/pan-left`（≈5%） | 固定与手持慢移各半，无剧烈运镜 |
| | `movement_intensity` | `slow` | 所有移动均为慢速、平稳 |
| **构图** | `composition` | `[center-framing, negative-space, rule-of-thirds, frame-in-frame, leading-lines]` | 中心构图为主（POV），三分法为辅，白色墙面/桌面做负空间 |
| **景别分布** | `scale` | CU（30%）、MCU（25%）、MS（20%）、ECU（15%）、LS（10%） | 特写/中特写占主导，强调手部动作和面部情绪；远景用于环境交代 |
| **拍摄角度** | `angle` | `eye-level`（50%）、`pov`（30%）、`high-angle`（15%）、`low-angle`（5%） | 平视 + POV 为主体；俯拍用于食物/桌面动作 |
| **景深** | `dof.style` | `shallow`（80%）、`deep`（20%） | 浅景深为主，突出主体；环境景用深景深 |
| | `dof.aperture_equiv` | `f/1.8-f/2.8`（特写/人像），`f/4-f/5.6`（环境景） | |
| **画幅** | `aspect_ratio` | `9:16` | 垂直社交媒体格式 |
| **转场分布** | `transition.hard_cut_pct` | 90 | 硬切为主，干脆不拖沓 |
| | `transition.cross_dissolve_pct` | 8 | 叠化用于时间过渡（如从天亮到天黑） |
| | `transition.dip-to-color_pct` | 2 | 偶尔黑场淡入淡出用于章节分隔 |
| **灯光风格** | `lighting.style` | `naturalistic` | 自然主义灯光 |
| | `lighting.source` | `natural`（90%）, `practical`（10%） | 自然光为主，偶尔使用场景内台灯/屏幕光 |
| | `lighting.direction` | `side`（50%）、`back`（30%）、`front`（20%） | 侧光/侧逆光为主，营造柔和轮廓 |
| | `lighting.quality` | `soft` / `diffused` | 柔光/漫射光，无硬阴影 |
| | `lighting.color_temperature` | `warm` | 暖色温 |
| **焦距** | `lens` | `normal`（35-50mm等效），`telephoto`（85mm等效用于特写） | 标准焦段接近人眼视角，长焦用于细节压缩 |
| **剪辑手法** | `technique_type` | `straight-cut`（90%）, `j-cut`（5%）, `l-cut`（5%） | 直切为主，偶尔 J/L 剪做声音先入/延续 |
| **节奏模式** | `rhythm` | `decelerando` | 整体节奏渐慢，从日常活动到沉静结尾 |
| **叙事结构** | `narrative` | `chronological` | 线性叙事，按时间顺序展示日常片段 |
| **音频** | `audio.music_drive` | `weak` | Lo-fi音乐作为背景氛围，不主导节奏 |
| | `audio.sync_type` | `free` | 非精确对齐节拍 |
| | `audio.sound_design` | `ambient` | ASMR级环境音（烹饪声/雨声/风声/脚步声）为主，音乐为辅 |
| | `audio.bpm_range` | [70, 95] | Lo-fi / chill hop BPM区间 |

---

## Layer 3: 执行层（Execution）

### 3.1 基础调色命令（暖调柔光褪色质感）

```bash
# 暖调褪色 + 低对比 + 柔和高光
ffmpeg -i input.mp4 \
  -vf "eq=contrast=0.80:saturation=0.70:brightness=0.03:gamma=1.15,\
       colortemperature=temperature=5500,\
       vignette=PI/5:max_eval=frame" \
  # contrast: -20% | saturation: -30% | gamma: +15% | warm shift to 5500K
  # vignette: 轻微暗角增强电影感，不过度
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  output.mp4
```

### 3.2 胶片颗粒与柔光效果（Life of Riza 标志性质感）

```bash
# 柔和胶片颗粒 + 轻微泛光感
ffmpeg -i input.mp4 \
  -vf "noise=alls=6:allf=t+u,\
       eq=saturation=0.75:contrast=0.85,\
       gblur=sigma=0.5:enable='between(t,0,0.3)'" \
  # noise: 6% 随机噪点（比Qmike更轻）| 开头0.3秒微小柔焦
  # 模拟复古胶片 + 梦幻感的轻微泛光
  output.mp4
```

### 3.3 模拟浅景深（对非浅景深素材）

```bash
# 模拟浅景深效果（针对手机或小传感器素材）
ffmpeg -i input.mp4 \
  -vf "libvmaf=model_path=/dev/null:log_fmt=json:log_path=/dev/null,\
       gblur=sigma=4:enable='between(t,0,2)',\
       eq=contrast=0.85:saturation=0.75" \
  # 边缘模糊模拟浅景深（实际拍摄用大光圈更佳）
  output.mp4
```

### 3.4 转场处理

```bash
# 硬切为主（默认不做任何过渡）
# 叠化转场（用于时间跳跃，如白天→夜晚）
ffmpeg -i clip1.mp4 -i clip2.mp4 \
  -filter_complex "xfade=transition=fade:duration=0.6:offset=4.0" \
  # duration: 0.6s 慢叠化 | offset: 在clip1的4秒处开始过渡
  output.mp4
```

### 3.5 Lo-fi 音频处理示例

```bash
# 背景乐 + ASMR环境音混音（假设已有环境音轨 lo-fi_{BGM}.wav）
# 示例：用 ffmpeg 混合 bgm 和环境音，降低 bgm 音量
ffmpeg -i input.mp4 -i lofi_bgm.mp3 \
  -filter_complex "[0:a]volume=1.0[ambient];[1:a]volume=0.3[bgm];\
                   [ambient][bgm]amix=inputs=2:duration=first" \
  # 环境音保持、背景乐降到30%
  -c:v copy output.mp4
```

---

## Layer 4: 反向分镜层（Shot Blueprint — 模式B专用）

> 适用于创建"温暖慢节奏生活vlog"风格的视频。
> `layer4_reproducible: full` — 普通创作者可用自然光+手机/入门相机复现。

### 4.1 镜头类型清单

| 镜头类型 | 景别 | 角度 | 运动 | 强度 | 参考时长 | 数量建议 | 构图 | 景深 | 内容要求 | 拍摄要点 | 失败信号 |
|---------|------|------|------|------|---------|---------|------|------|---------|---------|---------|
| **POV establish** （第一人称到达场景） | LS / MS | pov | handheld | slow | 3-5s | 1-2个 | center-framing, negative-space | deep (f/5.6) | 模拟眼睛看到的进入场景过程——推开门、走入房间、拿起杯子 | 相机固定在胸前或手持与眼同高；走路速度放慢；画面居中；保持呼吸节奏稳定 | 抖动剧烈=不合格；镜头太低不似人眼高度=出戏；画面过曝/欠曝=重拍 |
| **Environmental wide** （环境大景，交代氛围） | LS / ELS | eye-level / high-angle | static | — | 3-4s | 2-3个 | rule-of-thirds, leading-lines | deep (f/5.6-f/8) | 空景展示所在环境的整体氛围——房间一角、窗外街景、厨房全貌 | 利用自然框架（窗框/门框）；注意光线方向，让环境有层次；人可入画但极小或背影 | 画面杂乱无视觉焦点=失败；正午顶光导致高反差=失败；含碍眼现代元素（电线/广告）=避免 |
| **Hand detail** （手部特写，做事的细节） | CU / ECU | eye-level / high-angle | static / handheld | slow | 2-4s | 3-5个 | center-framing, negative-space | shallow (f/1.8-f/2.8) | 手在做事的动作——切菜、倒水、写字、拿杯子、整理物品 | 浅景深让背景虚化；侧光让手部纹理立体；动作放慢一拍，有仪式感；白/米色桌面做干净背景 | 手部过曝/欠曝=细节丢失；背景杂乱抢戏=失败；动作太快看不清=重拍 |
| **Portrait medium** （中景人像，带环境） | MS / MCU | eye-level | static / steadicam | slow | 3-5s | 2-3个 | rule-of-thirds, negative-space | shallow (f/2.0-f/2.8) | 创作者在环境中的自然状态——看书、喝咖啡、望向窗外、做饭间隙 | 侧光/侧逆光勾勒面部轮廓；人物占frame 1/3-1/2；环境留2/3；眼神不看镜头；可在画面边缘留前景虚化 | 眼神直视镜头=破坏沉浸感；平光无立体感=失败；背景过曝=窗户光线控制不当 |
| **Detail macro** （极致特写，食物/物品纹理） | ECU / CU | eye-level / high-angle | static | — | 2-3s | 2-3个 | center-framing, leading-lines | shallow (f/1.8-f/2.8) | 食物纹理/咖啡拉花/植物叶片/布料材质/水滴细节 | 最浅景深突出质感；自然侧光让纹理立体；构图极简，只留主体+柔和背景；可用微距镜头或近摄 | 对焦不实=最致命失败；过曝高光刺眼=失败；背景元素干扰主体=构图不对 |
| **Closing wide** （收尾大景，情绪消退） | LS / ELS | eye-level / high-angle | static / pan-left/right | slow | 4-5s | 1个 | negative-space, rule-of-thirds | deep (f/5.6-f/8) | 从近景切到开阔大景——落日窗景、雨幕街道、离开的背影、空房间 | 保留10-15%负空间在画面一侧留白；声音渐弱/环境音放大；镜头时长稍长给观众消化情绪的时间 | 画面塞满无呼吸空间=失败；切得太快就收尾=节奏不对；选择太杂乱的场景=破坏情绪 |

### 4.2 叙事结构模板

```
开场（Hook）：POV establish → Environmental wide（2个镜头，占总时长15%）
  → 以第一人称视角带入场景，再用环境大景交代氛围
  → 声音：环境音先入，lo-fi bgm 缓缓起来
主体（Body）：Hand detail ↔ Portrait medium ↔ Detail macro 交替（5-8个镜头，占总时长60%）
  → 手部细节（做事）→ 中景人像（状态）→ 手部/细节特写 → 人像
  → 节奏：慢→微快→慢，中间穿插1个环境wide做呼吸帧
  → 声音：以ASMR环境音为主（烹饪声/水流声/键盘声），bgm陪衬
高潮（Climax）：Detail macro → Portrait medium（2个镜头，占总时长15%）
  → 最佳光线下的最美细节特写，再接一个有沉浸感的人像镜头
收尾（Close）：Closing wide（1-2个镜头，占总时长10%）
  → 从近景拉远或从室内转到窗外/街道大景
  → 声音：bgm渐弱，环境音放大，缓缓淡出
```

### 4.3 最小可用素材集（MVP Shot List）

```
最少可用：6个镜头
1. POV establish: 第一人称走进房间/厨房（手持，与眼同高，慢速）
2. Environmental wide: 环境大景，交代氛围（侧光，深景深）
3. Hand detail: 手在做一件事——倒咖啡/切食材（浅景深，侧光）
4. Portrait medium: 人望向窗外的中景（侧逆光，浅景深）
5. Detail macro: 食物/物品极致特写（微距或近摄，最浅景深）
6. Closing wide: 从室内转到窗外/街道的收尾大景（留负空间，声音渐弱）
```

### 4.4 风格守卫（Style Guards）

```
✅ 合格信号：
  - 暖调柔光调色（色温4800-6200K，饱和度-20%至-30%）
  - 低对比度，高光柔和无溢出，阴影有细节
  - 浅景深为主，背景柔和虚化
  - 自然光主导（窗户光最佳），无人工硬光源
  - 固定与手持慢移交替，无剧烈晃动
  - 声音设计以ASMR环境音为主（烹饪/雨声/风声）
  - lo-fi / chill hop BGM在70-95BPM
  - 画面干净，构图简洁，善用负空间
  - 全局暖色调（米色/杏色/卡其/暖棕为主色系）
  - 眼神不看镜头，维持"被观察"的沉浸感

❌ 失败信号：
  - 冷色调或蓝色调过重（破坏温暖感）
  - 对比度过高，高光刺眼或阴影死黑
  - 饱和度偏高，颜色过于鲜艳（非褪色胶片感）
  - 手持抖动明显（超过轻微自然晃动）
  - 人物正对镜头说话或摆拍（出戏）
  - 画面杂乱，构图无重点
  - 音乐音量过大盖过环境音（破坏ASMR沉浸感）
  - 对焦不实（尤其是Detail macro镜头）
  - 正午顶光拍摄，人脸有刺眼阴影
  - 镜头切换过快（<1.5s），破坏舒缓节奏
```
