# open-edit 工程打包说明（2026-06-28）

> 给 Mr.Gao 回退评估用。本包 = 代码 + 研究 + 已训角色资产。**不含密钥(secrets.env 已排除)、不含 venv/大模型权重(可重装)。**

## 一、已落地的工程（能跑的代码）
| 模块 | 文件 | 作用 |
|---|---|---|
| 生成引擎 | `engine/` | 纯函数 pipeline：build_edl / render / providers(fal) / character(LoRA训练) / subtitles / music |
| CLI | `oe.py` + `oe` | `./oe make/plan/animate/train-character/...` 一条命令出片 |
| **MCP server** | `mcp_server.py` | 10 个工具让 Claude Code 直接调 open-edit(oe_make/oe_camera_presets/oe_lint_prompt/...) |
| 后端 | `backend/app/` | FastAPI(JSON API + AI 导演 orchestrator) |
| **纪律层(抄 Higgsfield)** | `engine/prompt_kit.py` / `engine/seedance_lint.py` / `engine/ledger.py` / `taxonomy/dop_camera_presets.json` | MCSLA 公式 + 66 相机预设 + prompt 预检 + 生成台账 |
| 配置中心 | `config/` | 所有 API key 统一(secrets.env 本包已排除) + loader |
| 旧 web 原型 | `web/` | Flask 风格分析页(v1 遗留，和生成核心未打通) |

## 二、已训角色资产（你拥有的，$ 已花）
- `engine/characters/baba.json` + `baba.safetensors`(85MB) — 爸爸 Soul-LoRA，trigger=`baba_man`
- `engine/characters/yuer.json` + `yuer.safetensors`(89MB) — 鱼儿 Soul-LoRA，trigger=`yuer_boy`

## 三、研究成果（`_research/higgsfield-2026-06-28/`）
- `00-总纲-先读这个.md` — Higgsfield 深挖总纲
- `01-官方技术逆向.md` / `02-开源技术对标.md` / `03-社区实操秘籍.md` / `04-可落地工作流与prompt骨架.md` / `05-NotebookLM跨86视频问答.md`

## 四、关键结论（决定"自建 vs 买 Higgsfield"的事实）
1. **Higgsfield 护城河 = 编排+预设+上新速度+代理商分发，不是模型。** 底模全是接的。
2. **身份一致最终方案** = 训可导出 Soul-LoRA(锚) + 关键帧定死脸 + i2v 保持 + 纪律约束；裸 i2v 锁不住真人脸。
3. **官方火山 Seedance 中国区拦真人输入图**(需肖像授权) → 人物镜走 fal，无人脸/空镜走官方(1080p)。
4. **成本现实(要重新评测的核心)**：
   - fal 人物镜 ~$1.5/5s(720p)；官方无人脸 ~11元/5s(1080p,实测2.25元/秒)。
   - **彩票税 keeper rate 20-33% → 真实成本 ×3-5。** 一条 25s 片现实 ~$35-55。
   - **Higgsfield 订阅 Plus $39/mo(1000 credits)/ Ultra $99/mo。** ← 低产量时订阅可能比我们按次烧更便宜。这是你担心"成本高于 Higgsfield"的关键点。
5. **香槟问题真正解法** = 慢动作生成+后期加速(Speed-ramp)，或无人脸特写走官方 1080p(已验证效果好)。

## 五、诚实的现状判断
- **能跑通**：角色训练 / 关键帧 / i2v / MCP 调用 / 混合(官方空镜+fal人物) / 研究纪律层。
- **偏离风险**：一直在堆战术能力(换脸/官方API/config)，没回答"单位成本 vs Higgsfield 订阅"这个生意账。
- **待决策**：自建走"按次 API"成本可能 > Higgsfield 订阅；真正省钱要等终态本地栈(Wan2.2+LoRA 本地/RunPod，边际成本≈0)，但那需要前期投入。**这正是你要重新评测的。**
