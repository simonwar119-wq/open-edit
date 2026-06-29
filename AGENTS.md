# AGENTS.md — `oe` 本地工具（给 agent 调用）

Open Edit 的整条流水线收口成一个本地命令 `./oe`。**给 AI agent 用**：所有日志走 stderr，
最终结果是 **stdout 上的一段 JSON**，直接解析即可。零云依赖也能跑（mock）。

## 一条命令出片

```bash
cd open-edit
./oe make --prompt "深夜居酒屋，威士忌特写，孤独冷峻" \
  --uploads 素材1.mp4 素材2.mp4 \
  --duration 16 --provider mock --subtitles --music \
  --out film.mp4
```

`make` 做完整流程：**分析素材 → AI 导演(选风格+排镜) → 生成补镜 → 风格化调色(保留上传素材原色) → 组接 → 逐字字幕 → 自动配乐**。

stdout 返回（节选）：
```json
{
  "output": ".../film_music.mp4",
  "duration_s": 16.0,
  "style": "fincher-inspired",
  "director": { "reason": "...", "directives": "...", "music_category": "cinematic", "source": "ai:..." },
  "clips": 4, "generated": 1, "uploads": 3, "cost_usd": 0.45,
  "subtitles": { "words": 48, "skipped": false },
  "music": { "category": "cinematic", "track": "cinema-03", "attribution": "... (Pixabay)" }
}
```

## 子命令

| 命令 | 作用 |
|---|---|
| `./oe styles` | 列出可用导演风格(JSON) |
| `./oe analyze <video...>` | 素材画面特征(亮度/饱和/节奏)(JSON) |
| `./oe plan --prompt ... [opts]` | 只规划出 EDL(JSON)，不渲染（便宜，先看导演决策） |
| `./oe make --prompt ... [opts]` | 一条龙出成片 |
| `./oe render <edl.json> [--subtitles] [--music]` | 渲染已有 EDL |
| `./oe subtitle <video> [--lang]` | 单独烧逐字字幕 |
| `./oe music <video> [--category]` | 单独加配乐 |
| `./oe animate <photo> --prompt "场景/运动"` | **一张照片 → 视频**(图生视频 Kling i2v，约$0.45/5s) |
| `./oe train-character <photo...> --name X` | **多角度照片 → 身份角色模型**(FLUX LoRA，约$2)，存为可复用资产 |
| `./oe characters` | 列出已训练的身份角色 |

```bash
# 训一次脸(10-20张多角度照片) → 之后 make 时同一张脸进每个生成镜头
./oe train-character p1.jpg p2.jpg ... --name 高先生
./oe make --prompt "深夜居酒屋，主角独饮" --character 高先生 --provider fal --duration 12
```

```bash
# 一张照片 + 一句场景 → 5秒视频
./oe animate my_photo.jpg --prompt "镜头缓慢推近，衣物随风轻摆，黄昏暖光" --out clip.mp4
```

## plan/make 选项

```
--prompt "一句话"        必填
--style auto|fincher-inspired|wes-anderson-inspired   默认 auto(导演选)
--uploads a.mp4 b.mp4    用户素材(不给则全部生成)
--duration 16            目标秒数
--provider mock|fal      mock=离线零成本；fal=真生成(花钱)
--video-model seedance-2.0-fast|seedance-2.0|kling-hq  fal 模型档(kling-hq=FLUX→Kling 高质量)
--subtitles [--lang zh]  逐字字幕
--music [--music-category tech|warm|energetic|cinematic]  自动配乐
--out film.mp4
```

## 给 agent 的调用守则

- **先 `plan` 后 `make`**：`plan` 不花钱不渲染，先看导演选了什么风格/排了几镜；满意再 `make`。
- **省钱**：`--provider mock` 全程零成本(生成镜头是占位)。要真画面才用 `--provider fal`（**每个生成镜头都是真钱**：seedance≈$0.2、kling-hq≈$0.45/镜）。给 `--uploads` 可把生成镜头压到最少。
- **错误**：失败时 stdout 是 `{"error": "..."}` 且退出码非 0。
- **环境变量**：真生成 `export FAL_API_KEY=...`；真 LLM 导演 `export OPENEDIT_LLM_PROVIDER=anthropic|openai` + key（缺则启发式选风格，仍可跑）。
- 成片/中间产物在 `engine/.work/`。

## 调色标准（重要，已内建）

上传素材**默认保原色**(`grade=preserve`)，只有生成镜头套风格 CDL+LUT。已调好色的素材不会被二次调色弄诡异。raw/log 素材想统一重调色 → 加 `--grade-scope all`。
