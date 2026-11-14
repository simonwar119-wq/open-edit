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

## J-cut：声音提前、画面硬切

EDL 的后镜头支持 `"transition_in": {"type": "j-cut", "duration": 0.5}`。
`duration` 单位为秒，同时表示声音提前量和线性音频交叉淡化时长。
`in`/`out` 始终是**画面**的源时间；声音从 `in - duration` 开始，
在画面切点继续与同一源时间的画面同步。J-cut 不缩短画面时间线。

例如 A 的 `in=0, out=2`，B 的 `in=0.5, out=2.5`，B 的 J-cut 为 `0.5`：
输出为 4 秒；B 的声音从 1.5 秒淡入，2.0 秒硬切到 B 的画面。
在 24 fps 下，第 47 帧仍是 A，第 48 帧是 B 的源时间 0.5 秒。

已有 EDL 可直接渲染，也可从统一 CLI 指定镜头：

```bash
python oe.py render edit.edl.json --j-cut c2:0.5 --out film.mp4
# 多个入转场：追加 --j-cut c3:0.25
# 已写入 transition_in 的 EDL：python oe.py render edit.edl.json --out film.mp4
```

CLI 临时覆盖指定 clip id 的入转场，不改写原 EDL，也不移动其画面入出点。
要保存剪辑决策以重复渲染，把对应 `transition_in` 写回你另存的 EDL。
当前 `plan`/`make` 的自动导演仍选择原有 cut/dissolve；J-cut 通过 EDL/`render` 显式启用。
后端使用同一 `render_edl()` 时同样支持此 EDL。

素材和时间约束：

- 后镜头必须有音轨，且 `in >= duration`，以保留实际源声音余量；首镜不能设 J-cut。
- 提前量必须是有限正数，小于前镜头可用画面时长；前镜头有入叠化时扣除该叠化时长。
- 含 J-cut 的 EDL，其画面 in/out、J-cut 与叠化时长必须对齐输出帧边界；例如 24 fps 的 0.5 秒为 12 帧。
- 后镜头无音轨会报错，请使用普通 cut。前镜头无音轨或音轨较短会用静音补齐，不提前结束画面。
- 支持连续 J-cut 及与 cut/dissolve 混用；不含 J-cut 的 EDL 保留原有组接路径。
- 本版本把提前量与淡化时长绑定，尚不支持独立音频偏移或 L-cut。

来源：SeedanceCheap / @pesoszpesosz 的 [PR #4](https://github.com/simonwar119-wq/open-edit/pull/4)
提供了正确保留源音频余量的配方。App 渲染、校验与 CLI 集成另行实现。
[PR #5](https://github.com/simonwar119-wq/open-edit/pull/5) 指出了 LUT 路径的两层解析问题；
当前实现同时转义选项与 filtergraph，并以实际像素回归覆盖 100%/70% LUT 强度。

离线测试（需 Python 3.11+、带 libx264/eq/lut3d 的 FFmpeg 和 ffprobe；CLI 测试还需 httpx）：

```bash
python -m unittest engine.test_render -v
```

测试不访问生成服务，子进程有超时，解码检查画面、帧数、音轨时长和声音频率。
测试结果与平台限制见 [integration-validation.md](integration-validation.md)。
