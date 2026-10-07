# -*- coding: utf-8 -*-
"""把导航栏里每个页面的字形换成 Themes/Icons.xaml 里的自绘图标。

为什么不是手改 XAML
------------------
每一处都在一个 `NavigationViewItem` 里，替换的是一行的中间一段。手改这么多遍
既要求每一遍都认出正确的那个（字形 `E9E9` 出现两次、`E9D2` 两次、`E9D9` 两次——
正是这次要修的东西），又会在下一次重跑时重复劳动。脚本按**项名**锚定，字形重号
也就无所谓了：`NavCandle` 只有一个。

幂等：已经是 `PathIcon` 的项原样跳过；`App.xaml` 里已经合并过这本字典就不再插。

用法
----
    python tools/port-nav-icons.py
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAIN = REPO / "src/MarketMotionStudio/MainWindow.xaml"
APP = REPO / "src/MarketMotionStudio/App.xaml"
DICT = "ms-appx:///Themes/Icons.xaml"

# 项名 → 几何资源的键。键与 tools/make-icons.py 里的 ICONS 一一对应，
# 也一一对应导航顺序。
ITEMS = [
    ("NavMarketTurnover", "Turnover"),
    ("NavCandle", "Candle"),
    ("NavStockVolume", "Volume"),
    ("NavSectorRace", "SectorRace"),
    ("NavMarketCap", "MarketCap"),
    ("NavCapHistory", "CapHistory"),
    ("NavAhPremium", "AhPremium"),
    ("NavExtremeDays", "ExtremeDays"),
    ("NavFxCorridor", "FxCorridor"),
    ("NavIndexRace", "IndexRace"),
    ("NavAssetRace", "AssetRace"),
    ("NavBondRace", "BondRace"),
    ("NavDrawdown", "Drawdown"),
    ("NavHoldOdds", "HoldOdds"),
    ("NavMatrix", "Matrix"),
    ("NavGainCalendar", "GainCalendar"),
    ("NavDcaPlan", "DcaPlan"),
    ("NavPosition", "Position"),
]

ANCHOR = (
    r'(<mux:NavigationViewItem x:Name="{name}"[^>]*>\s*'
    r'<mux:NavigationViewItem\.Icon>)(.*?)(</mux:NavigationViewItem\.Icon>)')


def anchor_for(name):
    # `{name}` 得真的填进去：模板里留着占位符，正则就去找一个叫 `{name}` 的属性，
    # 于是每一项一项都认不出（第一版就是这么错的）。
    return re.compile(ANCHOR.format(name=re.escape(name)), re.S)


def fix_main():
    text = MAIN.read_text(encoding="utf-8")
    before = text
    changed = []

    for name, key in ITEMS:
        hit = anchor_for(name).search(text)

        if hit is None:
            if f'x:Name="{name}"' in text:
                print(f"✗ {name}：认不出它的图标那一段")
                return None

            print(f"✗ {name}：MainWindow.xaml 里没有这一项")
            return None

        icon = f'<PathIcon Data="{{StaticResource Icon{key}}}" />'

        if hit.group(2).strip() == icon:
            continue

        text = text[:hit.start(2)] + icon + text[hit.end(2):]
        changed.append(name)

    if not changed:
        print("· MainWindow.xaml 已经是自绘图标")
    else:
        MAIN.write_text(text, encoding="utf-8")
        print(f"· MainWindow.xaml：换了 {len(changed)} 项 —— {'、'.join(changed)}")

    # 字形一个都不该剩在菜单里（页脚那两个不在 ITEMS 里，也保留系统字形）。
    leftover = re.findall(r'<mux:NavigationViewItem\.Icon><FontIcon Glyph="&#x([0-9A-Fa-f]+);" /></mux:NavigationViewItem\.Icon>',
                          text)

    if changed and len(leftover) not in (0, 2):
        print(f"✗ 菜单里还剩 {len(leftover)} 处字形，预期只剩页脚两处")

    assert before != text or not changed

    return True


def fix_app():
    text = APP.read_text(encoding="utf-8")

    if DICT in text:
        print("· App.xaml 已经合并过 Icons.xaml")
        return True

    # 插在 XamlControlsResources 之后、那本"背景图要避开的表面"之前：那种用
    # ResourceDictionary.ThemeDictionaries 覆盖 Fluent 键的字典必须排在自绘字典
    # 之后（合并字典是后插的先查），顺序反了主题刷子会被这里的东西盖掉。
    anchor = '                <ResourceDictionary Source="' + DICT + '" />\n'
    target = "                <XamlControlsResources xmlns=\"using:Microsoft.UI.Xaml.Controls\" />\n"

    if target not in text:
        print("✗ App.xaml 里找不到 XamlControlsResources 那一行")
        return False

    text = text.replace(target, target + "\n" + anchor, 1)
    APP.write_text(text, encoding="utf-8")
    print("· App.xaml：合并了 Themes/Icons.xaml")

    return True


def main():
    return 0 if (fix_main() and fix_app()) else 1


if __name__ == "__main__":
    sys.exit(main())
