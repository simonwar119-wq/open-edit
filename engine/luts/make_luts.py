#!/usr/bin/env python3
"""合成 Phase 0 用的创意 .cube 3D LUT（无第三方依赖，纯 Python）。

为什么自建而不是下社区 LUT：社区 LUT 商用授权要逐个确认（plan 风险项），
自建的可商用、可复现、可参数化。Phase 0 先给两个标志性 look：
    bleach-bypass.cube   高对比 + 去饱和 + 阴影偏青（Fincher 风）
    pastel-highkey.cube  抬暗部 + 低对比 + 暖粉调（Wes Anderson 风）

LUT 是 input RGB(0..1) → output RGB(0..1) 的查找表。size=17（17^3=4913 格，够用且小）。
渲染时 FFmpeg `lut3d=file=xxx.cube:interp=tetrahedral` 应用。
"""

from pathlib import Path

SIZE = 17
LUTS_DIR = Path(__file__).resolve().parent


def clamp(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def luma(r: float, g: float, b: float) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def bleach_bypass(r: float, g: float, b: float):
    """高对比、低饱和、阴影偏青——冷峻控制(Fincher)风。"""
    y = luma(r, g, b)
    # 去饱和：向亮度靠拢（保留 ~45% 原色）
    sat = 0.45
    r = lerp(y, r, sat)
    g = lerp(y, g, sat)
    b = lerp(y, b, sat)
    # 提对比：以 0.5 为轴的 S 曲线
    def contrast(v, k=1.35):
        return clamp((v - 0.5) * k + 0.5)
    r, g, b = contrast(r), contrast(g), contrast(b)
    # 阴影偏青/绿（暗部加一点 g/b，减一点 r），高光略暖
    shadow = clamp(1.0 - y * 1.6)      # 越暗权重越大
    r = clamp(r - 0.04 * shadow + 0.02 * (1 - shadow))
    g = clamp(g + 0.025 * shadow)
    b = clamp(b + 0.05 * shadow)
    return r, g, b


def pastel_highkey(r: float, g: float, b: float):
    """抬暗部、低对比、暖粉高调——对称童趣(Wes Anderson)风。"""
    y = luma(r, g, b)
    # 抬暗部（lift）+ 压一点高光 → 低对比
    def lowcon(v, lift=0.10, k=0.82):
        return clamp(lift + (v * k) * (1 - lift))
    r, g, b = lowcon(r), lowcon(g), lowcon(b)
    # 暖粉调：整体加暖（r 多、b 少），中间调加品红一点点
    r = clamp(r + 0.04)
    g = clamp(g + 0.015)
    b = clamp(b - 0.02)
    # 略降饱和让其"粉彩"
    sat = 0.85
    y2 = luma(r, g, b)
    r = lerp(y2, r, sat)
    g = lerp(y2, g, sat)
    b = lerp(y2, b, sat)
    return r, g, b


def write_cube(name: str, fn, title: str):
    out = LUTS_DIR / name
    lines = [
        f"# Open Edit generated LUT — {title}",
        "# 可商用 (CC0) · size=17 · 生成: engine/luts/make_luts.py",
        f"TITLE \"{title}\"",
        f"LUT_3D_SIZE {SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    n = SIZE - 1
    # .cube 顺序：红色变化最快，最外层蓝
    for bi in range(SIZE):
        for gi in range(SIZE):
            for ri in range(SIZE):
                r, g, b = fn(ri / n, gi / n, bi / n)
                lines.append(f"{clamp(r):.6f} {clamp(g):.6f} {clamp(b):.6f}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ {out}  ({SIZE}^3 = {SIZE**3} entries)")


def main():
    write_cube("bleach-bypass.cube", bleach_bypass, "Bleach Bypass Teal")
    write_cube("pastel-highkey.cube", pastel_highkey, "Pastel High-Key")


if __name__ == "__main__":
    main()
