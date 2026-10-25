#!/usr/bin/env python3
"""把 NbaMotionStudio 生涯竞速页的五种展示样式接到 MarketMotionStudio 的条形竞速页。

渲染器本体（Render/RaceStyle.cs、SectorRaceRenderer 的四路分频绘制）与共享控件
（Views/RaceStyleCombo.cs）由本次改动直接写入，不归本脚本管；本脚本只做两类
机械、幂等的批量插入：

1. 12 个竞速页面（XAML + code-behind）：
   - XAML 在 <views:VideoSettingsPanel> 之前插一行 <views:RaceStyleCombo>；
   - cs 在 `VideoSettings.Restore(_prefs);` 之后插 `Bind(_prefs)` 与 `Chosen` 订阅；
   - cs 在 `new SectorRaceRenderer(...)` 对象初始化器里插 `Style = RaceStyleCombo.ChosenStyle,`。
2. 14 份 Resources.resw：从 NbaMotionStudio 同名文案移植五个样式名与表头，
   转成 MarketMotionStudio 的单行 `<data><value>` 格式，插在 `</root>` 之前。

幂等：已含 `RaceStyleCombo`（页面）或 `RaceStyleBar`（resw）的文件直接跳过。
resw 保持 LF + BOM；页面文件原换行符原样保留。
"""

from __future__ import annotations

import re
from pathlib import Path

MARKET = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio")
NBA = Path(r"D:\software\NbaMotionStudio\src\NbaMotionStudio")

PAGES = [
    "AhPremiumPage", "AssetRacePage", "BondRacePage", "ExtremeDaysPage",
    "CryptoComparePage", "CryptoMarketCapPage", "CryptoMoversPage",
    "CryptoDominancePage", "MarketCapPage", "SectorRacePage", "IndexRacePage",
    "HoldOddsPage",
]

LANGS = [
    "cs", "de", "en-US", "es", "fr", "it", "ja", "ko", "pl", "pt-BR", "ru",
    "tr", "zh-Hans", "zh-Hant",
]

# Nba 键名后缀 -> Market 键名。
STYLE_KEYS = {
    "": "RaceStyleHeader",
    "Bar": "RaceStyleBar",
    "Podium": "RaceStylePodium",
    "Skyline": "RaceStyleSkyline",
    "Pyramid": "RaceStylePyramid",
    "FocusTour": "RaceStyleFocusTour",
}


def edit_page(name: str) -> list[str]:
    """改一个页面的 XAML 与 code-behind，返回人类可读的变更说明。"""
    notes: list[str] = []

    xaml_path = MARKET / "Pages" / f"{name}.xaml"
    xaml = xaml_path.read_text(encoding="utf-8-sig")

    if "RaceStyleCombo" in xaml:
        notes.append(f"{name}.xaml: 已有，跳过")
    else:
        anchor = '        <views:VideoSettingsPanel x:Name="VideoSettings" />'
        if anchor not in xaml:
            raise SystemExit(f"{name}.xaml: 找不到 VideoSettingsPanel 锚点")

        line = next(l for l in xaml.splitlines() if "<views:VideoSettingsPanel" in l)
        indent = line[: len(line) - len(line.lstrip())]
        combo = f'{indent}<views:RaceStyleCombo x:Name="RaceStyleCombo" />\n'
        xaml = xaml.replace(line, combo + line, 1)
        xaml_path.write_text(xaml, encoding="utf-8-sig", newline="")
        notes.append(f"{name}.xaml: 插入 RaceStyleCombo")

    cs_path = MARKET / "Pages" / f"{name}.xaml.cs"
    cs = cs_path.read_text(encoding="utf-8-sig")

    if "RaceStyleCombo" in cs:
        notes.append(f"{name}.xaml.cs: 已有，跳过")
        return notes

    lines = cs.splitlines(keepends=True)

    # 1) Bind + Chosen 订阅，插在 VideoSettings.Restore(_prefs); 之后。
    restore_at = next(i for i, l in enumerate(lines) if "VideoSettings.Restore(_prefs);" in l)
    indent = lines[restore_at][: len(lines[restore_at]) - len(lines[restore_at].lstrip())]
    bind = (
        f"{indent}RaceStyleCombo.Bind(_prefs);\n"
        f"{indent}RaceStyleCombo.Chosen += (_, _) => ApplyPreviewSettings();\n"
    )
    lines.insert(restore_at + 1, bind)
    notes.append(f"{name}.xaml.cs: Bind + Chosen（第 {restore_at + 1} 行后）")

    # 2) 初始化器里插 Style = ...。先定位 new SectorRaceRenderer(，再找它之后
    #    第一个整行为 `{` 的行。
    ctor_at = next(i for i, l in enumerate(lines) if "new SectorRaceRenderer(" in l)
    brace_at = next(i for i in range(ctor_at, min(ctor_at + 12, len(lines)))
                    if lines[i].strip() == "{")
    prop_at = brace_at + 1
    prop_indent = lines[prop_at][: len(lines[prop_at]) - len(lines[prop_at].lstrip())]
    lines.insert(prop_at, f"{prop_indent}Style = RaceStyleCombo.ChosenStyle,\n")
    notes.append(f"{name}.xaml.cs: Style 属性（初始化器第 {prop_at + 1} 行）")

    cs_path.write_text("".join(lines), encoding="utf-8-sig", newline="")
    return notes


def port_resw(lang: str) -> list[str]:
    """把 Nba 的样式文案移植进 Market 的 resw，返回变更说明。"""
    nba_text = (NBA / "Strings" / lang / "Resources.resw").read_text(encoding="utf-8-sig")

    # Nba 的条目是多行 + xml:space="preserve"；捕获原样文本（含转义实体）。
    found = dict(re.findall(
        r'<data name="NbaHistoryStyle(\w*)"[^>]*>\s*<value>(.*?)</value>',
        nba_text, re.DOTALL))

    missing = [k for k in STYLE_KEYS if k not in found]
    if missing:
        raise SystemExit(f"Nba {lang} resw 缺少键：{missing}")

    path = MARKET / "Strings" / lang / "Resources.resw"
    text = path.read_text(encoding="utf-8-sig")

    if "RaceStyleBar" in text:
        return [f"{lang}/resw: 已有，跳过"]

    entries = ["  <!-- 竞速画面样式（移植自 NbaMotionStudio 生涯竞速）。 -->"]
    for suffix, key in STYLE_KEYS.items():
        entries.append(f'  <data name="{key}"><value>{found[suffix]}</value></data>')

    anchor = "</root>"
    if anchor not in text:
        raise SystemExit(f"{lang}/resw: 找不到 </root>")

    text = text.replace(anchor, "\n".join(entries) + "\n" + anchor, 1)
    path.write_text(text, encoding="utf-8-sig", newline="")
    return [f"{lang}/resw: 追加 {len(STYLE_KEYS)} 条"]


def main() -> None:
    for name in PAGES:
        for note in edit_page(name):
            print(note)

    for lang in LANGS:
        for note in port_resw(lang):
            print(note)


if __name__ == "__main__":
    main()
