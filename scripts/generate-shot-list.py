#!/usr/bin/env python3
"""
Open Edit — Mode B: 分镜清单生成器 (Shot List Generator)
==========================================
用途：给定风格 + 拍摄主题，从风格档案的 Layer 4 读取拍摄蓝图，
     输出一份可以直接拿去拍摄的分镜清单文档。

用法：
    python generate-shot-list.py \\
        --style qmike \\
        --topic "Mr.Gao 牛排料理过程" \\
        --duration 60 \\
        --output outputs/shot-list-steak.md

参数：
    --style    风格档案名（不含路径和.md，如 qmike、li-ziqi）
    --topic    拍摄主题（自由描述，用于定制化输出）
    --duration 目标视频时长（秒，默认60）
    --genre    拍摄类型（food/travel/lifestyle/portrait，默认food）
    --mvp      是否只输出最小可用清单（默认False，输出完整版）
    --output   输出文件路径（默认打印到终端）
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TAXONOMY_DIR = PROJECT_ROOT / "taxonomy" / "03-styles"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


# ── 工具函数 ──────────────────────────────────────────────

def find_style_file(style_name: str) -> Path:
    """在 taxonomy/03-styles/ 下搜索风格文件"""
    # 先在 custom-analysis/ 找
    for subdir in ["custom-analysis", "from-shotdeck"]:
        candidates = [
            TAXONOMY_DIR / subdir / f"{style_name}.md",
            TAXONOMY_DIR / subdir / f"{style_name}-style-guide.md",
        ]
        for path in candidates:
            if path.exists():
                return path
    raise FileNotFoundError(
        f"找不到风格档案：{style_name}\n"
        f"搜索路径：{TAXONOMY_DIR}/custom-analysis/ 和 from-shotdeck/\n"
        f"可用风格：{list_available_styles()}"
    )


def list_available_styles() -> list[str]:
    """列出所有可用的风格名称"""
    styles = []
    for subdir in ["custom-analysis", "from-shotdeck"]:
        d = TAXONOMY_DIR / subdir
        if d.exists():
            for f in d.glob("*.md"):
                if f.name != "_template.md":
                    styles.append(f.stem.replace("-style-guide", ""))
    return sorted(styles)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，返回 (meta_dict, body_content)"""
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


def extract_layer4(body: str) -> str:
    """从 markdown body 中提取 Layer 4 节"""
    # 找 Layer 4 的起始位置
    pattern = re.compile(r'^## Layer 4[:\s]', re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""

    start = match.start()
    # 找下一个同级 ## 或文件结尾
    next_h2 = re.search(r'^## ', body[start + 10:], re.MULTILINE)
    if next_h2:
        end = start + 10 + next_h2.start()
        return body[start:end].strip()
    return body[start:].strip()


def parse_shot_types_table(layer4_text: str) -> list[dict]:
    """解析 4.1 镜头类型清单表格"""
    shots = []

    # 找表格区域（4.1 节）
    section = re.search(r'### 4\.1.*?(?=### 4\.2|\Z)', layer4_text, re.DOTALL)
    if not section:
        return shots

    table_text = section.group(0)

    # 解析 markdown 表格行
    rows = []
    for line in table_text.split("\n"):
        line = line.strip()
        if line.startswith("|") and not re.match(r'^\|[-\s|]+\|$', line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[0] != "镜头类型":
                rows.append(cells)

    headers = ["type", "scale", "angle", "movement", "duration", "count", "content", "notes", "failure"]
    for row in rows:
        shot = {}
        for i, header in enumerate(headers):
            shot[header] = row[i] if i < len(row) else ""
        # 清理粗体标记
        shot["type"] = re.sub(r'\*\*(.*?)\*\*', r'\1', shot["type"])
        shots.append(shot)

    return shots


def parse_narrative_structure(layer4_text: str) -> dict:
    """解析 4.2 叙事结构"""
    structure = {}
    section = re.search(r'### 4\.2.*?```(.*?)```', layer4_text, re.DOTALL)
    if not section:
        return structure

    content = section.group(1).strip()
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 匹配 "开场（Hook）：..." 格式
        m = re.match(r'^(开场|主体|高潮|收尾)[（(](\w+)[）)][:：](.*)', line)
        if m:
            phase_cn, phase_en, desc = m.groups()
            structure[phase_en.lower()] = {
                "phase_cn": phase_cn,
                "description": desc.strip()
            }
    return structure


def parse_mvp_list(layer4_text: str) -> list[str]:
    """解析 4.3 最小可用素材集"""
    mvp = []
    section = re.search(r'### 4\.3.*?```(.*?)```', layer4_text, re.DOTALL)
    if not section:
        return mvp

    content = section.group(1).strip()
    for line in content.split("\n"):
        m = re.match(r'^\d+\.\s+(.*)', line.strip())
        if m:
            mvp.append(m.group(1).strip())
    return mvp


def parse_style_guards(layer4_text: str) -> dict:
    """解析 4.4 风格守卫"""
    guards = {"pass": [], "fail": []}
    section = re.search(r'### 4\.4.*?```(.*?)```', layer4_text, re.DOTALL)
    if not section:
        return guards

    content = section.group(1)
    current = None
    for line in content.split("\n"):
        line = line.strip()
        if "✅" in line:
            current = "pass"
        elif "❌" in line:
            current = "fail"
        elif line.startswith("- ") and current:
            guards[current].append(line[2:].strip())
    return guards


def calculate_shot_durations(shots: list[dict], total_duration: int,
                              structure: dict) -> list[dict]:
    """根据叙事结构分配各镜头的时长"""
    # 解析叙事结构中各段的百分比
    phase_pcts = {
        "hook": 15, "body": 65, "climax": 10, "close": 10  # 默认
    }
    for phase, info in structure.items():
        desc = info.get("description", "")
        m = re.search(r'占总时长(\d+)%', desc)
        if m:
            phase_pcts[phase] = int(m.group(1))

    # 解析每个 shot 的推荐时长范围
    for shot in shots:
        duration_str = shot.get("duration", "2-3s")
        m = re.search(r'([\d.]+)[\-–]([\d.]+)', duration_str)
        if m:
            shot["duration_min"] = float(m.group(1))
            shot["duration_max"] = float(m.group(2))
            shot["duration_mid"] = (shot["duration_min"] + shot["duration_max"]) / 2
        else:
            m2 = re.search(r'([\d.]+)', duration_str)
            val = float(m2.group(1)) if m2 else 2.0
            shot["duration_min"] = val
            shot["duration_max"] = val
            shot["duration_mid"] = val

    return shots


def build_shot_list_document(
    meta: dict,
    shots: list[dict],
    structure: dict,
    mvp: list[str],
    guards: dict,
    topic: str,
    duration: int,
    genre: str,
    mvp_only: bool
) -> str:
    """组装最终输出文档"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    style_name = meta.get("name", "unknown")
    style_desc = meta.get("description", "")

    lines = []

    # ── 标题页 ────────────────────────────────────────────
    lines.append(f"# 分镜拍摄清单")
    lines.append(f"")
    lines.append(f"| 字段 | 值 |")
    lines.append(f"|-----|---|")
    lines.append(f"| 拍摄主题 | {topic} |")
    lines.append(f"| 目标风格 | {style_name} |")
    lines.append(f"| 目标时长 | {duration}s |")
    lines.append(f"| 拍摄类型 | {genre} |")
    lines.append(f"| 生成时间 | {now} |")
    lines.append(f"| 生成工具 | Open Edit — 模式B分镜生成器 |")
    lines.append(f"")

    # ── 风格简介 ──────────────────────────────────────────
    lines.append(f"## 风格概述")
    lines.append(f"")
    lines.append(f"> {style_desc[:200] if style_desc else '无描述'}")
    lines.append(f"")

    # ── MVP 清单（优先显示，拍摄前快速参考）─────────────
    if mvp:
        lines.append(f"## ⚡ 最小可用清单（MVP — 最少必拍镜头）")
        lines.append(f"")
        lines.append(f"> 时间紧迫时只拍这些，保证基本可剪。")
        lines.append(f"")
        for i, item in enumerate(mvp, 1):
            lines.append(f"- [ ] **镜头 {i}**：{item}")
        lines.append(f"")

    if mvp_only:
        return "\n".join(lines)

    # ── 叙事结构 ──────────────────────────────────────────
    if structure:
        lines.append(f"## 叙事结构（拍摄顺序参考）")
        lines.append(f"")
        phase_order = ["hook", "body", "climax", "close"]
        phase_icons = {"hook": "🎬", "body": "📽️", "climax": "🔥", "close": "🌅"}

        for phase in phase_order:
            info = structure.get(phase)
            if not info:
                continue
            icon = phase_icons.get(phase, "▶️")
            phase_cn = info["phase_cn"]
            desc = info["description"]
            lines.append(f"### {icon} {phase_cn}（{phase.upper()}）")
            lines.append(f"")
            lines.append(f"{desc}")
            lines.append(f"")

    # ── 完整镜头清单 ──────────────────────────────────────
    lines.append(f"## 完整镜头清单")
    lines.append(f"")
    lines.append('> 拍摄前：逐条阅读"拍摄要点"和"失败信号"')
    lines.append("> 拍摄中：每类镜头拍满建议数量的 1.5 倍（备用素材）")
    lines.append('> 拍摄后：用"风格守卫"检查素材合格率')
    lines.append(f"")

    for i, shot in enumerate(shots, 1):
        shot_type = shot.get("type", f"Shot {i}")
        scale = shot.get("scale", "")
        angle = shot.get("angle", "")
        movement = shot.get("movement", "")
        duration_str = shot.get("duration", "")
        count = shot.get("count", "")
        content = shot.get("content", "")
        notes = shot.get("notes", "")
        failure = shot.get("failure", "")

        lines.append(f"### 镜头类型 {i}：{shot_type}")
        lines.append(f"")
        lines.append(f"| 参数 | 值 |")
        lines.append(f"|-----|---|")
        if scale:
            lines.append(f"| 景别 | `{scale}` |")
        if angle:
            lines.append(f"| 角度 | `{angle}` |")
        if movement:
            lines.append(f"| 运镜 | `{movement}` |")
        if duration_str:
            lines.append(f"| 参考时长 | {duration_str} |")
        if count:
            lines.append(f"| 建议数量 | {count} |")
        lines.append(f"")

        if content:
            lines.append(f"**拍什么：** {content}")
            lines.append(f"")

        if notes:
            # 按分号或句号分割拍摄要点
            note_items = re.split(r'[；;]', notes)
            note_items = [n.strip() for n in note_items if n.strip()]
            lines.append(f"**拍摄要点：**")
            for note in note_items:
                if note:
                    lines.append(f"- {note}")
            lines.append(f"")

        if failure:
            fail_items = re.split(r'[；;]', failure)
            fail_items = [f.strip() for f in fail_items if f.strip()]
            lines.append(f"**❌ 失败信号（看到这些立刻重拍）：**")
            for f_item in fail_items:
                if f_item:
                    lines.append(f"- {f_item}")
            lines.append(f"")

        lines.append(f"- [ ] 已拍（至少 {count.split('-')[-1] if count else '3'} 条备选）")
        lines.append(f"")

    # ── 风格守卫 ──────────────────────────────────────────
    if guards["pass"] or guards["fail"]:
        lines.append(f"## 风格守卫（拍摄后素材验收）")
        lines.append(f"")
        lines.append(f"> 每条素材用以下标准过一遍。合格率 < 60% 说明拍摄方向错了。")
        lines.append(f"")

        if guards["pass"]:
            lines.append(f"### ✅ 合格信号（素材要有这些特征）")
            for item in guards["pass"]:
                lines.append(f"- {item}")
            lines.append(f"")

        if guards["fail"]:
            lines.append(f"### ❌ 失败信号（有这些就是废片）")
            for item in guards["fail"]:
                lines.append(f"- {item}")
            lines.append(f"")

    # ── 拍摄清单 Checklist ────────────────────────────────
    lines.append(f"## 出发前检查")
    lines.append(f"")
    lines.append(f"- [ ] 相机电池满电")
    lines.append(f"- [ ] 储存卡空间充足（建议至少留 30GB）")
    lines.append(f"- [ ] 画面格式：4K 60fps（慢动作素材需要）/ 4K 24fps（正常素材）")
    lines.append(f"- [ ] 色彩配置文件：F-log / ProRes RAW / 中性（后期调色空间最大）")
    lines.append(f"- [ ] 时间：黄金时刻（日出后 1h / 日落前 1h）—— 除非特别标注")
    lines.append(f"- [ ] 音频：内置麦克风录制环境音（后期用）")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*由 Open Edit generate-shot-list.py 生成 | 风格: {style_name} | {now}*")

    return "\n".join(lines)


# ── 主程序 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Open Edit 模式B — 分镜清单生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 生成 Qmike 风格的牛排拍摄清单
  python generate-shot-list.py --style qmike --topic "Mr.Gao 牛排料理" --duration 60

  # 只输出 MVP 最小清单（赶时间用）
  python generate-shot-list.py --style qmike --topic "牛排" --mvp

  # 查看所有可用风格
  python generate-shot-list.py --list-styles
        """
    )

    parser.add_argument("--style", type=str, help="风格档案名（如 qmike）")
    parser.add_argument("--topic", type=str, default="拍摄主题未指定", help="拍摄主题描述")
    parser.add_argument("--duration", type=int, default=60, help="目标视频时长（秒）")
    parser.add_argument("--genre", type=str, default="food",
                        choices=["food", "travel", "lifestyle", "portrait", "sport", "brand"],
                        help="拍摄类型")
    parser.add_argument("--mvp", action="store_true", help="只输出最小可用清单")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径（默认打印到终端）")
    parser.add_argument("--list-styles", action="store_true", help="列出所有可用风格")

    args = parser.parse_args()

    # 列出风格
    if args.list_styles:
        styles = list_available_styles()
        print("可用风格档案（layer4_ready 的）：")
        for s in styles:
            print(f"  - {s}")
        return

    if not args.style:
        parser.print_help()
        sys.exit(1)

    # 读取风格文件
    try:
        style_path = find_style_file(args.style)
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}", file=sys.stderr)
        sys.exit(1)

    print(f"📂 读取风格文件：{style_path}", file=sys.stderr)

    content = style_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)

    # 检查 layer4_ready
    if meta.get("layer4_ready", "false").lower() != "true":
        print(f"⚠️  警告：{args.style} 的 layer4_ready = false，Layer 4 可能不完整", file=sys.stderr)

    # 提取 Layer 4
    layer4_text = extract_layer4(body)
    if not layer4_text:
        print(f"❌ 错误：在 {args.style} 中找不到 Layer 4 内容", file=sys.stderr)
        sys.exit(1)

    # 解析各部分
    shots = parse_shot_types_table(layer4_text)
    structure = parse_narrative_structure(layer4_text)
    mvp_list = parse_mvp_list(layer4_text)
    guards = parse_style_guards(layer4_text)

    if not shots:
        print(f"⚠️  警告：解析到 0 个镜头类型，请检查风格档案的 4.1 节格式", file=sys.stderr)
    else:
        print(f"✅ 解析到 {len(shots)} 个镜头类型", file=sys.stderr)

    shots = calculate_shot_durations(shots, args.duration, structure)

    # 构建文档
    doc = build_shot_list_document(
        meta=meta,
        shots=shots,
        structure=structure,
        mvp=mvp_list,
        guards=guards,
        topic=args.topic,
        duration=args.duration,
        genre=args.genre,
        mvp_only=args.mvp,
    )

    # 输出
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(doc, encoding="utf-8")
        print(f"✅ 分镜清单已保存：{out_path}", file=sys.stderr)
    else:
        print(doc)


if __name__ == "__main__":
    main()
