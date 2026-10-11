# -*- coding: utf-8 -*-
"""真机验证「加密货币」三个页面：导航显隐、取数、以及那个「天」字。

要回答的核心问题有四个：

1. **导航里到底有没有那三项。** 三项只在某个源应答之后才在菜单里，所以「看得到」本身就是
   一条判据：它把「探测能通」「探测的结果接到了菜单上」这两件事一起验了。
2. **取数真的拿到了币价，而且报出来的天数是对的。** 加密页的状态行说的是**自然日**，股票页
   说的是**交易日** —— 这两批 resw 键分开写就是为了这个，所以判据认「天（」而不是
   「个交易日」。认错了字，这轮最重要的一条约束就白写了。
3. **币种名是本地化的，不是源端那个英文名。** `INSTBTC` 这套键如果没接上，界面上会写
   "Bitcoin" 而不是「比特币」，而它看起来完全正常。
4. **源码里那两处守卫真的在**：导航项在 XAML 里是 Collapsed（未决定前不可点），`Navigate`
   里有一句按 `Crypto.Answered` 挡住带 tag 的直达。第 1 条只能证明「可达时在」，证明不了
   「不可达时不在」——那条路本机走不通（要关掉 VPN），所以退而验守卫本身。

用法：python tools/verify-crypto.py
"""
import os
import re
import sys
import time

import uiautomation as auto

import winui

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src", "MarketMotionStudio")

# 状态行里那三种说法。注意都是「天」，不是股票页的「个交易日」。
CANDLE = re.compile(r"(\d[\d,]*)\s*根")
DAYS = re.compile(r"(\d[\d,]*)\s*天（")
BUYS = re.compile(r"买入\s*(\d[\d,]*)\s*次")
# 终态要么是「说出了数字与日期」，要么是「说出了为什么不行」。
#
# 日期那个「至」必须连着年月日才算：状态行里「请至少勾选一个币种」也带一个「至」字，
# 只认单字会把一句拒绝读成一次成功 —— 这正是「断言失败先怀疑断言本身」那一类。
DONE = re.compile(r"至\s*\d{4}-\d{2}-\d{2}")
FAILED = re.compile(r"失败|无法|错误|没有|出错|请至少|请勾")

PRIVATE = re.compile(r"[\ue000-\uf8ff]")

FAILURES = []


def check(label, ok, detail=""):
    print("  %s %s%s" % ("PASS" if ok else "FAIL", label, (" -> " + detail) if detail else ""))

    if not ok:
        FAILURES.append(label)

    return ok


def nav_item(win, automation_id):
    return winui.find(win, lambda c: c.AutomationId == automation_id, limit=10)


def open_page(win, automation_id, marker, seconds=20):
    """点导航项，等到页面上出现只属于它的那个控件。"""
    item = nav_item(win, automation_id)

    if item is None:
        return False

    winui.invoke_click(item, settle=1.2)

    deadline = time.time() + seconds

    while time.time() < deadline:
        if winui.find(win, lambda c: c.AutomationId == marker, limit=12) is not None:
            return True

        winui.invoke_click(item, settle=0.8)
        time.sleep(0.5)

    return False


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status", limit=12)

    if bar is None:
        return None

    texts = [t.Name for t in winui.find_all(bar, lambda c: c.ControlTypeName == "TextControl", limit=8)
             if t.Name and not PRIVATE.search(t.Name)]

    return max(texts, key=len) if texts else None


def fetch(win, seconds=180):
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton", limit=12)

    if button is None:
        return None

    winui.invoke_click(button, settle=1.0)

    deadline = time.time() + seconds
    last = None

    while time.time() < deadline:
        text = status_text(win)

        if text and text != last:
            last = text

            if DONE.search(text) or FAILED.search(text):
                return text

        time.sleep(1.0)

    return last


def chip_names(win):
    chips = winui.find_all(
        win, lambda c: c.AutomationId and c.AutomationId.startswith("Coin"), limit=14)

    return [c.Name for c in chips]


def toggle_state(chip):
    """开关现在是开还是关 —— 问节点，不问像素。"""
    try:
        pattern = chip.GetPattern(auto.PatternId.TogglePattern)

        if pattern is not None:
            return pattern.ToggleState
    except Exception:  # noqa: BLE001 - 控件在读取时消失
        return None

    return None


def ensure_coin(win, code, seconds=8):
    """把某个币种勾上。

    **为什么先看开关状态**：三页都把「上次选的」存了下来，没存过时默认给第一个币种 ——
    也就是说**打开页面时 BTC 往往已经是勾上的**。不看状态直接点，就是把它点掉，然后取数
    报「请至少勾选一个币种」。这个错看起来像取数坏了，实际是判据自己把开关关了。
    """
    chip = winui.find(win, lambda c: c.AutomationId == "Coin" + code, limit=14)

    if chip is None:
        return False

    deadline = time.time() + seconds

    while time.time() < deadline:
        state = toggle_state(chip)

        if state == auto.ToggleState.On:
            return True

        winui.invoke_click(chip, settle=0.6)
        time.sleep(0.4)

    return toggle_state(chip) == auto.ToggleState.On


def picks_note(win):
    """选择器下面那一行：已选几个、最多几个。"""
    note = winui.find(win, lambda c: c.AutomationId == "Note", limit=14)

    return note.Name if note is not None else None


def main():
    win = winui.launch("MarketMotionStudio.exe")
    assert win is not None, "窗口未找到"

    # ---- 1. 导航里有没有那三项 -------------------------------------------------
    print("[导航]")

    # 探测是启动时异步发的，最多 6 秒的绳子；等它答完再看菜单。
    deadline = time.time() + 30
    ids = ["NavCryptoCandle", "NavCryptoDca", "NavCryptoPosition"]
    found = {}

    while time.time() < deadline:
        found = {i: nav_item(win, i) for i in ids if nav_item(win, i) is not None}

        if len(found) == len(ids):
            break

        time.sleep(1.0)

    for i in ids:
        item = found.get(i)
        check("导航里有 %s" % i, item is not None,
              (item.Name if item is not None else "源不可达，整组不进菜单"))

    if len(found) != len(ids):
        print("\n源没应答：三项不在菜单里（本机若开着 VPN 应可达）。")
        print("FAIL:", ", ".join(FAILURES))
        sys.exit(2)

    # ---- 2. 加密 K 线 ----------------------------------------------------------
    print("\n[加密货币 K 线]")

    check("打开加密 K 线页", open_page(win, "NavCryptoCandle", "CoinBTC"))

    names = chip_names(win)
    check("十二个币种都在", len(names) == 12, "%d 个" % len(names))

    # 名字是本地化的，不是源端那个英文名 —— 这是 INST 键接上了没有的唯一证据。
    check("币种名是当地语言的写法", "比特币" in names,
          "、".join(names[:4]) if names else "(没找到币种开关)")

    check("勾上 BTC", ensure_coin(win, "BTC"))
    print("  选择器:", picks_note(win))

    text = fetch(win)
    print("  状态行:", text)
    check("加密 K 线取数成功", bool(text) and not FAILED.search(text or ""))

    bars = CANDLE.search(text or "")
    check("状态行报出根数", bars is not None, bars.group(1) if bars else text)
    check("根数在 1~4000 之间", bars is not None and 0 < int(bars.group(1).replace(",", "")) <= 4000,
          bars.group(1) if bars else "")
    check("状态行说的是「天」而不是「交易日」", bool(text) and "交易日" not in text)

    # ---- 3. 加密定投 -----------------------------------------------------------
    print("\n[加密货币定投]")

    check("打开加密定投页", open_page(win, "NavCryptoDca", "AmountBox"))

    check("勾上 BTC", ensure_coin(win, "BTC"))
    print("  选择器:", picks_note(win))

    text = fetch(win)
    print("  状态行:", text)
    check("加密定投取数成功", bool(text) and not FAILED.search(text or ""))

    days = DAYS.search(text or "")
    buys = BUYS.search(text or "")
    check("状态行报出天数", days is not None, days.group(1) if days else text)
    check("状态行报出买入次数", buys is not None, buys.group(1) if buys else text)
    check("天数在 1~4000 之间", days is not None and 0 < int(days.group(1).replace(",", "")) <= 4000,
          days.group(1) if days else "")

    # ---- 4. 加密持仓 -----------------------------------------------------------
    print("\n[加密货币持仓]")

    check("打开加密持仓页", open_page(win, "NavCryptoPosition", "CapitalBox"))

    check("勾上 BTC", ensure_coin(win, "BTC"))
    print("  选择器:", picks_note(win))

    text = fetch(win)
    print("  状态行:", text)
    check("加密持仓取数成功", bool(text) and not FAILED.search(text or ""))

    days = DAYS.search(text or "")
    check("状态行报出天数", days is not None, days.group(1) if days else text)
    check("天数在 1~4000 之间", days is not None and 0 < int(days.group(1).replace(",", "")) <= 4000,
          days.group(1) if days else "")

    # ---- 5. 源码里的两处守卫 ---------------------------------------------------
    print("\n[源码守卫]")

    xaml = open(os.path.join(SOURCE, "MainWindow.xaml"), encoding="utf-8-sig").read()
    code = open(os.path.join(SOURCE, "MainWindow.xaml.cs"), encoding="utf-8-sig").read()

    collapsed = re.findall(r'x:Name="(NavCrypto\w+)"[^>]*Visibility="Collapsed"', xaml)
    check("三项在 XAML 里先 Collapsed", len(collapsed) == 3, "、".join(collapsed))

    guarded = "CryptoPositionPage)) && !_services.Crypto.Answered" in code
    check("Navigate 按 Crypto.Answered 挡住直达", guarded)

    removed = "Nav.MenuItems.Remove(page)" in code
    check("探测不到时整组移除而不是隐藏", removed)

    print()

    if FAILURES:
        print("FAILED: %d —— %s" % (len(FAILURES), "，".join(FAILURES)))
        sys.exit(2)

    print("FAILED: 0")


if __name__ == "__main__":
    main()
