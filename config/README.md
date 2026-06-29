# config — open-edit 的 API 密钥与配置中心

> 项目所有 API key 统一放这里，不再依赖 `AutoClip/api/.env`。
> **真实密钥在 `secrets.env`（已 gitignore，不会进版本库）；`api_keys.example.env` 是脱敏模板。**

## 用法
```python
from config.loader import load_keys
load_keys()   # 把 secrets.env 的 key 注入 os.environ
```
或终端：`set -a; source config/secrets.env; set +a`

## API 清单（咱们要用的 + 可能用到的）

### 🟢 核心 — 现在就在用
| 变量 | 服务 | 用途 | 状态 |
|---|---|---|---|
| `FAL_API_KEY` | fal.ai | **生成核心**：Seedance 2.0 / Kling / Nano Banana Pro / FLUX-LoRA 训练 / face-swap | ✅ 已有 |
| `DEEPSEEK_API_KEY` | DeepSeek | 导演大脑（选风格/排镜的 LLM） | ✅ 已有 |
| `GEMINI_API_KEY` | Google Gemini | Gemini CLI（研究/多 agent 讨论） | ✅ 已有(~/.zshrc) |

### 🟡 官方 Seedance 2.0 — 计划接入（待办）
| 变量 | 服务 | 用途 | 状态 |
|---|---|---|---|
| `ARK_API_KEY` | 火山引擎·火山方舟 | **官方 Seedance 2.0**(reference-to-video + 首尾帧 + 1080p)，Bearer token | ⏳ 待申请 |
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` | 火山引擎 | 火山其他服务（AK/SK 签名式） | ✅ 已有 |

### 🔵 可能用到 — 备选/未来
| 变量 | 服务 | 用途 | 备注 |
|---|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter | LLM 路由（仅非美三家 LLM 备用） | ⚠️ **无视频生成；且本账号区域被封 OpenAI/Anthropic/Google → NBP/GPT Image/Claude/GPT/Gemini 全用不了。只剩 DeepSeek/Qwen/Mistral/Llama/GLM/Grok/MiniMax。价值低（图像走 fal，director 用 DeepSeek 直连）** |
| `ANTHROPIC_API_KEY` | Anthropic | Claude 当导演/agent（可选） | 按需 |
| `DASHSCOPE_API_KEY` | 阿里灵积 | **Wan 2.2 视频模型官方 API**（终态本地省钱栈相关） | ✅ 已有 |
| `DEEPGRAM_API_KEY` | Deepgram | ASR 字幕（我们现用本地 faster-whisper，这是备选） | ✅ 已有 |
| `DOUBAO_API_KEY` | 豆包/火山 | LLM/Vision 备选 | ✅ 已有 |
| `OSS_ACCESS_KEY` | 阿里云 OSS | 云存储 | ✅ 已有 |
| `SHOTSTACK_API_KEY` | Shotstack | 云端视频渲染（备选，我们现用本地 FFmpeg） | ✅ 已有 |
| `REMOTION_AWS_ACCESS_KEY` / `REMOTION_AWS_SECRET_ACCESS_KEY` | AWS(Remotion Lambda) | 旧 AutoClip 的渲染栈，open-edit 用 FFmpeg，**大概率不用** | ✅ 已有 |

## 安全
- `secrets.env` 在 `.gitignore`，**永不提交**。
- 别把 key 写进代码/日志/commit。
