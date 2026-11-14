# Open Edit

> **本地 AI 电影工坊。** 上传素材 + 一句话，AI 导演分析画面、选风格、排镜头、AI 补拍缺失镜头、调色、字幕、配乐，一条命令出成片。开源，你的素材和角色模型永远归你。
>
> **A local AI film studio.** Drop your footage + one sentence, and an AI director analyzes the shots, picks a style, plans the sequence, generates missing scenes, color-grades, subtitles, and scores — one command to a finished film. Open source. Your footage, your character models, forever yours.

---

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status">
</p>

---

## 它能干什么

```
$ ./oe make --prompt "深夜居酒屋，威士忌特写，孤独冷峻" --uploads 素材1.mp4 素材2.mp4 --duration 16 --subtitles --music --out film.mp4
```

一条命令，AI 自动完成：

1. **分析素材** — 提取每段视频的分辨率、亮度、饱和度、节奏
2. **AI 导演决策** — 看素材 + 理解意图 → 选风格（Fincher？Wes Anderson？）→ 出完整 shot-plan
3. **补拍缺失镜头** — 调用 fal.ai（Seedance / Kling）AI 生成你拍不到的镜头
4. **风格化调色** — CDL + 自建 LUT，保持上传素材原色，只对生成镜头套风格
5. **逐字字幕** — Whisper 词级转录，卡拉OK 逐字高亮
6. **自动配乐** — 按导演情绪选曲，循环到片长 + 人声下垫底

**输出 = 一条带字幕配乐的成片 MP4。**

---

## 30 秒跑起来

```bash
git clone https://github.com/simonwar119-wq/open-edit.git
cd open-edit
./oe make --prompt "你想拍的" --duration 15 --provider mock
```

Mock 模式零成本跑通全流程。要真 AI 生成画面：`export FAL_API_KEY=你的key`，改 `--provider fal`。

---

## 怎么工作的

```
你的素材 + 一句话
       │
       ▼
  ┌─────────────────┐
  │   AI 导演大脑     │  DeepSeek / Claude 分析素材 → 选风格 → 排 shot-plan
  └────────┬────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  已有素材     需要补拍的镜头
     │           │
     │     ┌─────┴─────┐
     │     │  fal.ai    │  Seedance / Kling AI 生成
     │     │  角色 LoRA  │  你训过的脸自动进每个镜头
     │     └─────┬─────┘
     │           │
     └─────┬─────┘
           ▼
  ┌─────────────────┐
  │  剪辑 + 调色      │  CDL + LUT 风格化，上传素材保原色
  │  字幕 + 配乐      │  Whisper 逐字 + Pixabay 策展曲库
  └────────┬────────┘
           ▼
        film.mp4
```

---

## 知识库：把形容词翻译成参数

这是 Open Edit 的护城河。影视行业几十年积累的「电影感」「王家卫风」全是形容词——AI 听不懂。

Open Edit 把 53 个电影手法 / 风格模板翻译成四层可执行数据：

| 层 | 例子 |
|---|---|
| **描述层** | J-cut = 声音先进，画面后切 |
| **参数层** | 声音提前 0.5-1.5s，镜头时长 2-4s |
| **执行层** | `ffmpeg -i video -itsoffset 1.0 -i audio ...` |
| **反向分镜层** | 这个风格需要：1 个大特写(2s) + 2 个中景(3s) + 1 个全景(4s)… |

**两个工作模式共享同一知识库：**
- **模式 A**：素材 → 分析 → 推荐风格 → 剪辑 plan（适配现有素材）
- **模式 B**：选风格 → 出拍摄分镜表 → 你按表拍 → AI 剪辑（导演模式，全球无竞品）

---

## 已落地的能力

- ✅ **AI 导演** — DeepSeek 真看懂素材选风格排镜（已跑通端到端）
- ✅ **角色训练** — 10-20 张照片训 Soul-LoRA（$2/个），同一张脸进每个生成镜头
- ✅ **图生视频** — 一张照片 + 一句话 → 5s 视频
- ✅ **3 档画质** — Seedance 快速档 → Kling 高质量档（FLUX 出参考帧 + i2v）
- ✅ **字幕 + 配乐** — Whisper 逐字 + Pixabay 策展曲库混音
- ✅ **MCP Server** — 10 个工具，Claude Code 直接调
- ✅ **WebUI** — `http://127.0.0.1:5050`
- ✅ **J-cut 导出** — EDL + `oe render --j-cut c2:0.5`，保留切点后的音画同步；[用法与素材余量要求](engine/README.md#j-cut声音提前画面硬切)

---

## ROADMAP

| 优先级 | 事项 |
|---|---|
| 🔴 P0 | 成本实测：跑 5-10 条真成片，算 keeper rate |
| 🟡 P1 | SaaS 化：FastAPI + Temporal + R2 服务化 |
| 🟡 P1 | iOS 客户端（SwiftUI 原生） |
| 🟢 P2 | 本地推理栈：Wan2.2 + LoRA 本地跑，边际成本归零 |
| 🟢 P2 | 更多 AI 生成 provider（Kling O1 Edit / HeyGen / ElevenLabs） |
| 🟢 P3 | DaVinci Resolve MCP — 导出到专业调色/剪辑 |

想参与？见 [CONTRIBUTING.md](./CONTRIBUTING.md)。新手可以从 [good first issue](https://github.com/simonwar119-wq/open-edit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 标签入手。

---

## 竞品研究

我们花了 6/28 整晚深挖 [Higgsfield](https://higgsfield.ai)：
- **它的护城河 = 编排层 + 预设品味 + 上新速度，不是模型**（底模全是 Sora/Kling/Seedance）
- **我们的差异化** = 可导出 LoRA 权重 + 风格化剪辑调色合成（它只是个 clip 生成器）+ 本地可跑

详见 `_research/higgsfield-2026-06-28/`。

---

## License

MIT License. © 2025-2026 Mr.Gao（高牧洪）.

---

## 作者

Mr.Gao — 专业厨师、餐厅老板、美食内容创作者、AI 工程实践者。
项目同步在「Mr.Gao 的厨房」频道。
