# engine — Open Edit v2 内核（Phase 0 CLI 纵切）

生成即核心的 AI 电影短片流水线的 Python 内核。证明 spine：
**生成 → 按导演风格组接 → CDL+LUT 调色 → 渲染成片**。
之后由 `backend/`（FastAPI + Temporal）包成服务，`web/` + `ios/` 接它。

## 设计要点

- **EDL(JSON) 是合同**：`build_edl` 只规划产出 EDL；`render` 纯函数消费 EDL → 渲染可复现、可 diff、可重跑、可被用户在 NLE 里精修。LLM 永不碰像素。
- **风格 = 数据**：`profiles/*.json`（v2 schema）同时驱动剪辑节奏（ASL/转场）、调色（CDL+LUT）、生成镜头的 prompt 风格（`generation_hints`）、反向分镜（模式B）。
- **provider 收口**：所有生成厂商实现 `GenerationProvider.submit()`，持久化 provider+model+cost+commercial_ok。无 `FAL_KEY` 时用 `MockProvider`（离线零成本）跑通整条 spine。

## 快速开始

```bash
cd open-edit                      # 必须在 engine/ 的父目录（包根）

# 1. 生成创意 LUT（可商用，自建）
python3 engine/luts/make_luts.py

# 2. 规划：prompt + 风格 → 反向分镜 + 生成补缺 → EDL(JSON)
#    （--uploads 给真实素材；不给则全部生成）
python3 -m engine.build_edl \
  --style fincher-inspired \
  --prompt "牛排在铸铁锅上油花四溅，黄油浇汁，慢动作特写" \
  --duration 16 --uploads qmike样片1.MP4 \
  --provider mock \
  --out engine/.work/steak.edl.json

# 3. 渲染：EDL → MP4（Pass1 逐clip归一化+调色，Pass2 xfade/acrossfade 组接）
python3 -m engine.render engine/.work/steak.edl.json --out engine/.work/steak_final.mp4
```

接真生成：`export FAL_KEY=...` 后把 `--provider mock` 换成 `--provider fal`。

## 目录

```
engine/
├── style_profile.py     v2 profile 加载/访问
├── edl.py               EDL 契约 + 校验 + 存取
├── build_edl.py         模式B 规划器（CLI）：prompt+风格 → EDL
├── render.py            纯函数渲染（CLI）：EDL → MP4
├── providers/
│   ├── base.py          GenerationProvider 接口 + GenSpec/GenResult
│   ├── mock.py          离线零成本替身（FFmpeg 合成带标签 clip）
│   └── fal.py           fal.ai 接入（需 FAL_KEY，未在无 key 环境跑过）
├── luts/make_luts.py    合成可商用 .cube 3D LUT
├── profiles/*.json      v2 风格 profile
└── .work/               中间产物 + 成片（gitignore）
```

## 已知 Phase 0 取舍（Phase 1 修）

- 调色：CDL 用 `colorchannelmixer`(slope)+`eq`(power→gamma, offset→brightness, saturation) 近似；offset 取三通道均值（非逐通道）。LUT 用 `lut3d` + `blend` 做 intensity 混合。
- 转场：硬切用 1 帧 `xfade=fade` 近似（保持单一 xfade 链路），dissolve 用真转场时长。
- 输入色彩空间假设 Rec.709（手机素材）；log 检测/归一化未实现。
- `fal.py` 轮询而非 webhook；并发/backpressure 未做（fal 起步并发仅 2）。
