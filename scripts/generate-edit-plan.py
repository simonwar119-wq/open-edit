#!/usr/bin/env python3
"""
Open Edit — 剪辑方案生成器 (Edit Plan Generator)
==========================================
用途：给定风格 + 素材列表，从风格档案的 Layer 2/3 读取参数，
     输出一份含时间线编排 + FFmpeg 命令的完整剪辑方案。

用法：
    # 基本用法
    python generate-edit-plan.py \\
        --style qmike \\
        --footage footage.txt \\
        --music track.mp3 \\
        --duration 60 \\
        --output outputs/edit-plan-steak.md

    # footage.txt 格式（每行一条素材）：
    #   clip_001.mp4 | 3s | 牛排下锅特写，烟雾升腾
    #   clip_002.mp4 | 5s | 中景，翻面动作
    #   clip_003.mp4 | 8s | 全景，厨房环境建立镜头
    #   ...

参数：
    --style    风格档案名
    --footage  素材清单文件路径（见上方格式说明）
    --music    音乐文件路径（可选，用于 BPM 分析）
    --bpm      手动指定 BPM（如 --bpm 95，不提供 --music 时用）
    --duration 目标时长（秒，默认60）
    --output   输出文件路径
"""

import argparse
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TAXONOMY_DIR = PROJECT_ROOT / "taxonomy" / "03-styles"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


# ── 工具函数（复用 generate-shot-list.py 的解析逻辑）──────

def find_style_file(style_name: str) -> Path:
    for subdir in ["custom-analysis", "from-shotdeck"]:
        candidates = [
            TAXONOMY_DIR / subdir / f"{style_name}.md",
            TAXONOMY_DIR / subdir / f"{style_name}-style-guide.md",
        ]
        for path in candidates:
            if path.exists():
                return path
    available = [
        f.stem.replace("-style-guide", "")
        for subdir in ["custom-analysis", "from-shotdeck"]
        for f in (TAXONOMY_DIR / subdir).glob("*.md")
        if f.name != "_template.md" and (TAXONOMY_DIR / subdir).exists()
    ]
    raise FileNotFoundError(
        f"找不到风格档案：{style_name}\n可用风格：{sorted(set(available))}"
    )


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    yaml_text = content[3:end].strip()
    body = content[end + 4:].strip()
    meta = {}
    for line in yaml_text.split("\n"):
        if ": " in line and not line.startswith(" "):
            key, _, val = line.partition(": ")
            meta[key.strip()] = val.strip().strip('"')
    return meta, body


def extract_layer(body: str, layer_num: int) -> str:
    """提取指定 Layer 的内容"""
    pattern = re.compile(rf'^## Layer {layer_num}[:\s]', re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    start = match.start()
    next_h2 = re.search(r'^## ', body[start + 10:], re.MULTILINE)
    if next_h2:
        end = start + 10 + next_h2.start()
        return body[start:end].strip()
    return body[start:].strip()


# ── Layer 2 参数解析 ──────────────────────────────────────

def parse_layer2_params(layer2_text: str) -> dict:
    """从 Layer 2 提取关键参数"""
    params = {}

    # 色温
    m = re.search(r'(\d{4})[–\-](\d{4})\s*K', layer2_text)
    if m:
        params["color_temp_min"] = int(m.group(1))
        params["color_temp_max"] = int(m.group(2))
        params["color_temp_mid"] = (params["color_temp_min"] + params["color_temp_max"]) // 2

    # 饱和度偏移
    m = re.search(r'[Ss]aturation[：:]?\s*[−\-](\d+)%?\s*(?:to|至|~)\s*[−\-](\d+)%?', layer2_text)
    if m:
        params["saturation_offset"] = -(int(m.group(1)) + int(m.group(2))) // 2
    else:
        m = re.search(r'[Ss]aturation[：:]?\s*([−\-]?\d+)%', layer2_text)
        if m:
            params["saturation_offset"] = int(m.group(1).replace('−', '-'))

    # 对比度偏移
    m = re.search(r'[Cc]ontrast[：:]?\s*[−\-](\d+)%?\s*(?:to|至|~)\s*[−\-](\d+)%?', layer2_text)
    if m:
        params["contrast_offset"] = -(int(m.group(1)) + int(m.group(2))) // 2
    else:
        m = re.search(r'[Cc]ontrast[：:]?\s*([−\-]?\d+)%', layer2_text)
        if m:
            params["contrast_offset"] = int(m.group(1).replace('−', '-'))

    # 平均镜头时长
    m = re.search(r'avg.*?([\d.]+)[–\-]([\d.]+)\s*s', layer2_text, re.IGNORECASE)
    if m:
        params["avg_shot_duration"] = (float(m.group(1)) + float(m.group(2))) / 2
    else:
        # 从表格里找
        m = re.search(r'[\d.]+[–\-]([\d.]+)\s*s.*?shot', layer2_text)
        if m:
            params["avg_shot_duration"] = float(m.group(1))

    if "avg_shot_duration" not in params:
        params["avg_shot_duration"] = 1.5  # 默认值

    # 转场比例（硬切）
    m = re.search(r'[Hh]ard.cut.*?(\d+)%', layer2_text)
    if m:
        params["hard_cut_pct"] = int(m.group(1))
    else:
        params["hard_cut_pct"] = 80  # 默认

    # 画幅比例
    m = re.search(r'(9:16|16:9|1:1)', layer2_text)
    if m:
        params["aspect_ratio"] = m.group(1)
    else:
        params["aspect_ratio"] = "9:16"  # 短视频默认

    return params


# ── Layer 3 FFmpeg 命令提取 ────────────────────────────────

def extract_ffmpeg_commands(layer3_text: str) -> list[dict]:
    """提取 Layer 3 中所有 FFmpeg 命令块"""
    commands = []

    # 找所有代码块
    code_blocks = re.finditer(r'###\s*(.+?)\n+```bash\n(.*?)```', layer3_text, re.DOTALL)
    for block in code_blocks:
        section_name = block.group(1).strip()
        cmd_text = block.group(2).strip()
        commands.append({
            "name": section_name,
            "command": cmd_text,
        })

    return commands


def get_primary_grade_command(commands: list[dict], style_name: str) -> str:
    """获取主调色命令（优先返回完整调色 filtergraph）"""
    # 优先找标记为"主调色"或"Warm"的命令
    for cmd in commands:
        if any(k in cmd["name"].lower() for k in ["主调色", "warm", "color grade", "调色"]):
            return cmd["command"]

    # 否则返回第一个
    if commands:
        return commands[0]["command"]

    # 默认：根据 style_name 生成基础调色命令
    return (
        f"# 主调色（{style_name} 基础参数）\n"
        f"ffmpeg -i INPUT.mp4 \\\n"
        f"  -vf \"eq=contrast=0.9:saturation=0.8:brightness=0.02,\\\n"
        f"       colorbalance=rs=0.05:gs=0.02:bs=-0.03\" \\\n"
        f"  # contrast: -10% | saturation: -20% | warm shift\n"
        f"  OUTPUT_graded.mp4"
    )


# ── 素材文件解析 ──────────────────────────────────────────

def parse_footage_file(filepath: str) -> list[dict]:
    """
    解析素材清单文件
    格式：clip_001.mp4 | 3s | 牛排下锅特写，烟雾升腾
    """
    clips = []
    path = Path(filepath)
    if not path.exists():
        print(f"❌ 素材清单文件不存在：{filepath}", file=sys.stderr)
        return clips

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split("|")]
            filename = parts[0] if len(parts) > 0 else f"clip_{i:03d}.mp4"
            duration = parts[1] if len(parts) > 1 else "?"
            description = parts[2] if len(parts) > 2 else "无描述"

            # 解析时长数字
            dur_s = 0.0
            m = re.search(r'([\d.]+)', duration)
            if m:
                dur_s = float(m.group(1))

            clips.append({
                "index": i,
                "filename": filename,
                "duration_str": duration,
                "duration_s": dur_s,
                "description": description,
            })

    return clips


def estimate_bpm_from_file(music_file: str) -> int | None:
    """尝试用 ffprobe 或 librosa 检测 BPM（可选功能）"""
    try:
        import librosa
        y, sr = librosa.load(music_file, duration=60)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return int(round(tempo))
    except ImportError:
        print("⚠️  librosa 未安装，跳过 BPM 检测（pip install librosa）", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  BPM 检测失败：{e}", file=sys.stderr)
        return None


# ── 剪辑方案生成 ──────────────────────────────────────────

def assign_clips_to_structure(
    clips: list[dict],
    params: dict,
    total_duration: int
) -> dict:
    """
    根据叙事结构比例，将素材分配到各段
    结构：hook(15%) → body(65%) → climax(10%) → close(10%)
    """
    structure = {
        "hook":   {"pct": 0.15, "clips": [], "budget_s": 0},
        "body":   {"pct": 0.65, "clips": [], "budget_s": 0},
        "climax": {"pct": 0.10, "clips": [], "budget_s": 0},
        "close":  {"pct": 0.10, "clips": [], "budget_s": 0},
    }

    for phase, info in structure.items():
        info["budget_s"] = total_duration * info["pct"]

    # 简单策略：按描述关键词分配
    phase_keywords = {
        "hook":   ["建立", "全景", "环境", "开场", "establishing", "wide"],
        "climax": ["最佳", "最好", "高潮", "hero", "成品", "final", "hero shot"],
        "close":  ["结尾", "收尾", "close", "fade", "out", "空镜"],
    }

    used = set()
    for phase, keywords in phase_keywords.items():
        for clip in clips:
            if clip["index"] in used:
                continue
            desc_lower = clip["description"].lower()
            if any(k in desc_lower for k in keywords):
                structure[phase]["clips"].append(clip)
                used.add(clip["index"])

    # 剩余素材全部放 body
    for clip in clips:
        if clip["index"] not in used:
            structure["body"]["clips"].append(clip)

    return structure


def calculate_edit_timing(
    structure: dict,
    params: dict,
    total_duration: int,
    bpm: int | None
) -> list[dict]:
    """计算每条素材的时间线位置和目标时长"""
    avg_shot = params.get("avg_shot_duration", 1.5)
    timeline = []
    cursor = 0.0

    phase_order = ["hook", "body", "climax", "close"]
    phase_names = {
        "hook": "开场", "body": "主体", "climax": "高潮", "close": "收尾"
    }

    # BPM 换算：一拍时长
    beat_duration = (60.0 / bpm) if bpm else None

    for phase in phase_order:
        info = structure[phase]
        clips = info["clips"]
        budget_s = info["budget_s"]
        phase_cn = phase_names[phase]

        if not clips:
            continue

        # 根据段落预算分配每条素材的时长
        per_clip_budget = budget_s / len(clips) if clips else avg_shot

        for clip in clips:
            # 目标时长：按预算，但限制在合理范围内
            target_dur = max(0.5, min(per_clip_budget, clip["duration_s"] or per_clip_budget))

            # 如果有 BPM，对齐到最近的拍子
            if beat_duration:
                beats = max(1, round(target_dur / beat_duration))
                target_dur = beats * beat_duration

            in_point = 0.0  # 素材入点（默认从头开始，用户后期调整）

            timeline.append({
                "phase": phase,
                "phase_cn": phase_cn,
                "index": clip["index"],
                "filename": clip["filename"],
                "description": clip["description"],
                "source_duration": clip["duration_s"],
                "target_duration": round(target_dur, 2),
                "timeline_start": round(cursor, 2),
                "timeline_end": round(cursor + target_dur, 2),
                "in_point": in_point,
                "beat_aligned": beat_duration is not None,
                "beats": round(target_dur / beat_duration) if beat_duration else None,
            })
            cursor += target_dur

    return timeline


def build_ffmpeg_batch_script(
    timeline: list[dict],
    grade_command: str,
    style_name: str,
    output_dir: str = "outputs/graded"
) -> str:
    """生成批量调色的 FFmpeg shell 脚本"""
    lines = [
        "#!/bin/bash",
        f"# Open Edit — {style_name} 批量调色脚本",
        f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"OUTPUT_DIR=\"{output_dir}\"",
        f"mkdir -p \"$OUTPUT_DIR\"",
        f"",
        f"# ── 调色参数（来自风格档案 Layer 3）────────────────",
        f"# {grade_command.split(chr(10))[0]}",
        f"",
    ]

    # 提取 filtergraph（-vf 参数内容）
    vf_match = re.search(r'-vf\s+"([^"]+)"', grade_command)
    vf_filter = vf_match.group(1) if vf_match else "eq=contrast=0.9:saturation=0.8"

    lines.append("# ── 批量处理每条素材 ────────────────────────────────")
    lines.append("")

    seen = set()
    for clip in timeline:
        fname = clip["filename"]
        if fname in seen:
            continue
        seen.add(fname)

        stem = Path(fname).stem
        lines.append(f"echo \"处理：{fname}\"")
        lines.append(
            f"ffmpeg -i \"{fname}\" \\\n"
            f"  -vf \"{vf_filter}\" \\\n"
            f"  -c:v libx264 -crf 18 -preset slow \\\n"
            f"  -c:a copy \\\n"
            f"  \"$OUTPUT_DIR/{stem}_graded.mp4\""
        )
        lines.append("")

    lines.append("echo \"✅ 批量调色完成，输出目录：$OUTPUT_DIR\"")
    return "\n".join(lines)


def build_edit_plan_document(
    meta: dict,
    params: dict,
    timeline: list[dict],
    commands: list[dict],
    grade_cmd: str,
    clips: list[dict],
    topic: str,
    total_duration: int,
    bpm: int | None,
    style_name: str,
) -> str:
    """组装剪辑方案文档"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_source = sum(c["duration_s"] for c in clips)
    total_timeline = sum(t["target_duration"] for t in timeline)

    lines = []

    # ── 标题 ──────────────────────────────────────────────
    lines.append("# 剪辑方案")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|-----|---|")
    lines.append(f"| 主题 | {topic} |")
    lines.append(f"| 风格 | {style_name} |")
    lines.append(f"| 目标时长 | {total_duration}s |")
    lines.append(f"| 素材总时长 | {total_source:.1f}s |")
    lines.append(f"| 规划使用时长 | {total_timeline:.1f}s |")
    lines.append(f"| BPM | {bpm if bpm else '未检测（请手动调整剪辑点）'} |")
    lines.append(f"| 画幅 | {params.get('aspect_ratio', '9:16')} |")
    lines.append(f"| 生成时间 | {now} |")
    lines.append("")

    # ── 关键参数速查 ───────────────────────────────────────
    lines.append("## 关键参数速查")
    lines.append("")
    lines.append("| 参数 | 值 | 说明 |")
    lines.append("|-----|---|------|")

    temp_min = params.get("color_temp_min", "")
    temp_max = params.get("color_temp_max", "")
    temp_str = f"{temp_min}–{temp_max}K" if temp_min and temp_max else "5200K"
    lines.append(f"| 色温 | `{temp_str}` | 暖色调，后期调色目标值 |")

    sat = params.get("saturation_offset", -20)
    lines.append(f"| 饱和度 | `{sat:+d}%` | 相对原始素材的偏移量 |")

    con = params.get("contrast_offset", -10)
    lines.append(f"| 对比度 | `{con:+d}%` | 偏低对比，柔和感 |")

    avg = params.get("avg_shot_duration", 1.5)
    lines.append(f"| 平均镜头时长 | `{avg}s` | 剪辑点密度参考 |")

    hc = params.get("hard_cut_pct", 80)
    lines.append(f"| 硬切比例 | `{hc}%` | 其余 {100-hc}% 用特效转场 |")

    if bpm:
        beat_ms = round(60000 / bpm)
        lines.append(f"| BPM | `{bpm}` | 每拍 {beat_ms}ms，剪辑点参考 |")

    lines.append("")

    # ── 时间线编排 ─────────────────────────────────────────
    lines.append("## 时间线编排")
    lines.append("")
    lines.append("> 以下为建议排列顺序，素材使用时长已按叙事结构分配。")
    lines.append("> DaVinci / Premiere 中按此顺序排列素材，再微调剪辑点。")
    lines.append("")

    current_phase = None
    for clip in timeline:
        if clip["phase"] != current_phase:
            current_phase = clip["phase"]
            lines.append(f"### {clip['phase_cn']}（{clip['phase'].upper()}）")
            lines.append("")

        beat_info = f"（{clip['beats']} 拍）" if clip["beat_aligned"] and clip["beats"] else ""
        lines.append(
            f"**{clip['index']:02d}. `{clip['filename']}`** — "
            f"{clip['timeline_start']}s → {clip['timeline_end']}s "
            f"（使用 {clip['target_duration']}s{beat_info}）"
        )
        lines.append(f"> {clip['description']}")
        lines.append("")

    # ── 调色命令 ───────────────────────────────────────────
    lines.append("## 调色方案（Layer 3 执行层）")
    lines.append("")
    lines.append("### 主调色命令")
    lines.append("")
    lines.append("```bash")
    lines.append("# 将 INPUT.mp4 替换为实际文件名")
    lines.append(grade_cmd)
    lines.append("```")
    lines.append("")

    if len(commands) > 1:
        lines.append("### 其他可用命令")
        lines.append("")
        for cmd in commands[1:]:
            lines.append(f"#### {cmd['name']}")
            lines.append("")
            lines.append("```bash")
            lines.append(cmd["command"])
            lines.append("```")
            lines.append("")

    # ── 批量处理脚本 ───────────────────────────────────────
    lines.append("## 批量调色脚本")
    lines.append("")
    lines.append("将以下内容保存为 `grade_all.sh`，在素材目录下运行 `bash grade_all.sh`：")
    lines.append("")
    lines.append("```bash")
    batch = build_ffmpeg_batch_script(timeline, grade_cmd, style_name)
    lines.append(batch)
    lines.append("```")
    lines.append("")

    # ── 剪辑指导 ───────────────────────────────────────────
    lines.append("## 剪辑操作指导")
    lines.append("")
    lines.append("### Step 1：素材整理")
    lines.append("1. 运行上方批量调色脚本，对所有素材统一调色")
    lines.append("2. 在 DaVinci/Premiere 新建项目，帧率 24fps，分辨率与主摄一致")
    lines.append(f"3. 画幅设为 {params.get('aspect_ratio', '9:16')}（竖屏/横屏）")
    lines.append("")
    lines.append("### Step 2：导入与粗剪")
    lines.append("1. 按上方时间线顺序导入素材")
    lines.append("2. 每条素材粗剪到目标时长（±0.5s 误差内）")
    if bpm:
        beat_s = round(60 / bpm, 3)
        lines.append(f"3. 打开节拍标记（BPM {bpm}，每 {beat_s}s 一拍），主要剪辑点对齐拍子")
    else:
        lines.append("3. 选好背景音乐，打开节拍标记，主要剪辑点对齐鼓点")
    lines.append("")
    lines.append("### Step 3：转场")
    lines.append(f"- 80% 使用直切（硬切），不加任何效果")
    lines.append(f"- 场景切换处可用 Whip Pan 转场（0.1–0.2s）")
    lines.append(f"- 高潮段前可加速度坡道（speed ramp）")
    lines.append("")
    lines.append("### Step 4：精修")
    lines.append("- 检查色彩一致性（全片色温统一）")
    lines.append("- 音乐淡入/淡出（开头 0.5s / 结尾 1.0s）")
    lines.append("- 字幕/标题（如需）")
    lines.append("")
    lines.append("---")
    lines.append(f"*由 Open Edit generate-edit-plan.py 生成 | 风格: {style_name} | {now}*")

    return "\n".join(lines)


# ── 主程序 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Open Edit — 剪辑方案生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
footage.txt 格式（每行：文件名 | 时长 | 描述）：
  clip_001.mp4 | 3s | 牛排下锅特写，烟雾升腾
  clip_002.mp4 | 5s | 中景，翻面动作
  clip_003.mp4 | 8s | 全景，厨房环境建立镜头

示例：
  python generate-edit-plan.py --style qmike --footage footage.txt --bpm 95 --duration 60
        """
    )

    parser.add_argument("--style", type=str, required=True, help="风格档案名")
    parser.add_argument("--footage", type=str, required=True, help="素材清单文件路径")
    parser.add_argument("--topic", type=str, default="拍摄主题", help="拍摄主题描述")
    parser.add_argument("--music", type=str, default=None, help="音乐文件（用于BPM检测）")
    parser.add_argument("--bpm", type=int, default=None, help="手动指定BPM")
    parser.add_argument("--duration", type=int, default=60, help="目标时长（秒）")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")

    args = parser.parse_args()

    # 读取风格文件
    try:
        style_path = find_style_file(args.style)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📂 风格文件：{style_path}", file=sys.stderr)
    content = style_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)

    # 提取 Layer 2 和 Layer 3
    layer2_text = extract_layer(body, 2)
    layer3_text = extract_layer(body, 3)

    if not layer2_text:
        print(f"⚠️  Layer 2 为空，将使用默认参数", file=sys.stderr)
    if not layer3_text:
        print(f"⚠️  Layer 3 为空，将使用默认 FFmpeg 命令", file=sys.stderr)

    params = parse_layer2_params(layer2_text)
    commands = extract_ffmpeg_commands(layer3_text) if layer3_text else []
    grade_cmd = get_primary_grade_command(commands, args.style)

    print(f"✅ 解析参数：色温 {params.get('color_temp_min', '?')}–{params.get('color_temp_max', '?')}K | "
          f"饱和度 {params.get('saturation_offset', '?')}% | "
          f"平均镜头时长 {params.get('avg_shot_duration', '?')}s", file=sys.stderr)

    # 解析素材清单
    clips = parse_footage_file(args.footage)
    if not clips:
        print(f"❌ 素材清单为空或解析失败", file=sys.stderr)
        sys.exit(1)
    print(f"✅ 读取素材：{len(clips)} 条", file=sys.stderr)

    # BPM
    bpm = args.bpm
    if not bpm and args.music:
        bpm = estimate_bpm_from_file(args.music)
        if bpm:
            print(f"✅ 检测到 BPM：{bpm}", file=sys.stderr)

    # 分配素材到叙事结构
    structure = assign_clips_to_structure(clips, params, args.duration)

    # 计算时间线
    timeline = calculate_edit_timing(structure, params, args.duration, bpm)

    # 构建文档
    doc = build_edit_plan_document(
        meta=meta,
        params=params,
        timeline=timeline,
        commands=commands,
        grade_cmd=grade_cmd,
        clips=clips,
        topic=args.topic,
        total_duration=args.duration,
        bpm=bpm,
        style_name=args.style,
    )

    # 输出
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(doc, encoding="utf-8")
        print(f"✅ 剪辑方案已保存：{out_path}", file=sys.stderr)
    else:
        print(doc)


if __name__ == "__main__":
    main()
