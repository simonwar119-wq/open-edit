#!/usr/bin/env python3
"""open-edit MCP server — 把整条 open-edit pipeline 暴露成 Claude Code 能直接调用的 typed 工具。

设计：薄包装，零逻辑重复。直接 import 现有 `oe.py` 的 cmd_* 函数（它们本就是
agent 友好的：日志走 stderr，结果走 emit）。我们把 `oe.emit` 拦截掉，让结果回到
工具返回值，而不是打到 stdout（stdout 被 MCP stdio 协议占用）。

运行：  backend/.venv/bin/python mcp_server.py
注册：  claude mcp add open-edit -- /绝对路径/backend/.venv/bin/python /绝对路径/mcp_server.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import oe  # noqa: E402  现有 CLI；import 安全（main() 有 __main__ 守卫）
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("open-edit")

# ── emit 拦截：把 cmd_* 的结果从 stdout 转到返回值 ──────────────
_PLAN_DEFAULTS = dict(
    prompt="", style="auto", uploads=[], duration=16.0, provider="mock",
    video_model=None, grade_scope="auto", character=None, edl_out=None,
)


def _call(cmd_func, **attrs) -> dict:
    """构造 args namespace → 调 cmd_func → 拦截 emit → 返回 dict。"""
    holder: dict = {}
    real_emit = oe.emit
    oe.emit = lambda obj: holder.setdefault("result", obj)
    try:
        cmd_func(SimpleNamespace(**attrs))
    except SystemExit as e:  # cmd 内部不会 sys.exit，但稳妥兜底
        holder["result"] = {"error": f"SystemExit: {e}"}
    except Exception as e:
        holder["result"] = {"error": f"{type(e).__name__}: {e}"}
    finally:
        oe.emit = real_emit
    return holder.get("result", {"error": "no result emitted"})


# ── 工具：信息查询（快、无网络、无花费）────────────────────────
@mcp.tool()
def oe_styles() -> dict:
    """列出所有可用的导演风格 profile（id + 名称 + 节奏/调色摘要）。零成本。"""
    return _call(oe.cmd_styles)


@mcp.tool()
def oe_characters() -> dict:
    """列出已训练的身份角色（Soul-LoRA）：slug / 名称 / trigger_word。零成本。"""
    return _call(oe.cmd_characters)


@mcp.tool()
def oe_analyze(videos: list[str]) -> dict:
    """分析素材画面特征（亮度/饱和/节奏/分镜）。输入视频路径列表。零成本（本地 ffprobe）。"""
    return _call(oe.cmd_analyze, videos=videos)


# ── 工具：规划（便宜，不渲染、不生成）──────────────────────────
@mcp.tool()
def oe_plan(prompt: str, style: str = "auto", uploads: list[str] | None = None,
           duration: float = 16.0, provider: str = "mock",
           video_model: str | None = None, grade_scope: str = "auto",
           character: str | None = None) -> dict:
    """AI 导演规划：选风格 + 反向分镜 → 产出 EDL(JSON)，不渲染不生成。
    先 plan 看导演决策满意了再 make。provider=mock 全程零成本。
    返回 {edl: 路径, director: 决策, stats: 镜头数/成本估算}。"""
    return _call(oe.cmd_plan, **{**_PLAN_DEFAULTS, "prompt": prompt, "style": style,
                                 "uploads": uploads or [], "duration": duration,
                                 "provider": provider, "video_model": video_model,
                                 "grade_scope": grade_scope, "character": character})


# ── 工具：出片（provider=fal 时花真钱）─────────────────────────
@mcp.tool()
def oe_make(prompt: str, style: str = "auto", uploads: list[str] | None = None,
           duration: float = 16.0, provider: str = "mock",
           video_model: str | None = None, grade_scope: str = "auto",
           character: str | None = None, subtitles: bool = False,
           lang: str | None = None, music: bool = False,
           music_category: str | None = None, out: str | None = None) -> dict:
    """一条龙出片：规划 → 生成补镜 → 风格化调色 → 组接 → [字幕] → [配乐] → 成片。
    ⚠️ provider='fal' 每个生成镜头都花真钱（seedance≈$0.2、kling-hq≈$0.45/镜）；
    provider='mock' 零成本占位。给 uploads 可把生成镜头压到最少。
    character=角色 slug 时生成镜头锁同一张脸。返回 {output, cost_usd, clips, ...}。"""
    return _call(oe.cmd_make, **{**_PLAN_DEFAULTS, "prompt": prompt, "style": style,
                                 "uploads": uploads or [], "duration": duration,
                                 "provider": provider, "video_model": video_model,
                                 "grade_scope": grade_scope, "character": character,
                                 "subtitles": subtitles, "lang": lang, "music": music,
                                 "music_category": music_category, "out": out})


@mcp.tool()
def oe_render(edl: str, out: str | None = None, subtitles: bool = False,
              lang: str | None = None, music: bool = False,
              music_category: str | None = None) -> dict:
    """渲染一个已有的 EDL(JSON 路径) → 成片。可选烧字幕/加配乐。返回 {output, duration_s}。"""
    return _call(oe.cmd_render, edl=edl, out=out, subtitles=subtitles, lang=lang,
                 music=music, music_category=music_category)


@mcp.tool()
def oe_animate(image: str, prompt: str, provider: str = "fal",
               model: str = "kling-i2v", duration: float = 5.0,
               out: str | None = None) -> dict:
    """一张照片 + 一句场景/运动 → 视频（图生视频 i2v）。⚠️ provider='fal' 花真钱(约$0.45/5s)。
    返回 {output, model, cost_usd, duration_s, commercial_ok}。"""
    return _call(oe.cmd_animate, image=image, prompt=prompt, provider=provider,
                 model=model, duration=duration, out=out)


@mcp.tool()
def oe_camera_presets(category: str | None = None) -> dict:
    """列出 DoP 相机预设库（对标 Higgsfield DoP，66 个）。可按 category 过滤
    (dolly/crane/orbit/zoom/follow/handheld/specialty/time/pan-tilt/...)。
    每个预设含 prompt_fragment（可注入 i2v prompt）+ best_for + face_safe。"""
    import json as _json
    from pathlib import Path as _P
    data = _json.loads((_P(ROOT) / "taxonomy" / "dop_camera_presets.json").read_text(encoding="utf-8"))
    presets = data["presets"]
    if category:
        presets = [p for p in presets if p["category"] == category]
    return {"count": len(presets), "presets": presets, "emotion_sync": data["emotion_sync"]}


@mcp.tool()
def oe_lint_prompt(prompt: str, zh: bool = False) -> dict:
    """生成前预检一条 Seedance prompt（彩票税前置）：查便条语域/冲突运镜/塑料触发词/
    slop 词/槽位缺失/长度。返回 {ok, score, errors, warnings}。errors=很可能挂。"""
    from engine.seedance_lint import lint
    return lint(prompt, zh=zh)


@mcp.tool()
def oe_train_character(photos: list[str], name: str, trigger: str | None = None,
                       steps: int = 1000) -> dict:
    """多角度照片(10-20张) → 训练身份角色 Soul-LoRA（FLUX LoRA，约 $2，永久拥有）。
    ⚠️ 调 fal 训练，花真钱。返回 {character, trigger_word, lora_url, n_photos}。"""
    return _call(oe.cmd_train_character, photos=photos, name=name, trigger=trigger, steps=steps)


if __name__ == "__main__":
    mcp.run()  # 默认 stdio transport
