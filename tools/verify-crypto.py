# -*- coding: utf-8 -*-
"""真机验证「加密货币」这个市场，以及它那三个页面。

要回答的核心问题有五个：

1. **默认市场（A 股）下，那三项不在导航里。** 加密页不是并列的第二套页面，是一个市场里才
   有的页面 —— 所以「看得到」与「看不到」都要验，而默认那一眼正是绝大多数用户看到的样子。
2. **市场下拉里有「加密货币」这一格**，而且它只在能取到币价的地方出现。本机开着 VPN，
   所以它应该**在**；这一条验的是「下拉接到了可达性上」，不是「隐藏逻辑生效了」。
3. **选中它之后，导航里只剩三页。** 股票各页全部移除 —— 它们读的是股票接口，一个币也不报，
   留着就是一次一次的失败。这一条必须真机切一次市场，因为「菜单裁成什么样」只在启动读
   市场设置时才发生。
4. **三页真的取到了币价，而且报出来的天数是自然日。** 加密页的状态行说的是**自然日**，
   股票页说的是**交易日** —— 这两批 resw 键分开写就是为了这个，所以判据认「天（」而不是
   「个交易日」。认错了字，这轮最重要的一条约束就白写了。
5. **源码里的五处守卫真的在**（见最后一节）。

**跑完必须把市场改回 A 股**，所以整段包在 `try/finally` 里，而恢复那一步自己再验一次
（改回之后三项应该又不在导航里）。中途被打断也不会留下一台「市场是加密货币」的机器。

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

# 切到加密市场、取完数那一眼的实拍。
CRYPTO_SHOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "artifacts", "crypto-market.png")

# 检索框里敲了两个字之后的那一眼：一行十二个只剩一个。
CRYPTO_FILTER_SHOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "artifacts", "crypto-search.png")

# 1 分钟那一档取完数的那一眼：横轴是钟点，右边区间下拉换成了日期框。
CRYPTO_MINUTE_SHOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "artifacts", "crypto-minute.png")

EXE = "MarketMotionStudio.exe"

CRYPTO_IDS = ["NavCryptoCandle", "NavCryptoDca", "NavCryptoPosition"]

# A few stock pages, one from each part of the menu. If the market were crypto and
# these were still listed, the menu would be offering pages that cannot fetch a single
# price — which is the whole reason the branch in `ApplyMarket` exists.
STOCK_IDS = ["NavMarketTurnover", "NavCandle", "NavSectorRace", "NavDcaPlan", "NavPosition"]

# 状态行里那三种说法。注意都是「天」，不是股票页的「个交易日」。
CANDLE = re.compile(r"(\d[\d,]*)\s*根")
DAYS = re.compile(r"(\d[\d,]*)\s*天（")
BUYS = re.compile(r"买入\s*(\d[\d,]*)\s*次")
# 终态要么是「说出了数字与日期」，要么是「说出了为什么不行」。
#
# 日期那个「至」必须连着年月日才算：状态行里「请至少勾选一个币种」也带一个「至」字，
# 只认单字会把一句拒绝读成一次成功 —— 这正是「断言失败先怀疑断言本身」那一类。
DONE = re.compile(r"至\s*\d{4}-\d{2}-\d{2}")

# 分钟档那句写的是一天而不是一段（「1 分钟 K 线 1440 根（2026-10-11）」），里面没有「至」，
# 所以 `DONE` 匹配不上 —— 不换判据的话，三档各要空等满 180 秒才返回。
MINUTE_DONE = re.compile(r"[（(]\s*\d{4}-\d{2}-\d{2}\s*[)）]")
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


def fetch(win, seconds=180, done=None):
    """点取数，等状态行说完了。

    `done` 是「说完了」的判据，默认是 `DONE`（日档那句「… 至 2026-10-11」）。分钟档那句
    写的是一天，没有「至」，所以要换 —— 见 `MINUTE_DONE`。
    """
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton", limit=12)

    if button is None:
        return None

    winui.invoke_click(button, settle=1.0)

    pattern = done or DONE
    deadline = time.time() + seconds
    last = None

    while time.time() < deadline:
        text = status_text(win)

        if text and text != last:
            last = text

            if pattern.search(text) or FAILED.search(text):
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


def open_settings(win):
    """从导航进设置页。市场卡是页面第一张，所以读到 `MarketCombo` 就到地方了。"""
    return open_page(win, "NavSettingsItem", "MarketCombo")


def labels_of(win, seconds=0):
    """市场下拉里现在有哪几格。用它而不是读选中项 —— 选中项读不回来，见 `winui.combo_pick`。

    **要等，而不是读一次。** 第四格是探测回来之后才补上的（`SettingsPage.OfferCryptoMarketAsync`），
    而设置页往往比那次请求先打开：探测对每个源最多问两次、每次一条二十秒的绳子。跨境
    的第一个请求要先付 DNS、握手与 TLS 的钱（实测十四秒），绳子短了就把能取到币价的机器
    判成取不到 —— 只读一次的写法**实测过**，答案是「三格」，而真相有两个：还在问，或者真
    的取不到。两者长得一模一样。
    所以这里按「四格」等，等到为止。

    `combo_labels` 在手忙脚乱的时候会返回空（上一次收起还在动画时展开是无效的），空答案不覆盖
    已经看到的最长那份。
    """
    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)

    if combo is None:
        return []

    deadline = time.time() + seconds
    best = []

    while True:
        labels = winui.combo_labels(win, combo)

        if labels and len(labels) > len(best):
            best = labels

        if len(best) >= 4 or time.time() >= deadline:
            return best

        time.sleep(1.5)


def restart():
    """关掉再起来。市场是启动时读的，所以改完之后必须真的重启一次。"""
    return winui.launch(EXE)


def reset_market():
    """开场先把市场摆回第一格，再重启一次。

    **起点不假设**：上一趟可能崩在半路 —— 恢复那一步一旦出错，机器就停在「加密货币」
    上退出了。下一趟读到的于是是一台被上一趟改过的机器，而「默认市场下三项不在导航
    里」这条断言会失败，报的却是应用坏了。

    只用等三格：这一趟要的只是「第一格存在」，第四格是探测回来才补的，等它白等二十几秒。
    """
    win = winui.launch(EXE)

    if not open_settings(win):
        return win

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)

    if combo is None:
        return win

    labels = labels_of(win, seconds=6)

    if labels:
        winui.combo_pick(win, combo, labels[0])
        win = restart()

    return win


def main():
    # 不是 `winui.launch`：市场是持久的，不先摆回来就等于假设上一趟收得干净。
    win = reset_market()
    assert win is not None, "窗口未找到"

    switched = False

    try:
        # ---- 1. 默认市场 -----------------------------------------------------------
        print("[默认市场 A 股]")

        for i in CRYPTO_IDS:
            check("导航里没有 %s" % i, nav_item(win, i) is None)

        # ---- 2. 市场下拉 -----------------------------------------------------------
        print("\n[设置页的市场下拉]")

        check("打开设置页", open_settings(win))

        print("  等探测……（每源最多问两次，每次二十秒）")
        # 九十秒，不是四十：最坏是两源各问两次、每次一条二十秒的绳子，四十秒会在
        # 「Yahoo 两次都超时、CoinGecko 还没轮到」的那一刻读到一个三格的下拉，然后
        # 报「源不可达」—— 而真相是还没问完。
        labels = labels_of(win, seconds=90)
        print("  下拉里：", "、".join(labels) if labels else "(没读到)")

        check("下拉列出四格（三个股票市场 + 加密货币）", len(labels) == 4, "%d 格" % len(labels))

        if len(labels) != 4:
            print("\n源不可达：这一格本就不该出现，后面几节无从验起。")
            print("本机开着 VPN 时应该能取到币价（见 CryptoQuotes.ProbeAttempts）。")
            print("FAILED: %d —— %s" % (len(FAILURES), "，".join(FAILURES)))
            sys.exit(2)

        crypto_label = labels[3]

        # ---- 3. 切到加密货币，重启，看菜单 ------------------------------------------
        print("\n[切到「%s」]" % crypto_label)

        combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)
        picked = winui.combo_pick(win, combo, crypto_label) == crypto_label

        check("选中它", picked)

        if not picked:
            print("\n没选上，不做重启（否则后面每一节都在错的市场上跑）。")
            print("FAILED: %d —— %s" % (len(FAILURES), "，".join(FAILURES)))
            sys.exit(2)

        switched = True
        win = restart()

        for i in CRYPTO_IDS:
            item = nav_item(win, i)
            check("导航里有 %s" % i, item is not None, item.Name if item is not None else "")

        for i in STOCK_IDS:
            check("导航里没有 %s" % i, nav_item(win, i) is None)

        # ---- 4. 加密 K 线 ----------------------------------------------------------
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
        check("根数在 1~4000 之间",
              bars is not None and 0 < int(bars.group(1).replace(",", "")) <= 4000,
              bars.group(1) if bars else "")
        check("状态行说的是「天」而不是「交易日」", bool(text) and "交易日" not in text)

        # 一眼看得见的证据：左边只剩那三项，而画面是一枚币的 K 线。断言说的是「对不对」，
        # 这张图说的是「看起来是不是这么回事」—— 两条都留着，改坏了才知道坏在哪。
        winui.shot(win, CRYPTO_SHOT)

        # ---- 4.5 检索框 ------------------------------------------------------------
        #
        # 按**当前界面语言的名字**匹配，也认代码。三页共用同一口框（`CryptoPicker`），
        # 所以这里验一次就够 —— 验的是控件，不是三份接线。
        # 和币种开关一个深度（14）。写浅了找不到：这一块在右侧滚动区里，比导航深得多。
        box = winui.find(win, lambda c: c.AutomationId == "CryptoSearch", limit=14)
        check("有检索框", box is not None)

        if box is not None:
            def typed(what):
                box.GetPattern(auto.PatternId.ValuePattern).SetValue(what)
                time.sleep(1.0)

                return [c.Name for c in winui.find_all(
                    win, lambda c: c.AutomationId and c.AutomationId.startswith("Coin"),
                    limit=14)]

            # 数说个数，不认名字：名字是当前语言拼的，判据不该跟着界面语言改。
            got = typed("比特")
            check("搜「比特」只剩一个币", len(got) == 1, "、".join(got) or "(一个都不剩)")

            # 这张图说的是「看起来是不是这么回事」：一行十二个只剩一个。
            winui.shot(win, CRYPTO_FILTER_SHOT)

            got = typed("btc")
            check("搜代码 btc 也命中同一个", len(got) == 1, "、".join(got) or "(一个都不剩)")

            # 已选中的币不会因为不匹配而消失 —— 它是答案的一部分，藏起来会让下面那行
            # 「已选 N 个」没有对应的东西。所以搜一个不存在的词时，留下的正是它。
            got = typed("zzz")
            check("搜不存在的词只有已选的那一个", len(got) == 1, "、".join(got) or "(一个都不剩)")

            none = winui.find(win, lambda c: c.AutomationId == "CryptoSearchNone", limit=14)
            check("搜不到时说出声", none is not None, none.Name if none else "(没有那句话)")

            got = typed("")
            check("清空后十二个都回来", len(got) == 12, "%d 个" % len(got))

        # ---- 4.6 分钟档 ------------------------------------------------------------
        #
        # 三档问的是「哪一天」而不是一段区间，这是它们和日/周/月唯一的区别，也正是最容易
        # 做错的地方 —— 做错了的症状不是报错，是「取到了数，但取的是另一批」。所以验三件
        # 事：换档之后区间下拉让位给日期框；**同一天里档越细根越多**（1 分钟必然多于 5 分钟，
        # 这条比任何绝对数字都硬 —— 取错日期、三档共用一份数据、退回日线，它都不成立）；
        # 状态行说的是一天，不写一个「至」。
        print("\n[分钟档：问的是一天]")

        period = winui.find(win, lambda c: c.AutomationId == "CryptoPeriodCombo", limit=14)
        check("有周期下拉", period is not None)

        if period is not None:
            offered = winui.combo_labels(win, period)
            print("  周期：", "、".join(offered) if offered else "(没读到)")
            check("周期有六档（日/周/月 + 1/5/15 分钟）", len(offered) == 6, "%d 档" % len(offered))

            counts = {}

            for want in ("1 分钟", "5 分钟", "15 分钟"):
                got = winui.combo_pick(win, period, want)
                check("切到「%s」" % want, got == want, got or "(没选上)")

                if got != want:
                    continue

                # Collapsed 的控件不出现在 UIA 树里，所以「找不到了」正是「它让位了」的
                # 证据 —— 不必再去读可见性，而读可见性也读不出这个。
                check("「%s」下区间下拉不在了" % want,
                      winui.find(win, lambda c: c.AutomationId == "CryptoRangeCombo",
                                 limit=14) is None)

                day = winui.find(win, lambda c: c.AutomationId == "CryptoMinuteDay", limit=14)
                check("「%s」给出日期框" % want, day is not None)

                note = winui.find(win, lambda c: c.AutomationId == "CryptoMinuteNote", limit=14)
                check("「%s」说出能往回选多少天" % want, note is not None and bool(note.Name),
                      note.Name if note is not None else "(没有那句话)")

                text = fetch(win, done=MINUTE_DONE)
                print("  %s -> %s" % (want, text))

                check("「%s」取数成功" % want, bool(text) and not FAILED.search(text or ""))

                bars = CANDLE.search(text or "")
                counts[want] = int(bars.group(1).replace(",", "")) if bars else 0

                check("「%s」说的是一天而不是一段" % want,
                      bool(text) and "至" not in text, text or "")

                # 最细那一档的实拍：横轴该是钟点而不是日期，右边该是日期框而不是区间下拉 ——
                # 这两件事断言都验了，但「看起来是不是这么回事」得看一眼才知道。
                if want == "1 分钟":
                    winui.shot(win, CRYPTO_MINUTE_SHOT)

            check("同一天里档越细根越多",
                  counts.get("1 分钟", 0) > counts.get("5 分钟", 0) > counts.get("15 分钟", 0) > 0,
                  "1m=%d 5m=%d 15m=%d" % (counts.get("1 分钟", 0),
                                           counts.get("5 分钟", 0),
                                           counts.get("15 分钟", 0)))

            # 换回去也要验：只验「换过去」的开关，坏了也看不出来。
            # 那一档在下拉里写的是「日K」—— 与状态行里说的「日K K 线」同一个词，不是「日」。
            # 写「日」的话 combo_pick 匹配不上，切不回去，而报错看起来像换档坏了。
            got = winui.combo_pick(win, period, "日K")
            check("切回日档", got == "日K", got or "(没选上)")
            check("日档下区间下拉回来了",
                  winui.find(win, lambda c: c.AutomationId == "CryptoRangeCombo",
                             limit=14) is not None)

        # ---- 5. 加密定投 -----------------------------------------------------------
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
        check("天数在 1~4000 之间",
              days is not None and 0 < int(days.group(1).replace(",", "")) <= 4000,
              days.group(1) if days else "")

        # ---- 6. 加密持仓 -----------------------------------------------------------
        print("\n[加密货币持仓]")

        check("打开加密持仓页", open_page(win, "NavCryptoPosition", "CapitalBox"))

        check("勾上 BTC", ensure_coin(win, "BTC"))
        print("  选择器:", picks_note(win))

        text = fetch(win)
        print("  状态行:", text)
        check("加密持仓取数成功", bool(text) and not FAILED.search(text or ""))

        days = DAYS.search(text or "")
        check("状态行报出天数", days is not None, days.group(1) if days else text)
        check("天数在 1~4000 之间",
              days is not None and 0 < int(days.group(1).replace(",", "")) <= 4000,
              days.group(1) if days else "")

        # ---- 7. 源码里的守卫 --------------------------------------------------------
        print("\n[源码守卫]")

        window = open(os.path.join(SOURCE, "MainWindow.xaml.cs"), encoding="utf-8-sig").read()
        xaml = open(os.path.join(SOURCE, "MainWindow.xaml"), encoding="utf-8-sig").read()
        markets = open(os.path.join(SOURCE, "Market", "Markets.cs"), encoding="utf-8-sig").read()
        settings = open(os.path.join(SOURCE, "Pages", "SettingsPage.xaml.cs"),
                        encoding="utf-8-sig").read()

        check("三项在 XAML 里先 Collapsed，由市场打开",
              len(re.findall(r'x:Name="(NavCrypto\w+)"[^>]*Visibility="Collapsed"', xaml)) == 3)

        check("ApplyMarket 按市场分岔（加密货币那一支）",
              "if (MarketSettings.Current is MarketId.Crypto)" in window)

        check("股票市场下把三项整组移除", "Nav.MenuItems.Remove(page)" in window)

        check("Navigate 按市场挡住带 tag 的直达",
              "&& MarketSettings.Current is not MarketId.Crypto)" in window)

        check("下拉按可达性列出一格",
              "Markets.Offered(cryptoReachable || MarketSettings.Current is MarketId.Crypto)"
              in settings)

        # 「不给加密市场一份假的股票档案」的守卫：`Of` 是按枚举下标取数组的，少了这一份
        # profile 就是越界异常；而五张股票清单是**空的**，不是抄一份币种清单进来 ——
        # 抄一份就是「哪些币是这个应用知道的」有了第二个答案，而它会各自过期。
        check("Markets 里有一份加密档案，且股票清单是空的",
              "MarketId.Crypto," in markets and "Rosters: []," in markets)

    finally:
        if switched:
            print("\n[恢复默认市场]")

            win = restart()
            open_settings(win)

            labels = labels_of(win)
            combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)

            if combo is not None and labels:
                winui.combo_pick(win, combo, labels[0])
                win = restart()

                back = nav_item(win, "NavCryptoCandle") is None
                check("改回「%s」后三项又不在导航里" % labels[0], back)

                if not back:
                    print("  ！！市场可能没改回去，请到设置页把「市场」手动改回「%s」。" % labels[0])
            else:
                print("  ！！读不到市场下拉，请到设置页把「市场」手动改回 A 股。")

    print()

    if FAILURES:
        print("FAILED: %d —— %s" % (len(FAILURES), "，".join(FAILURES)))
        sys.exit(2)

    print("FAILED: 0")


if __name__ == "__main__":
    main()
