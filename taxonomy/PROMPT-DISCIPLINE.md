# open-edit 纪律层（抄自 Higgsfield 工作流，已工程化落地）

> 2026-06-28 把 Higgsfield 的"工作流纪律"抄成 open-edit 的真实资产。研究底稿见 `_research/higgsfield-2026-06-28/`。
> 核心认知：**和 Higgsfield 的差距不在模型，在编排和纪律。** 这一层就是把纪律变成代码。

## 已落地的 4 件资产

| 文件 | 是什么 | 怎么用 |
|---|---|---|
| `taxonomy/dop_camera_presets.json` | **DoP 相机预设库**（66 预设 + 情绪处方 + 组合/冲突规则），对标 Higgsfield DoP。每个预设是模型无关的镜头语言宏。 | `oe_camera_presets` MCP 工具 / `engine.prompt_kit.camera()` |
| `engine/prompt_kit.py` | **MCSLA 五层公式** + 真实感词库 + 反 slop 替换 + 身份/运动分块 + Seedance 六槽/五模式 + 引擎硬约束。 | `from engine.prompt_kit import mcsla, seedance_i2v, identity_motion_blocks` |
| `engine/seedance_lint.py` | **生成前预检 linter**：便条语域/冲突运镜/塑料触发词/slop/槽位缺失/长度。把彩票税前置成本地秒检。 | `oe_lint_prompt` MCP 工具 / `python -m engine.seedance_lint "..."` |
| `engine/ledger.py` | **生成台账**：记每次 kept/rejected/成本，算 keeper rate（takes-per-kept）、累计成本、iterate-vs-batch 判定。 | `python -m engine.ledger log/ratio/budget/fork` |

## 抄过来的核心纪律（写进上述代码）

1. **MCSLA 公式**：Model + Camera(命名预设) + Subject + Look + Action。一镜一主导运镜，<200 词。
2. **防漂移 3 铁律**：①character sheet 一图一张脸 ②身份块 ⟂ 运动块物理分离、跨镜逐字复用（`identity_motion_blocks()`）③一次只改一个变量。
3. **真实感**：要 `pores/sheen/uneven falloff/35mm grain`；**禁** `flawless/perfect/8k/beautiful`（塑料脸触发词，linter 会抓）。
4. **Seedance 五模式**：Reference / Continuation / Expand / Edit / Transformation（`SEEDANCE_MODES`）。
5. **液体/慢动作**：别让模型直接出慢动作（必崩）→ 正常速生成 + 后期补帧慢放。
6. **彩票税工程化**：keeper rate 20-33%、真实成本 3-5x → 用 ledger 量化、用 lint 预检、用 iterate/batch fork 决策。

## 待接（下一步）
- 把 `mcsla()` + `lint()` 接进 `engine/build_edl.py` 的生成镜头 prompt 构造（现在生成镜头还没走纪律层）。
- 把 `ledger.log_gen()` 接进 fal provider 的每次生成（自动记台账）。
- 相机预设接进导演大脑：按镜头情绪用 `emotion_sync` 自动选运镜。
- 拿到官方 Seedance 2.0 key 后，用 reference-to-video + 首尾帧重做香槟（走"正常生成+后期慢放"管线）。
