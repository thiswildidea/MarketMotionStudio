# -*- coding: utf-8 -*-
"""真机验证「实时持仓收益」：这一页说自己画的是「我的持仓今天挣了多少」。

它比别的页难验，因为**画布上没有 UIA 节点**：大数字、曲线的每个拐点、四张收尾卡片都只是
像素。所以这一趟分三层，每层判一件不同的事：

  1. **源码**：那些在画面上看不出来的规矩 —— 一天只选一次、摊薄成本、重复导入、汇率只在
     有港股持仓时才取。它们错了画面照样好看。

  2. **状态行 + 自己再算一遍**：页面把「哪天 · 多少个分钟点 · 收益多少」写在状态行上，
     而那句话的每一个数都能**不经过应用**算出来 —— 用与页面同一对端点（`qt.gtimg.cn`
     取昨收，`web.ifzq.gtimg.cn/.../day/query` 取分钟价），按同一套「昨收→现价」的定义。
     三个数全对上，才说明九只的价格、昨收、汇率和那个「一天」都拼对了。
     **今天港股休市**，所以它同时验了「休市的那两只不算进曲线」这条分支。

  3. **像素**：曲线在画面上铺满绘图区的宽度，颜色跟着收益的符号走（红涨绿跌）。这两条
     只能量：`CurrencySign` 那类断言在别的页已经证明过，源码写对而画面没画上是可能的。

  4. **导入成交**：往对话框里粘两笔**同时刻、同价、一买一卖**的成交。这样一来
     书和曲线都应当**一个数都不变**（现金进出相抵、持仓一进一出），而账本里多两条记录 ——
     于是「导入真的改到了持仓」与「改完还是对的」可以分开验：前者看状态行说「已导入 2 笔」，
     后者看前后两次取数的收益差在 0.02 元以内。再导一次同一份，状态行必须说「重复 2 笔」。
     最后把 `portfolio.json` 复原（脚本自己备份/还原），下一次跑还是从同一本书开始。

用法：
  python tools/verify-portfolio.py
"""

import colorsys
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from datetime import datetime

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src/MarketMotionStudio")
ART = os.path.join(REPO, "artifacts")

BOOK = os.path.join(SRC, "Market/Portfolio.cs")
PNL = os.path.join(SRC, "Market/IntradayPnl.cs")
TEXT = os.path.join(SRC, "Market/TradeText.cs")
SCREEN = os.path.join(SRC, "Market/ScreenshotText.cs")
RENDER = os.path.join(SRC, "Render/PortfolioPnlRenderer.cs")
PALETTE = os.path.join(SRC, "Render/Palette.cs")
PAGE = os.path.join(SRC, "Pages/PortfolioIntradayPage.xaml.cs")
XAML = os.path.join(SRC, "Pages/PortfolioIntradayPage.xaml")

# 运行态的位置。`ApplicationData.Current.LocalFolder` 落在 `LocalState\`，**不是**
# `LocalAppData\LocalState\`（后者不存在）。写错的代价不是「判据红」而是下面这条：
# `os.path.exists(STATE)` 恒假 → 不备份、不还原 → 导入测验留下的那一笔成交就留在
# 读者真金白银的账本里，谁也没告诉你。实测：跑完账本多出「sz300036 买入 100 @10」。
STATE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Packages", "8166Yxw.MarketMotionStudio_fzc58jprbah1t",
    "LocalState", "portfolio.json")

# 状态行：`2026-10-19 · 242 个分钟点 · 收益 +¥1,368.00`
FETCHED = re.compile(r"(\d{4}-\d{2}-\d{2})\s*·\s*(\d+)\s*个分钟点\s*·\s*收益\s*([+\-]¥[\d,]+\.\d\d)")
IMPORTED = re.compile(r"已导入\s*(\d+)\s*笔成交（重复\s*(\d+)\s*笔，无对应持仓\s*(\d+)\s*笔）")

# 列表里那一行：`3,000 股 · 成本 ¥6.544`
DETAIL = re.compile(r"^[\d,]+\s*股\s*·\s*成本\s*[¥HK$]")
# 港股那一行的货币符是三个字符（`HK$34.062`）：单字符的字符集只吃得下一个，九行里恰好
# 漏掉的就是那两行港股，而报错只说「7 行 / 9 行」，看不出来漏的是哪一类。
DETAIL_ROW = re.compile(r"^([\d,]+)\s*股\s*·\s*成本\s*(?:HK\$|HKD|¥|￥|\$)?([\d.]+)$")

FAILED = []


def check(name, ok, note=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ((" — " + note) if note else ""))

    if not ok:
        FAILED.append(name)


def report():
    print()

    if FAILED:
        print("%d 项未通过：" % len(FAILED) + "、".join(FAILED))
        return 1

    print("全部通过")
    return 0


# ---- 1) 源码 --------------------------------------------------------------------------

def source_checks():
    print("源码")

    book = open(BOOK, encoding="utf-8").read()
    pnl = open(PNL, encoding="utf-8").read()
    text = open(TEXT, encoding="utf-8").read()
    screen = open(SCREEN, encoding="utf-8").read()
    render = open(RENDER, encoding="utf-8").read()
    palette = open(PALETTE, encoding="utf-8").read()
    page = open(PAGE, encoding="utf-8").read()
    xaml = open(XAML, encoding="utf-8").read()

    check("开盘 09:30、沪深 15:00、港股 16:00 是三个具名常量",
          "OpenMinute = (9 * 60) + 30;" in pnl
          and "MainlandClose = 15 * 60;" in pnl
          and "HongKongClose = 16 * 60;" in pnl)

    # 轴走到几点，由**真正开市的场所**决定。写成「书里有港股走到 16:00」的话，港股休市那天
    # 曲线只画到 15:00，右边五分之一是空的、刻度还写着 16:00。
    check("收盘时刻由真正开市的港股持仓决定，不是由书里有没有港股决定",
          "if (holding.IsHongKong)\n                {\n                    close = HongKongClose;" in pnl
          and "holdings.Any(h => h.IsHongKong) ? HongKongClose" not in pnl)

    check("曲线在成交的那一刻是连续的（现金进出计入，不是把持仓一删）",
          "TradeCash(trades, holding.Code)" in pnl
          and "cash += sign * trade.Shares * trade.Price * rate;" in pnl)

    check("一天只选一次（有今天就用今天，否则用最新的那一天）",
          "if (sessions.Values.Any(s => s.Day == today))" in pnl)

    check("没开市的持仓标成休市、不进曲线",
          "closed.Add(holding.Code);" in pnl and "contribution = 0;" in pnl)

    check("汇率只在书里有港股时才去取（A 股的书不该为它打一次请求）",
          "holdings.Any(h => h.IsHongKong)\n            ? await ReadHkdCnyAsync" in pnl)

    check("摊薄成本：卖出把成交额从剩余成本里扣掉",
          "cost = after > 0 ? ((shares * cost) - (sold * trade.Price)) / after : 0;" in book)

    check("重复导入靠六段指纹（日/时/码/方向/价/量）",
          'Day,\n        Time,\n        Code.ToLowerInvariant(),\n        Side,' in book
          and "if (!known.Add(trade.Fingerprint))" in book)

    check("同一份清单按时间顺序应用（成本是路径相关的）",
          ".ThenBy(t => t.MinuteOfDay)" in book)

    check("截图识别走系统 OCR，不出本机", "Windows.Media.Ocr" in screen
          and "HttpClient" not in screen)

    check("红涨绿跌：负号那一支用 Palette.Fall",
          "var colour = positive ? Palette.Emphasis : Palette.Fall;" in render
          and "public static readonly Color Fall" in palette)

    check("种子是 9 只，其中两只港股", book.count('new("sz') + book.count('new("sh')
          + book.count('new("hk') == 9
          and book.count('new("hk') == 2)

    check("这一页打开就读一次（它画的就是读者的持仓，不该先让人按按钮）",
          "await SilentRefreshAsync(report: false);" in page)

    check("自动刷新只在交易日 09:15~16:10 之间跑",
          "minute >= (9 * 60) + 15 &&" in page and "minute <= (16 * 60) + 10;" in page)

    check("列表是只读的，编辑在对话框里", 'ItemsControl x:Name="Holdings"' in xaml
          and 'IsReadOnly="True"' not in xaml)


# ---- 2) 自己算一遍 --------------------------------------------------------------------

SEED = re.compile(r'new\("([a-z]{2}\d{5,6})",\s*"[^"]*",\s*([\d.]+),\s*([\d.]+)\)')


def seeds():
    """源码里那九只种子的 (代码, 股数, 成本)：页第一次打开时账上有什么。

    **只用来对「种子还在」，不用来算数。** 见 `ledger()`：账会往前长，种子不会。
    """
    found = SEED.findall(open(BOOK, encoding="utf-8").read())
    return [(code, float(shares), float(cost)) for code, shares, cost in found]


def ledger():
    """这一页**真正在画**的那本账，从 App 自己写的那个文件读。

    不读源码里的种子。种子回答的是「第一次打开时账上有什么」，而读者的账会往前长：
    导入过成交、或者在对话框里手改过股数与成本之后，文件里的内容就不再是种子了
    （实测：超图软件已经是 5900 股 @8.387，种子写的是 3000 股 @6.544）。
    从那时起，脚本按种子算、页面按文件画，两边对不上，而且差额孤立地看谁都解释不了
    —— 第一次撞上时是整整 1293 元，看着像算法错了，其实是**算的是两本账**。
    compute 的输入必须和页面的输入是同一份。
    """
    if not os.path.exists(STATE):
        return None

    data = json.loads(open(STATE, encoding="utf-8").read())

    return [(row["Code"], float(row["Shares"]), float(row["Cost"]))
            for row in data.get("Holdings", [])]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(request, timeout=40).read()


def snapshot(codes):
    """`qt.gtimg.cn/q=`：一次问完，第 4 个字段是昨收（这一页的整个基准）。"""
    raw = get("https://qt.gtimg.cn/q=" + ",".join(codes)).decode("gbk", "ignore")
    out = {}

    for record in raw.split(";"):
        if "=" not in record or "~" not in record:
            continue

        fields = record.split("=", 1)[1].strip().strip('"').split("~")

        if len(fields) < 5:
            continue

        code = record.split("=", 1)[0].split("_")[-1].strip()

        try:
            out[code] = {"name": fields[1], "last": float(fields[3]), "prev": float(fields[4])}
        except ValueError:
            continue

    return out


def minutes(code):
    """`day/query`：五天的分钟价，取最新那一天，`{分钟: 价格}`。"""
    raw = get("https://web.ifzq.gtimg.cn/appstock/app/day/query?code=" + code)
    data = json.loads(raw).get("data", {}).get(code, {})
    best = None

    for day in data.get("data", []):
        stamp = day.get("date")

        if not stamp or len(stamp) != 8:
            continue

        prices = {}

        for row in day.get("data", []):
            fields = str(row).split()

            if len(fields) < 2 or len(fields[0]) < 4:
                continue

            try:
                prices[int(fields[0][:2]) * 60 + int(fields[0][2:4])] = float(fields[1])
            except ValueError:
                continue

        if not prices:
            continue

        iso = "%s-%s-%s" % (stamp[:4], stamp[4:6], stamp[6:])

        if best is None or iso > best[0]:
            best = (iso, prices)

    return best


def hkd():
    raw = get("https://qt.gtimg.cn/q=whHKDCNY").decode("gbk", "ignore")
    return float(raw.split("~")[3])


def expected(book=None):
    """按页面的定义把今天算一遍：日期、分钟点数、收益。

    收益 = Σ 持仓 × (末价 − 昨收) × 汇率。没开市的那几只两头都按同一个价计，贡献恒为 0，
    所以不写进来也不影响结果 —— 而这一点正是「休市那两只不算进曲线」那条断言要说的事。

    那一本账由调用方给（`ledger()`），不在这里问文件：主线程在这儿要先备份账本再开 App，
    而 `expected()` 在 App 起来之前就得算好。
    """
    book = book if book is not None else ledger()
    codes = [code for code, _, _ in book]
    shots = snapshot(codes)
    sessions = {code: minutes(code) for code in codes}

    today = datetime.now().strftime("%Y-%m-%d")
    stamps = [s[0] for s in sessions.values() if s]
    day = today if today in stamps else (max(stamps) if stamps else None)

    if day is None:
        return None

    live_hk = any(code.startswith("hk") and sessions[code] and sessions[code][0] == day
                  for code, _, _ in book)

    close = 960 if live_hk else 900
    rate = hkd() if any(code.startswith("hk") for code, _, _ in book) else 1.0

    last = 570
    profit = 0.0
    value = 0.0
    rows = []

    for code, shares, _ in book:
        session = sessions[code]
        shot = shots.get(code, {})
        scale = rate if code.startswith("hk") else 1.0
        live = session is not None and session[0] == day

        # **市值算每一行，收益只算今天开市的行。** 这不是不一致：一只休市的股票仍然值钱，
        # 所以它进市值；但它今天没成交，所以它对「今天挣了多少」的贡献是零（两头同一个价）。
        # 两个都跳过会少报一整块 —— 实测少 37,810 元，而那正是两只港股的全部市值。
        if live:
            mark = session[1][max(session[1])]
        else:
            mark = shot.get("last") or (session[1][max(session[1])] if session else 0)

        value += shares * mark * scale

        if not live:
            continue

        prices = session[1]
        at = min(prices)
        prev = shot.get("prev") or prices[at]
        price = prices[max(prices)]

        rows.append({"code": code, "shares": shares, "prev": prev, "last": price,
                     "delta": shares * (price - prev) * scale})

        profit += shares * (price - prev) * scale
        last = max(last, min(close, max(prices)))

    return {
        "day": day,
        "points": last - 570 + 1,
        "profit": profit,
        "value": value,
        "rows": rows,
        "rate": rate,
        "closed": [code for code, _, _ in book
                   if (s := sessions.get(code)) is None or s[0] != day],
        "shots": shots,
    }


# ---- 3) 像素 --------------------------------------------------------------------------

def rgb(name):
    """Palette 里那个颜色的 RGB，从源码读，不抄一份。

    正则用拼接而不是 `%` 格式化：`%02X` 也是占位符，会在 `%` 那一趟先把 `name` 吃掉，
    报的是「参数不够」—— 一句离真相很远的错。
    """
    source = open(PALETTE, encoding="utf-8").read()
    hit = re.search(name + r" = Rgb\(0x([0-9A-F]{2}), 0x([0-9A-F]{2}), 0x([0-9A-F]{2})\)", source)

    return None if hit is None else tuple(int(hit.group(i), 16) for i in (1, 2, 3))


def hue(rgb_value):
    return colorsys.rgb_to_hsv(*[v / 255 for v in rgb_value])[0] * 360


def near(image, box, target, window=14, saturation=0.30, value=0.12):
    """画面上一段区域里落在某个色相附近的像素。抗锯齿会把颜色冲淡，色相守得住。"""
    from PIL import Image  # noqa: F401  (只要 PIL 能开这张图就够)

    pixels = image.load()
    left, right, top, bottom = box
    want = hue(target)
    found = []

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            r, g, b = pixels[x, y][:3]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

            if s < saturation or v < value:
                continue

            away = min((h * 360 - want) % 360, (want - h * 360) % 360)

            if away <= window:
                found.append((x, y))

    return found


def frame_checks(profit, name="verify-portfolio-frame.png"):
    from PIL import Image

    path = os.path.join(ART, name)
    win = winui.app_window(winui.EXE)
    ok = winui.capture(win, path)

    check("截得到应用窗口", bool(ok))

    if not ok:
        return

    image = Image.open(path).convert("RGB")
    box = winui.canvas_box(image)

    check("量得出预览画布", box is not None)

    if box is None:
        return

    box = (box[0], box[1], box[2], winui.frame_bottom(image, box))
    left, right, top, bottom = box
    width = right - left + 1
    height = bottom - top + 1
    ratio = width / height

    check("画面是 9:16", abs(ratio - 9 / 16) / (9 / 16) < 0.01,
          "%d×%d 比 %.4f（9:16 是 0.5625）" % (width, height, ratio))

    # 绘图区：上面是标题与那个大数字，下面是四张卡片。取中间那一段，避开两头。
    plot = (left, right, top + (height * 40 // 100), top + (height * 66 // 100))
    red = near(image, plot, rgb("Emphasis"))
    green = near(image, plot, rgb("Fall"))

    tone = "红" if profit >= 0 else "绿"
    mine, other = (red, green) if profit >= 0 else (green, red)

    check("曲线的颜色跟着收益的符号走（收益 %+.2f 元 → %s）" % (profit, tone),
          len(mine) > 1500 and len(mine) > len(other) * 4,
          "近红 %d 像素 / 近绿 %d 像素" % (len(red), len(green)))

    span = 0 if not mine else max(x for x, _ in mine) - min(x for x, _ in mine)

    check("曲线铺满绘图区宽度（不是只画到一半）", span > width * 0.7,
          "曲线横跨 %d 像素，画布宽 %d" % (span, width))


# ---- 4) 真机 --------------------------------------------------------------------------

def texts(win):
    # **`winui.find_all` 的 `limit` 是深度上限，不是条数上限。** 传 4000 是让它往下爬四千层，
    # 整棵树一次几十秒 —— 于是每次轮询都像卡住了，而 `wait_for` 的 180 秒在它眼里只有三趟。
    # 走得动的上限是 30 层（这一页的列表离窗口根 20 层不到），一层就够它走完。
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=30) if c.Name]


def wait_for(win, pattern, seconds=120):
    """等到某一句话出现在界面上。

    用 `winui.find`（**找到就停**）而不是先收全树再逐个比：后者每趟几十秒，等一句话的事会
    变成等三四趟棵树的事，最后一根稻草是超时。
    """
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(1)

        hit = winui.find(win, lambda c: pattern.search(c.Name) if c.Name else False)

        if hit is not None:
            return pattern.search(hit.Name)

    return None


def find_text(win, pattern):
    for name in texts(win):
        hit = pattern.search(name)

        if hit:
            return hit

    return None


def press(win, control):
    if control is None:
        return False

    try:
        win.SetActive()
        time.sleep(0.2)
    except Exception:  # noqa: BLE001
        pass

    pattern = None

    try:
        pattern = control.GetInvokePattern()
    except Exception:  # noqa: BLE001
        pattern = None

    if pattern is not None:
        try:
            pattern.Invoke()
            return True
        except Exception:  # noqa: BLE001
            pass

    try:
        box = control.BoundingRectangle

        if box.width() > 0 and box.height() > 0:
            control.Click(simulateMove=False)
            return True
    except Exception:  # noqa: BLE001
        pass

    return False


def goto(win, name):
    """导航到某一页。

    **第十九项在视口之外。** 导航栏是可滚动的，滚出去的那些项 `BoundingRectangle` 量成
    (0,0,0,0)，`Click` 在空矩形上静默跳过 —— 于是「点了没反应」，而它其实一次都没点着。
    先 `ScrollIntoView` 把它滚进来，再量一次矩形。
    """
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    for _ in range(6):
        try:
            item.GetScrollItemPattern().ScrollIntoView()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(0.5)

        if item.BoundingRectangle.width() > 0:
            break

    return winui.invoke_click(item)


def deficit(page, guess):
    """对不上时把每一行的贡献摊开：差多少是总账，差在哪一行才是答案。

    「页面 2661 / 脚本 2673」这种话把人丢在一边 — 12 元的差额要从七行 × 三个字段里
    猜出来。逐行算下来，少的那一行自己会跳出来（实测：首旅酒店那一行的贡献凭空没了）。
    """
    lines = ["页面 %+.2f / 脚本 %+.2f，差 %+.2f 元" % (page, guess["profit"], page - guess["profit"])]

    for row in guess["rows"]:
        lines.append("    %-10s %6.0f 股 × (%s − %s) = %+9.2f"
                     % (row["code"], row["shares"], row["last"], row["prev"], row["delta"]))

    return "\n" + "\n".join(lines)


def book_rows(win):
    return [name for name in texts(win) if DETAIL.match(name)]


def main():
    for old in ("verify-portfolio-frame.png", "verify-portfolio-import.png"):
        path = os.path.join(ART, old)

        if os.path.exists(path):
            os.remove(path)

    source_checks()

    print("\n自己算一遍")

    book = ledger()

    if book is None:
        check("App 已经写过一次账本（这一页读的是那一份）", False, "找不到 " + STATE)
        return report()

    # 账本先验一遍本身的形状：后面所有敷设都拿它当输入，它自己错了底下全白塔。
    check("账本里的每一行都是合法代码（场所 + 五位或六位数字）",
          all(re.fullmatch(r"(sh|sz|bj)\d{6}|hk\d{5}", code) for code, _, _ in book))
    check("账本还是种子那九只（一眼看得出来这本账被改过多少）",
          {code for code, _, _ in book} == {code for code, _, _ in seeds()},
          "账本 %d 只 / 种子 %d 只" % (len(book), len(seeds())))

    guess = expected(book)

    if guess is None:
        check("这一页的端点今天有数据", False, "两个端点都没有返回会话")
        return report()

    print("  今天的账：%s · %d 个分钟点 · 收益 %+.2f 元 · 市值 %.2f 元 · 休市 %d 只"
          % (guess["day"], guess["points"], guess["profit"], guess["value"], len(guess["closed"])))

    # **先杀进程，再读账本，再备份。** 顺序在这个 app 上是要紧的：上一趟跑完脚本把文件还原了，
    # 可上一趟留下的那个**应用实例还活着**，它内存里那两笔成交还在 —— 它要是再写一次，
    # 还原就白做了，而下一趟起手面对的是一本脏账：第一次导入全被认成重复（实测就是这样）。
    # 还原挂着呕吐式的结果，还不如在源头把写着的那个人先请出去。
    winui.kill(winui.EXE)

    original = open(STATE, "rb").read()
    started = json.loads(original.decode("utf-8")).get("Trades", [])

    print("  起手的账：%d 只持仓 · %d 笔成交（应当是 0）"
          % (len(json.loads(original.decode("utf-8"))["Holdings"]), len(started)))

    check("账本起手是干净的（不然第一次导入会被认成重复）", len(started) == 0,
          "起手就有 %d 笔成交" % len(started))

    backup = STATE + ".verify-bak"
    shutil.copy2(STATE, backup)

    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来", False)
        return report()

    try:
        win.SetActive()
        time.sleep(1)

        try:
            win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(1.5)
        except Exception:  # noqa: BLE001
            pass

        print("\n进页")

        check("导航里有这一页，而且点得动", goto(win, "实时持仓收益"))
        time.sleep(4)

        check("页面上有两个按钮（管理持仓 / 导入成交）",
              winui.find(win, lambda c: c.AutomationId == "ManageButton") is not None
              and winui.find(win, lambda c: c.AutomationId == "ImportButton") is not None)

        updated = wait_for(win, re.compile(r"^最后更新\s*\d{2}:\d{2}:\d{2}$"), 150)

        check("打开就自己取了一次数（不用按按钮）", updated is not None,
              updated.group(0) if updated else "等了 150 秒没有「最后更新」")

        rows = book_rows(win)

        check("持仓列表是九行", len(rows) == 9, "读到 %d 行" % len(rows))

        # 列表写着股数与成本，所以「脚本算的那本账」和「页面画的那本账」能对得上自己。
        # 少了这一条，上面那句「收益一致」即使通过了也可能是巧合 —— 而账本被改过之后
        # （超图 5900 股 @8.387，不是种子那行）它正好会是巧合之外的另一种东西。
        shown = sorted((float(a.replace(",", "")), float(b))
                       for a, b in (DETAIL_ROW.match(n).groups() for n in rows if DETAIL_ROW.match(n)))
        wanted = sorted((shares, cost) for _, shares, cost in book)

        missed = [n for n in rows if not DETAIL_ROW.match(n)]

        check("列表上的股数与成本就是文件里那本账",
              len(shown) == len(wanted)
              and all(abs(a - b) < 1e-6 and abs(c - d) < 5e-4
                      for (a, c), (b, d) in zip(shown, wanted)),
              "列表 %d 行 / 文件 %d 行%r" % (len(shown), len(wanted), missed[:3]))

        closed_rows = [name for name in texts(win) if name == "休市"]

        check("休市的那几只标着「休市」，不是拿上一场的价冒充今天",
              len(closed_rows) == len(guess["closed"]),
              "页面 %d 行 / 脚本算出 %d 只休市（%s）"
              % (len(closed_rows), len(guess["closed"]), "、".join(guess["closed"]) or "没有"))

        print("\n取数")
        fetch = winui.find(win, lambda c: c.AutomationId == "FetchButton")

        check("按得动「获取数据」", press(win, fetch))

        got = wait_for(win, FETCHED, 180)

        if got is None:
            check("状态行报出「哪天 · 几个分钟点 · 收益」", False, "等不到那句话")
        else:
            day, points, money = got.group(1), int(got.group(2)), got.group(3)
            mine = float(money.replace("¥", "").replace(",", "").replace("+", ""))

            check("画的是今天的账", day == guess["day"], "页面 %s / 脚本 %s" % (day, guess["day"]))
            check("分钟点数与独立算的一致", points == guess["points"],
                  "页面 %d / 脚本 %d" % (points, guess["points"]))
            check("收益与独立算的一致（差 < 0.5 元）", abs(mine - guess["profit"]) < 0.5,
                  deficit(mine, guess) if abs(mine - guess["profit"]) >= 0.5
                  else "页面 %+.2f / 脚本 %+.2f" % (mine, guess["profit"]))

            frame_checks(guess["profit"])

        before = book_rows(win)

        # ---- 导入成交 ---------------------------------------------------------------
        #
        # 两笔同时刻、同价、一买一卖：现金进出相抵，持仓一进一出，账本回到原样。于是
        # 「导进去了」与「导完还是对的」可以分开验 —— 前者的证据是状态行那三个数字，后者
        # 的证据是前后两次取数的收益一模一样。
        print("\n导入成交")

        rows_text = ("买入 sz300036 超图软件 10.00 10.00 100 100 14:57:00\n"
                     "卖出 sz300036 超图软件 10.00 10.00 100 100 14:57:30")

        check("打开「导入成交」",
              press(win, winui.find(win, lambda c: c.AutomationId == "ImportButton")))
        time.sleep(2)

        raw = winui.find(win, lambda c: c.AutomationId == "Raw")

        check("对话框里有粘贴框", raw is not None)

        if raw is not None:
            raw.GetValuePattern().SetValue(rows_text)
            time.sleep(2)

            parsed = find_text(win, re.compile(r"识别到\s*(\d+)\s*笔"))

            check("粘进去两笔就被认成两笔", parsed is not None and parsed.group(1) == "2",
                  parsed.group(0) if parsed else "没有「识别到 N 笔」")

            apply = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "导入")

            check("「导入」按钮亮着（没有读不出来的行）", apply is not None and apply.IsEnabled)
            check("按下「导入」", press(win, apply))
            time.sleep(4)

            # 报重复时要把「应用了几次」摊开看。 reason 有两种可能：账本起手就是脏的（上一次
            # 跑没还原干净），或者一次按下应用了两遍。前者 file 里 2 笔，后者 4 笔 —— 光看
            # 那句「重复 2 笔」两边长得一模一样。
            said = find_text(win, IMPORTED)
            journalled = json.loads(open(STATE, encoding="utf-8").read()).get("Trades", [])

            print("    按下之后文件里的成交：%d 笔，状态行：%s"
                  % (len(journalled), said.group(0) if said else "（没有）"))

            check("状态行说导入了两笔、没有重复、没有无对应的持仓",
                  said is not None and said.group(1) == "2" and said.group(2) == "0"
                  and said.group(3) == "0",
                  said.group(0) if said else "没有「已导入 N 笔成交」")

            after = book_rows(win)

            check("账本回到原样（一买一卖抵平，数量与摊薄成本都不变）",
                  sorted(before) == sorted(after),
                  "%d 行 → %d 行" % (len(before), len(after)))

            again = wait_for(win, FETCHED, 180)

            if again is None:
                check("导入之后再取一次数", False, "等不到状态行")
            else:
                money = again.group(3)
                now = float(money.replace("¥", "").replace(",", "").replace("+", ""))

                check("收益回到原值（同一分钟一进一出，曲线不动）",
                      abs(now - guess["profit"]) < 0.5,
                      "导入前 %+.2f / 导入后 %+.2f" % (guess["profit"], now))

            # 再导一次同一份：指纹认得出来。
            check("再打开一次「导入成交」",
                  press(win, winui.find(win, lambda c: c.AutomationId == "ImportButton")))
            time.sleep(2)

            raw = winui.find(win, lambda c: c.AutomationId == "Raw")

            if raw is not None:
                raw.GetValuePattern().SetValue(rows_text)
                time.sleep(2)

                apply = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "导入")
                press(win, apply)
                time.sleep(4)

                said = find_text(win, IMPORTED)

                check("同一份清单再导一次，两笔都认成重复",
                      said is not None and said.group(1) == "0" and said.group(2) == "2",
                      said.group(0) if said else "没有「已导入 N 笔成交」")

                check("重复导入之后账本一字不变", sorted(book_rows(win)) == sorted(before))
    finally:
        # 关掉可能还开着的对话框：不关，下一次跑的导航会被它挡着。
        for _ in range(3):
            close = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭")

            if close is None:
                break

            press(win, close)
            time.sleep(1)

        if backup is not None and original is not None:
            shutil.copy2(backup, STATE)
            os.remove(backup)

            # 还原要**真的比过字节**才算数。备份路径写错过一次：那时 `os.path.exists` 恒假，
            # 于是不备份、不还原、也不报错 —— 测验那两笔成交就这么留在了读者的账本里，
            # 下一次跑从一本不一样的账开始，而报错出现在「收益对不上」那一栏，离病根三小时远。
            same = open(STATE, "rb").read() == original

            check("跑完之后账本还原成了跑之前那一版", same,
                  "文件与跑之前的字节不同" if not same else "")
        else:
            check("账本跑之前就在（不然备份不了，也还原不了）", False, STATE)

    report()


if __name__ == "__main__":
    sys.exit(main() or 0)
