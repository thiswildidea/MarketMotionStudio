# -*- coding: utf-8 -*-
"""真机验证导航栏的自绘图标（Tools/make-icons.py 的产物）。

这一套图标替换掉的是原本三对**同形**的字形（K线与板块竞速、成交量换手率与持有
胜率、成交额与持仓收益），所以这个脚本要盯的也正是"重号"这件事，而不是"好不好看"
——审美归预览图，机器能验的是形状与不变量。

四类断言，前三类是源码级的：

1. **导航里每一项都换成了 PathIcon**，而且每一项挂的是**它自己的那幅图**（项名 → 键的
   对应关系写死在脚本里，与 port-nav-icons.py 同表）。数量从那张表推，不写死：
   加一页就该让这张表多一行，而不是让四处「十六」变红。
2. **没有两条路径是完全一样的。** 这是这次改动的全部理由，也是最容易被一次
   复制粘贴毁掉的东西。
3. **每幅图的包围盒都是 [2,18]²。** PathIcon 用等比缩放填满图标格，量的是包围盒：
   一幅忘了带定位点的图会与邻座不一样大，而"大小不一样"在截图里几乎看不出来
   ——两边都"有个图标"。这里是唯一抓得住它的地方。
4. **真机上应用起得来、导航里一项不少、还能一项一项点过去。** 这条不是走过场：
   `PathGeometry` 当资源用（`Data="{StaticResource ...}"`）在 WinUI 里是能用但
   少见的写法，写错就是启动即崩 —— 而崩在启动时，正是源码级断言看不见的那种坏。

用法：python tools/verify-nav-icons.py
产物：artifacts/icons/nav-real.png（真机上那一条导航，供人眼复核）
"""
import os
import re
import sys
import time
from pathlib import Path

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = Path(__file__).resolve().parent.parent
MAIN = REPO / "src/MarketMotionStudio/MainWindow.xaml"
APP = REPO / "src/MarketMotionStudio/App.xaml"
ICONS = REPO / "src/MarketMotionStudio/Themes/Icons.xaml"
OUT = REPO / "artifacts/icons"

# 与 tools/port-nav-icons.py 同一张表：项名 → 几何键。
ITEMS = [
    ("NavMarketTurnover", "Turnover", "市场成交额"),
    ("NavCandle", "Candle", "K线"),
    ("NavStockVolume", "Volume", "成交量换手率"),
    ("NavSectorRace", "SectorRace", "行业板块竞速"),
    ("NavMarketCap", "MarketCap", "市值榜"),
    ("NavCapHistory", "CapHistory", "市值历程"),
    ("NavAhPremium", "AhPremium", "AH 溢价"),
    ("NavExtremeDays", "ExtremeDays", "极端交易日"),
    ("NavFxCorridor", "FxCorridor", "汇率走廊"),
    ("NavIndexRace", "IndexRace", "指数长跑"),
    ("NavAssetRace", "AssetRace", "大类资产"),
    ("NavBondRace", "BondRace", "债市固收"),
    ("NavDrawdown", "Drawdown", "回撤与修复"),
    ("NavHoldOdds", "HoldOdds", "持有胜率"),
    ("NavMatrix", "Matrix", "收益矩阵"),
    ("NavGainCalendar", "GainCalendar", "涨跌日历"),
    ("NavDcaPlan", "DcaPlan", "定投计划"),
    ("NavPosition", "Position", "持仓收益"),
]

BOX0, BOX1 = 2.0, 18.0
SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки"]

CHECKS = []


def check(name, ok, note=""):
    CHECKS.append((name, ok, note))
    print(f"{'✓' if ok else '✗'} {name}" + (f" — {note}" if note else ""))


def report():
    bad = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} 通过")

    for name, _, note in bad:
        print(f"  ✗ {name} — {note}")

    return 1 if bad else 0


# ------------------------------------------------------------ 第 1 类：换没换

def resource_geometries():
    """Icons.xaml 里每条几何的路径数据，按 key。

    存的是 `<x:String>`，不是 `<PathGeometry Figures="...">`：WinUI 的 XAML 编译器
    不接受把小语言写在 `Figures` 上（WMC0055），尽管写在 `PathIcon.Data` 上合法。
    所以这里读的是字符串元素的正文。
    """
    text = ICONS.read_text(encoding="utf-8")
    found = {}

    for hit in re.finditer(r'<x:String x:Key="(Icon\w+)"[^>]*>([^<]+)</x:String>', text):
        found[hit.group(1)] = re.sub(r"\s+", "", hit.group(2))

    return found


def contours(figures):
    """路径数据拆成一条条轮廓，每条是 [(x, y), ...]。只用 M/L/Z，所以好拆。"""
    out = []

    for piece in re.findall(r"M([^M]+)", figures):
        pts = []

        for pair in re.findall(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", piece):
            pts.append((float(pair[0]), float(pair[1])))

        if len(pts) >= 3:
            out.append(pts)

    return out


def source_checks():
    main = MAIN.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    geoms = resource_geometries()

    check("App.xaml 合并了 Icons.xaml", "ms-appx:///Themes/Icons.xaml" in app)

    # 每一项都挂自己的那幅图（数量从 ITEMS 推）
    for name, key, label in ITEMS:
        hit = re.search(
            rf'x:Name="{name}"[^>]*>\s*<mux:NavigationViewItem\.Icon>'
            rf'<PathIcon Data="\{{StaticResource Icon{key}\}}" />',
            main, re.S)

        check(f"{label}用的是自绘的 Icon{key}", hit is not None)

    # 菜单里不该再有字形
    leftover = re.findall(
        r"<mux:NavigationViewItem\.Icon><FontIcon", main)

    check("菜单里的字形一个不剩（页脚两项除外）", len(leftover) <= 2, f"还剩 {len(leftover)} 处")

    if not geoms:
        check("Icons.xaml 里读得到几何", False)
        return

    # 数量从 ITEMS 推：写死「十六」的断言在加了第十七页之后必然变红，而红的理由跟图标
    # 好不好看毫无关系 —— 那种红只会教人把数字往上改一次，然后在下一页再红一次。
    want = len(ITEMS)

    check(f"Icons.xaml 里有 {want} 幅图", len(geoms) == want, f"{len(geoms)} 幅")

    used = {f"Icon{key}" for _, key, _ in ITEMS}
    check(f"{want} 幅图正好被用到 {want} 处",
          used == set(geoms), f"差集 {sorted(used ^ set(geoms))}")

    # 第 2 类：没有两条路径一样 —— 这次改动的全部理由
    seen = {}

    for key in sorted(geoms):
        if geoms[key] in seen:
            check(f"{key} 与 {seen[geoms[key]]} 形状完全相同", False)
            break

        seen[geoms[key]] = key
    else:
        check(f"{want} 幅图两两不同（原来的毛病就是三对同形）", True)

    # 第 3 类：包围盒
    for name, key, label in ITEMS:
        pieces = contours(geoms[f"Icon{key}"])

        if not pieces:
            check(f"{label}的几何读得出轮廓", False)
            continue

        xs = [p[0] for piece in pieces for p in piece]
        ys = [p[1] for piece in pieces for p in piece]
        box = (min(xs), min(ys), max(xs), max(ys))

        check(f"{label}的包围盒是 [2,18]²",
              all(abs(a - b) < 0.02 for a, b in zip(box, (BOX0, BOX0, BOX1, BOX1))),
              f"{box}")

    # 定位点必须是"看得见的形状之外"的东西：一条零面积的轮廓会被渲染器丢掉，
    # 丢了包围盒就变，也就等于没钉住。所以它们得是真有面积的小方。
    #
    # 门槛 0.25 而不是 0.1：路径数据按一位小数落盘，边长 0.12 的定位点在文件里是
    # 0.1，用"严格小于 0.1"去数，数出来是零个 —— 而它明明在那儿。
    for name, key, label in ITEMS:
        pieces = contours(geoms[f"Icon{key}"])
        marks = 0

        for piece in pieces:
            xs = [p[0] for p in piece]
            ys = [p[1] for p in piece]

            if max(xs) - min(xs) <= 0.25 and max(ys) - min(ys) <= 0.25:
                marks += 1

        check(f"{label}带着两个定位点", marks == 2, f"{marks} 个")


# ------------------------------------------------------------ 第 4 类：真机

def open_settings(win):
    for name in SETTINGS_NAMES:
        item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

        if item is None:
            continue

        try:
            item.GetSelectionItemPattern().Select()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(2.0)

        return True

    return False


def force_ashare(win):
    """把市场切成 A 股并重启。

    "市场成交额"只在 A 股出现（港股与美股没有那一页的数据，导航把这一项摘掉），
    所以脚本先看它在不在 —— 这个信号比读设置页那个下拉可靠：下拉要展开、要等
    弹出层、要拿展开前后的差值去认它，而市场是**记住的偏好**，上一次别的脚本
    跑过就可能不是 A 股（这次就是：跑之前是港股，第一次跑只数到 15 项）。
    """
    if not open_settings(win):
        print("· 设置页没找到，市场保持原样")
        return win

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo")
    labels = winui.combo_labels(win, combo) if combo is not None else []

    if not labels:
        print("· 读不出市场下拉的内容，市场保持原样")
        return win

    picked = winui.combo_pick(win, combo, labels[0])
    print(f"· 市场复位到 {picked}（改市场要重启）")
    time.sleep(1.5)

    winui.kill(winui.EXE)
    time.sleep(2.0)

    return winui.launch(winui.EXE)


def nav_rows(win):
    names = [label for _, _, label in ITEMS]
    rows = {}

    for item in winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl", limit=40):
        if item.Name in names and item.Name not in rows:
            rows[item.Name] = item

    return rows


def capture(win, name):
    """截一张窗口图。预览面板与动画都不需要：要看的只有左边那一条导航。"""
    path = OUT / name

    try:
        win.SetTopmost(True)
        time.sleep(0.6)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(str(path))

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    print(f"· 截图 {path.relative_to(REPO)}")
    return path


def theme_labels(win):
    """(三档主题的文字, 当前那一档)，读不到就是 None。"""
    if not open_settings(win):
        return None

    combo = winui.find(win, lambda c: c.AutomationId == "ThemeCombo")

    if combo is None:
        return None

    labels_shown = winui.combo_labels(win, combo)

    if len(labels_shown) < 3:
        return None

    return labels_shown, winui.value(combo)


def set_theme(win, name, tries=3):
    """选某一档主题，返回**读回来**的那一档（读不回来就是 None）。

    读回来才算数：`combo_pick` 只是"把这一项选中了"，而这一页的下拉紧挨着别的一
    起重建过，点完之后值没跟上并不罕见 —— 第一版就是按"点过了"当成功，"改回原样"
    于是报了一个它其实已经改回去的失败。
    """
    for _ in range(tries):
        combo = winui.find(win, lambda c: c.AutomationId == "ThemeCombo")

        if combo is None:
            return None

        winui.combo_pick(win, combo, name)
        time.sleep(1.2)

        combo = winui.find(win, lambda c: c.AutomationId == "ThemeCombo")
        now = winui.value(combo) if combo is not None else None

        if now == name:
            return now

        time.sleep(0.8)

    return None


def live_checks():
    # 起得来本身就是一条断言：几何资源写错的话，XAML 在窗口出现之前就崩了。
    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来（几何资源能被解析）", False, "没有窗口")
        return

    check("应用起得来（几何资源能被解析）", True)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    labels = [label for _, _, label in ITEMS]
    rows = nav_rows(win)

    # 少的那一项如果正是"市场成交额"，那就是市场不对，不是图标不对：那一页只在
    # A 股做，导航把这一项摘掉是正常的。
    if "市场成交额" not in rows and len(rows) == 15:
        win = force_ashare(win)

        if win is None:
            check("复位市场后窗口还在", False)
            return

        try:
            win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(1.5)
        except Exception:  # noqa: BLE001
            pass

        rows = nav_rows(win)

    check(f"导航里 {len(ITEMS)} 项都在", len(rows) == len(ITEMS),
          f"数到 {len(rows)} 项：{' / '.join(rows)}")

    missing = [l for l in labels if l not in rows]
    check("一项都不少", not missing, " / ".join(missing))

    # 逐项点过去：图标坏了不影响这一条，但换成 PathIcon 有可能把项点不动
    # （比如图标节点吃掉了点击），所以还是要走一遍。
    went = []

    for label in labels:
        item = rows.get(label)

        if item is None:
            continue

        try:
            item.GetSelectionItemPattern().Select()
            time.sleep(0.7)
            went.append(label)
        except Exception as ex:  # noqa: BLE001
            print(f"· {label} 点不动：{ex}")

    check(f"{len(ITEMS)} 项都点得动", len(went) == len(ITEMS), f"{len(went)} 项")

    OUT.mkdir(parents=True, exist_ok=True)
    capture(win, "nav-real.png")

    # 深浅两套：PathIcon 用的是 Foreground，所以理论上同一幅几何在两种主题下都
    # 该看得见 —— 但"应该会跟随"与"确实跟随了"是两件事，而深色是最容易漏测的
    # 一边（开发机上大多是浅色）。顺手把主题改回原样，别把设置留给用户。
    themes = theme_labels(win)

    if themes is not None:
        labels_shown, original = themes
        light, dark = labels_shown[1], labels_shown[2]

        if set_theme(win, light) == light:
            capture(win, "nav-real-light.png")
            check("浅色主题下换得过来", True, light)
        else:
            check("浅色主题下换得过来", False, light)

        if set_theme(win, dark) == dark:
            capture(win, "nav-real-dark.png")
            check("深色主题下换得过来", True, dark)
        else:
            check("深色主题下换得过来", False, dark)

        # 改回原样：脚本不该把设置留给下一个人（上一轮市场就是被别的脚本留下的）。
        restored = set_theme(win, original)
        check("主题改回了原样", restored == original, f"现在是 {restored}")


def main():
    print("== 源码 ==")
    source_checks()

    print("\n== 真机 ==")
    live_checks()

    return report()


if __name__ == "__main__":
    sys.exit(main())
