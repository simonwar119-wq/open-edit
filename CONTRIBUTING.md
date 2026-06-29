# 参与 Open Edit

> 欢迎。这里告诉你项目怎么组织的、从哪下手、怎么提 PR。

---

## 项目结构

```
open-edit/
├── oe                       # CLI 入口（一条命令出片）
├── oe.py                    # CLI 主逻辑
├── engine/                  # 纯函数 pipeline 内核
│   ├── providers/           # AI 生成后端（fal / mock）
│   ├── character.py         # Soul-LoRA 角色训练
│   ├── subtitles.py         # Whisper 逐字字幕
│   └── music.py             # 自动配乐
├── backend/                 # FastAPI 后端（SaaS 化进行中）
│   └── app/
│       ├── orchestrator.py  # AI 导演编排
│       ├── llm.py           # LLM 抽象层（Claude / DeepSeek / Mock）
│       └── analyze.py       # ffmpeg 素材分析
├── webui/                   # Flask WebUI（localhost:5050）
├── taxonomy/                # 🔑 风格知识库（项目的灵魂）
│   ├── 01-scine-translated/ # SCINE 76 节点中文翻译
│   ├── 02-editing-techniques/ # 剪辑手法（J-cut / Whip pan…）
│   ├── 03-styles/           # 风格模板（Fincher / Wes Anderson / 李子柒…）
│   └── 04-ffmpeg-recipes/   # 每条手法对应的 FFmpeg 命令
├── config/                  # API Key 配置（secrets.env 不入库）
├── scripts/                 # 工具脚本
├── references/              # 研究语料（14 篇论文 + 3 个仓库）
├── _research/               # 竞品研究（Higgsfield 等）
└── mcp_server.py            # MCP Server（10 个工具，Claude Code 可调）
```

---

## 30 秒跑起来

```bash
# 1. 装依赖
python3 -m venv backend/.venv
backend/.venv/bin/pip install fastapi uvicorn sqlalchemy faster-whisper httpx

# 2. Mock 模式（零成本跑通全流程）
./oe make --prompt "测试" --duration 10 --provider mock

# 3. 真 AI 生成（需 FAL_API_KEY）
export FAL_API_KEY=你的key
./oe make --prompt "深夜居酒屋" --duration 15 --provider fal
```

Mock 模式不需要任何 API Key，生成镜头用占位画面，流程全部跑通。

---

## 从哪下手

### 🟢 新手友好

| 任务 | 说明 |
|---|---|
| 写新的风格模板 | 在 `taxonomy/03-styles/custom-analysis/` 下新增一个创作者/作品风格分析，参考 `qmike-style-guide.md` |
| 补 FFmpeg recipe | `taxonomy/04-ffmpeg-recipes/` 下很多手法还没写执行层 FFmpeg 命令 |
| 加新的剪辑手法 | `taxonomy/02-editing-techniques/` 补充缺失的技法 |

### 🟡 需要一些上下文

| 任务 | 说明 |
|---|---|
| 接新的 AI 生成 provider | `engine/providers/` 下加新后端（Veo、Wan 等），实现 Provider 基类 |
| 完善 WebUI | `webui/` 目前只有 3 个 Tab，可以加更多交互 |
| 加测试 | 目前测试覆盖很少，任何测试都欢迎 |

### 🔴 核心贡献

| 任务 | 说明 |
|---|---|
| 成本实测 & 优化 | 跑真成片统计 keeper rate，降低单位成本 |
| 本地推理栈 | 把 Wan2.2 + LoRA 跑在本地（M4 Pro / RunPod），边际成本归零 |
| iOS 客户端 | SwiftUI 原生 app，接 backend API |

---

## 开发约定

- **Python 3.11+**，类型标注尽量写
- **EDL (JSON) 是流水线合约** — 所有模块通过 EDL 通讯，不直接调
- **LLM 不碰像素** — LLM 只管创作决策（选风格、排镜、写 prompt），渲染走 ffmpeg
- **先 plan 后 make** — `plan` 免费看导演决策，满意再 `make` 花钱
- **环境变量取 Key** — 不硬编码，不扫 `.env` 文件偷 Key
- 提交前跑一下 `./oe make --provider mock` 确认没坏

---

## 提 PR

1. Fork + clone
2. 开新分支：`git checkout -b feat/你的功能`
3. 写完 + 本地验证
4. PR 描述写清楚：做了什么、为什么、怎么测的
5. 如果涉及 taxonomy 文件，按四层结构写（描述/参数/执行/反向分镜）

---

## 需要帮助？

开 Issue，或者在 PR 里 @ 维护者。

---

## 致谢

项目的灵感来自：
- [SCINE](https://arxiv.org/abs/2509.26555) — 76 节点电影镜头控制层级
- [ShotDeck](https://shotdeck.com) — 电影/广告专业标注数据
- [Open Design](https://github.com/nexu-io/open-design) — 开源设计系统的思路平移
- [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill) — MCSLA prompt 工程化
