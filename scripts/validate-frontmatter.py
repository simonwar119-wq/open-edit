#!/usr/bin/env python3
"""
Open Edit — Frontmatter 自动校验脚本

用途：遍历 taxonomy/ 下所有 .md 文件，检查 YAML frontmatter 是否符合 SKILL.md 第 3 节 schema。
用法：python3 scripts/validate-frontmatter.py

exit code 0 = 全部通过
exit code 1 = 存在不合规文件（输出到 stderr）
"""

import os
import re
import sys
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_DIR = os.path.join(PROJECT_ROOT, "taxonomy")

ERRORS = []


def extract_frontmatter(text):
    """Extract YAML frontmatter between --- markers."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    return m.group(1)


def infer_file_type(filepath):
    """Infer file type from path location."""
    rel = os.path.relpath(filepath, TAXONOMY_DIR)
    if rel.startswith("03-styles"):
        return "style"
    if rel.startswith("02-editing-techniques"):
        return "technique"
    if rel.startswith("04-ffmpeg-recipes"):
        return "recipe"
    if rel.startswith("01-scine-translated"):
        return "scine"
    return "unknown"


def get_required_fields(file_type):
    schemas = {
        "style": {
            "required": ["name", "description", "category", "subcategory", "source", "layer4_ready", "last_updated"],
            "enums": {
                "category": ["style"],
                "subcategory": ["custom-analysis", "from-shotdeck"],
                "layer4_ready": [True, False],
            }
        },
        "technique": {
            "required": ["name", "description", "category", "complexity", "requires_audio", "ffmpeg_available", "source", "last_updated"],
            "enums": {
                "category": ["cut", "transition", "rhythm-pattern", "narrative-structure"],
                "complexity": ["low", "medium", "high"],
                "requires_audio": [True, False],
                "ffmpeg_available": [True, False],
            }
        },
        "recipe": {
            "required": ["name", "for_technique", "ffmpeg_version_tested", "platform_tested", "complexity", "last_updated"],
            "enums": {
                "platform_tested": ["macOS", "Linux", "Windows"],
                "complexity": ["low", "medium", "high"],
            }
        },
        "scine": {
            "required": ["name", "last_updated"],
            "enums": {},
        },
        "unknown": {
            "required": ["name", "last_updated"],
            "enums": {},
        }
    }
    return schemas.get(file_type, schemas["unknown"])


def validate_file(filepath):
    relpath = os.path.relpath(filepath, PROJECT_ROOT)
    file_type = infer_file_type(filepath)
    schema = get_required_fields(file_type)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_fm = extract_frontmatter(content)
    if raw_fm is None:
        ERRORS.append(f"❌ {relpath} (type={file_type}): 缺少 YAML frontmatter")
        return

    try:
        data = yaml.safe_load(raw_fm)
    except yaml.YAMLError as e:
        ERRORS.append(f"❌ {relpath}: YAML 解析失败 — {e}")
        return

    if not isinstance(data, dict):
        ERRORS.append(f"❌ {relpath}: frontmatter 内容不是 key-value 格式")
        return

    # Check required fields
    for field in schema["required"]:
        if field not in data or data[field] is None:
            ERRORS.append(f"❌ {relpath}: 必填字段 '{field}' 缺失或为空")

    # Check enum fields
    for field, allowed_values in schema["enums"].items():
        if field in data and data[field] not in allowed_values:
            ERRORS.append(
                f"❌ {relpath}: 字段 '{field}' 值为 '{data[field]}'，"
                f"允许值: {allowed_values}"
            )


def main():
    if not os.path.isdir(TAXONOMY_DIR):
        print(f"❌ taxonomy/ 目录未找到: {TAXONOMY_DIR}")
        sys.exit(1)

    md_files = []
    for root, dirs, files in os.walk(TAXONOMY_DIR):
        # Skip .gitkeep files
        files = [f for f in files if f.endswith(".md")]
        for f in files:
            md_files.append(os.path.join(root, f))

    if not md_files:
        print("❌ taxonomy/ 下没有 .md 文件")
        sys.exit(1)

    # Special: overview.md, scouting reports, etc. can skip strict check
    skip_list = {"00-overview.md", "00-schema-v1.md", "00-editing-overview.md"}

    for fpath in sorted(md_files):
        fname = os.path.basename(fpath)
        if fname in skip_list:
            continue
        validate_file(fpath)

    total = len(md_files) - len(skip_list)
    if ERRORS:
        print(f"📊 检查了 {total} 个文件，发现 {len(ERRORS)} 个问题:\n", file=sys.stderr)
        for err in ERRORS:
            print(err, file=sys.stderr)
        sys.exit(1)
    else:
        print(f"✅ 全部 {total} 个文件 frontmatter 校验通过")


if __name__ == "__main__":
    main()
