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
import glob
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
# 「最后更新」那一行，改了它就是又取了一次数。
UPDATED = re.compile(r"^最后更新\s*(\d{2}:\d{2}:\d{2})$")
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
          "if (holding.IsHongKong && live)\n                {\n                    close = HongKongClose;" in pnl
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

    # ---- 三个观感开关（从「持仓收益」页移植过来的）----------------------------------
    #
    # 这三个开关只改「同一批数字放在哪儿」，不改任何数字。所以它们错起来的样子很特别：
    # 源码里写着、控件也亮着，画面却一动不动 —— 比如渲染器把它们读成了可写属性，构造时
    # 还是默认值。源码这一层能管住的正是这一条：三个都必须是**构造参数**。
    check("三个观感开关都是构造参数，不是事后可写的属性（否则关键那一帧拿到的是默认值）",
          "bool crossSafeRight = false, bool mascot = false, bool dynamicAxis = false)"
          in render)

    check("越线开关：开 = 让到用户设的边距，关 = 连那条轨一起让开",
          "var right = crossSafeRight ? context.ChartRight : Math.Min(context.ChartRight, context.SafeRight());"
          in render)

    check("动态纵轴取的是已经画出来的那一段的极值，且零线始终留在轴内",
          "if (dynamicAxis && shown >= 0)" in render
          and "peak = Math.Max(peak, session.Samples[i].Pnl);" in render
          and "var high = Math.Max(0, peak);" in render)

    check("牛熊骑在曲线头上，涨红跌绿（和曲线、和大数字同一个判据）",
          "Mascots.Draw(" in render
          and "value >= 0, Palette.Emphasis, Palette.Fall" in render)

    check("页面把三个开关交给渲染器",
          "crossSafeRight: CrossCheck.IsChecked is true," in page
          and "mascot: MascotCheck.IsChecked is true," in page
          and "dynamicAxis: DynamicAxisCheck.IsChecked is true" in page)

    # 三个开关复用的是已有的词条：同一句话在 14 种语言里写两遍，改一处就会漏一处。
    check("三个开关在页面上，词条复用持仓页那份（一句话不写两遍）",
          xaml.count('Click="OnLookChanged"') == 3
          and 'x:Uid="SafeRightCross"' in xaml
          and 'x:Uid="PositionMascot"' in xaml
          and 'x:Uid="PositionDynamicAxis"' in xaml)

    check("三个开关都记在偏好里（下次打开还是上次的看法）",
          '_prefs.Save("CrossSafeRight"' in page
          and '_prefs.Save("Mascot"' in page
          and '_prefs.Save("DynamicAxis"' in page
          and '_prefs.GetBool("CrossSafeRight", false)' in page
          and '_prefs.GetBool("Mascot", false)' in page
          and '_prefs.GetBool("DynamicAxis", false)' in page)

    # 改看点不该再打一次请求：三个开关都不动数字，重取一遍是一天里每只持仓多出两次请求，
    # 换回来的是同一个数，还会把读者正在看的那一帧挪走。
    check("改这三个开关只重画、不重取（OnLookChanged 里没有 LoadAsync）",
          "private void OnLookChanged(object sender, RoutedEventArgs e)\n"
          "    {\n"
          "        ApplyPreviewSettings();\n"
          "        SavePreferences();\n"
          "    }" in page
          and "LoadAsync" not in page.split("private void OnLookChanged")[1].split("private ")[0])

    # ---- 页眉两行 -------------------------------------------------------------------
    #
    # 2026-10-20 改的：日期单独一行、放大、换 `Moving` 那支琥珀色；「9 只持仓」和
    # 「截至 15:00」从帧上拿掉；「成交 N 笔」改成数**曲线已经走到的那几笔**。
    # 头两条在源码里只有一种写法，第三条例外 —— 它错了画面照样是「成交 0 笔」，
    # 而 0 笔正是这本书大部分时候的样子，所以一定要在源码这层把统计口径钉住。
    check("日期单独占一行，40 号粗体，用 `Moving` 那支琥珀色（原来是 25 号灰的副标题）",
          "using (var dayFormat = Ink.Format(context.Px(40), bold: true))" in render
          and "Ink.Centred(session2, session.Day, cx, Row(context, 0.187), dayFormat, Palette.Moving, a);"
          in render)

    check("帧上不再说「N 只持仓」，也不再点名「截至 HH:MM」",
          "session.Holdings.Count" not in render
          and "PortfolioPnlSubtitle" not in render
          and "PortfolioPnlTradesLine\", PortfolioSession.Clock" not in render)

    check("成交笔数数的是曲线已经走到的那几笔，不是全天的总数（`Filled`）",
          "return session.Trades.Count(t => t.Minute <= reached);" in render
          and "var trades = Filled(index)" in render
          and "session.TradeCount" not in render)

    check("页眉那个笔数和曲线上的圆点用的是同一条「到点才算」的规矩",
          "if (trade.Minute > reached)" in render
          and "var reached = session.Samples[index].Minute;" in render)

    # 装载器拿到的是**整本流水**，自己挑出画的那一天。反过来先把「今天的」筛一道，凌晨
    # （今天还没开盘、页上画的是上一个交易日）那一整天的成交就全丢了：曲线画着那一天却
    # 一个成交标记都没有，笔数恒为 0，页面上也没有任何一句解释。
    check("页面把整本成交流水交给装载器，而不是先只要「今天的」",
          "[.. Portfolio.Trades]" in page and "Portfolio.TradesOn(" not in page
          and "public static IReadOnlyList<PortfolioTrade> Trades => [.. Journal];" in book)

    # 「截至」只留在旧字符串里。14 份 resw 里任何一份还写着两个占位符，那一语言的字幕
    # 就会在运行时 FormatException（参数给了一个，模板要两个）—— 而这一页只有中文用户
    # 会先看到，别的语言是发版之后才发现的。
    stale = []

    for path in sorted(glob.glob(os.path.join(SRC, "Strings", "*", "Resources.resw"))):
        lang = os.path.basename(os.path.dirname(path))

        # **别叫 `text`。** `text` 上面已经装的是 TradeText.cs，在这个循环里覆盖掉它，
        # 循环之后所有拿 `text` 比的判据其实都在比最后一份 resw（tr-TR）—— 它们会
        # 一律报红，而源码完全正确，红的样子和「功能没做」一模一样。
        body = open(path, encoding="utf-8-sig").read()
        found = re.search(r'PortfolioPnlTradesLine"><value>([^<]*)</value>', body)

        if found is None:
            stale.append(lang + ":没有这条")
            continue

        value = found.group(1)

        if "{1}" in value or "截至" in value or "{0}" not in value:
            stale.append("%s:%s" % (lang, value))

    check("成交笔数那行在 14 种语言里都只剩一个占位符，没有一份还写着「截至」",
          not stale, "、".join(stale[:4]))

    # ---- 导入截图 -------------------------------------------------------------------
    #
    # 2026-10-20：桌面截一张手机行情里的订单列表（307×235）交给这一页，识别引擎在它自己的
    # 尺寸上把小数点读成居中点、把冒号读成中文冒号、把中文名读成别的中文名，解析器只好一行
    # 一行拒掉 —— 这一路走完，对话框说的是「识别到 0 笔」。实测那一张：原尺寸 0 笔，放大
    # 2 倍 4 笔（第 5 行丢了「买入」两个字），放大 4 倍 5 笔。所以先放大，再对缺方向词的
    # 那一行补读一次。
    check("小截屏先放大再交给识别引擎（307 宽的截图就是常态，不是边角情况）",
          "private const double TargetWidth = 700;" in screen
          and "private const int MaxFactor = 3;" in screen
          and "var factor = Factor((int)decoder.PixelWidth);" in screen
          and "ScaledWidth = (uint)(width * factor)," in screen)

    check("放大用 Fant（这几个字要的是笔画不糊，双线性会把小数点糊进数字里）",
          "InterpolationMode = BitmapInterpolationMode.Fant," in screen)

    check("缺方向词的行补读一次，整行取说得多的那一次（绝不一行拼一半）",
          "if (TradeText.Incomplete(rows))" in screen
          and "rows = TradeText.Merge(rows, twice);" in screen
          and "public static bool Incomplete(IReadOnlyList<string> rows) =>" in text
          and "public static IReadOnlyList<string> Merge(" in text
          and "if (first.Count != second.Count)" in text
          and "Side(second[i]) is not null ? second[i] : row" in text)

    # 钟是行的分隔符：两个钟被读成一个，两行就并成一行，出来的是一笔**错的**成交
    # （上一行的价 + 下一行的码与时间），而错的比缺的更坏 —— 它会被悄悄记进账里。
    check("一个格子里出现两个代码就是两笔（宁缺不错）",
          "private static IEnumerable<string> Single(string block)" in text
          and "yield return block[..cut].Trim();" in text
          and "return [.. blocks.SelectMany(Single)];" in text)

    check("引擎读丢的那几种字都收回来（、当逗号 / 分号当冒号 / 逗号当小数点 / S 读成 5）",
          ".Replace('、', ',')" in text
          and "[;；∶]" in text
          and "Regex Thousands" in text
          and "Regex Decimals" in text
          and ".Replace('5', 's')" in text)

    check("撤单 / 废单 / 未成交单独归一类（它们带着码、价、量、钟，当成交导进去就是凭空多一笔）",
          "public IReadOnlyList<string> Cancelled { get; init; } = [];" in text
          and "{ Cancelled = cancelled }" in text
          and '"已撤", "部撤", "撤单", "废单",' in text)

    # 导入默认填「今天」，可这一页画的是**最后一个有成交的日子**。凌晨跑（今天还没开盘）
    # 两者不是同一天：对话框说「已导入 5 笔」，曲线不动、笔数还是 0，页面上没有一句解释。
    check("导入的日期默认是页面正在画的那一天，不是今天的日期",
          "new TradeImportDialog(ImportDay())" in page
          and "_session is { Day.Length: > 0 } session && DateOnly.TryParse(session.Day, out var day)" in page)


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


def day_trades(day):
    """账本里落在**画的那一天**的成交，按时间排好。

    装载器（`IntradayPnl.Assemble`）拿到的是整本流水，进门第一件事就是按 `t.Day == day`
    筛一遍，`opening` 与 `TradeCash` 都只用筛过的那一份。这里照做：不筛的话，账上任何
    一天的历史成交都会挤进当天的收益里。
    """
    if not os.path.exists(STATE):
        return []

    data = json.loads(open(STATE, encoding="utf-8").read())

    return sorted((t for t in data.get("Trades", []) if t.get("Day") == day),
                  key=lambda t: (t.get("Time", ""), t.get("Code", "")))


def expected(book=None):
    """按页面的定义把今天算一遍：日期、分钟点数、收益。

    **收益 = Σ (现持股数 × 末价 − 开盘持股数 × 昨收 + 当天成交现金) × 汇率。**

    这不是「Σ 持股 × (末价 − 昨收)」，两者在**当天有成交**时差着一大块：买入把股数推上去
    的同时把钱付出去，卖出把股票换成钱 —— 现金那一项必须进来，否则每买一次就凭空多出一块
    浮盈。开盘持股数也不是现在的股数，而是把当天的成交**从最后一笔往前倒推**回去（同一分钟
    一买一卖的那种来回，正推会把开盘算成「卖掉的那些」，整天就差一个开盘市值）。

    没开市的那几只两头都按同一个价计，贡献恒为 0，所以不写进来也不影响结果 —— 而这一点
    正是「休市那两只不算进曲线」那条断言要说的事。

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

    # 当天成交：倒推开盘持股、累计现金（买是付出去，卖是收进来）。
    trades = day_trades(day)

    opening = {code: shares for code, shares, _ in book}
    cash = {}

    for trade in reversed(trades):
        sign = -1 if trade["Side"] == 0 else 1
        held = opening.get(trade["Code"], 0.0)
        before = held + (sign * trade["Shares"])

        if before <= 0:
            opening.pop(trade["Code"], None)
        else:
            opening[trade["Code"]] = before

    for trade in trades:
        sign = -1 if trade["Side"] == 0 else 1
        cash[trade["Code"]] = cash.get(trade["Code"], 0.0) + (sign * trade["Shares"] * trade["Price"])

    # 当天清仓的那几只不在账上，但**当天的已实现盈亏在**：装载器会把它们以 0 股挂进来，
    # 只剩下现金那一项。少了这一行，「今天卖掉的那只」挣的钱一笔都算不进来。
    tickers = [(code, shares) for code, shares, _ in book]

    for code in cash:
        if code not in opening and code not in [c for c, _ in tickers] and cash[code] != 0:
            tickers.append((code, 0.0))

    last = 570
    profit = 0.0
    value = 0.0
    rows = []

    for code, shares in tickers:
        session = sessions.get(code)
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

        opened = opening.get(code, 0.0)
        money = cash.get(code, 0.0)
        delta = ((shares * price) - (opened * prev) + money) * scale

        rows.append({"code": code, "shares": shares, "open": opened, "prev": prev,
                     "last": price, "cash": money, "delta": delta})

        profit += delta
        last = max(last, min(close, max(prices)))

    # The app skips the lunch break: the axis is the four trading hours laid end to end
    # (09:30–11:30 then 13:00–close), not the raw clock span. Count the minutes that fall
    # inside a trading window, matching IntradayPnl.Assemble's windows — Hong Kong's lunch is
    # 12:00–13:00, the mainland's is 11:30–13:00.
    lunch_start = 720 if live_hk else 690
    points = sum(1 for m in range(570, last + 1) if not (lunch_start < m < 780))

    return {
        "day": day,
        "points": points,
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

    # 阈值是 0.6 而不是 0.7，因为绘图区本来就只有画布的这么多：左边 150 的边距、右边
    # 194 的安全线（`SafeArea.Right` 是 18%），两条加起来占掉 32%，能画的只剩 0.68。
    # 0.7 那条线是照着**越界**的旧外观校准的 —— 那个时候曲线一路画到右边距，压进了手机
    # 自己盖住的按钮带。越线开关关掉之后曲线退回到安全线以内，0.68 是它**画满**的样子；
    # 反过来，一条只画了半场的曲线没有这个宽度，0.6 仍然拦得住。
    check("曲线铺满绘图区宽度（不是只画到一半）", span > width * 0.6,
          "曲线横跨 %d 像素，画布宽 %d" % (span, width))


# ---- 3.5) 三个观感开关 ----------------------------------------------------------------

def grab(win, name):
    """一张窗口图，加上画布在窗口里的坐标框；抓不到返回 None。"""
    from PIL import Image

    path = os.path.join(ART, name)

    if not winui.capture(win, path):
        return None

    image = Image.open(path).convert("RGB")
    box = winui.canvas_box(image)

    if box is None:
        return None

    return image, (box[0], box[1], box[2], winui.frame_bottom(image, box))


def curve_any(image, box):
    """绘图带里那条曲线的像素，**红绿都算**。

    曲线的颜色跟着「曲线头那个点」的正负走（`DrawCurve` 里 `colour = positive ? Emphasis : Fall`，
    `positive = value >= 0` 取的是已经画到那一帧的累计盈亏）。所以同一根曲线，停在结尾是红、
    停在中段某一刻可能是绿 —— 端到端实测里就有「整天盈利、但上午一度浮亏」的日子。只认一种
    颜色会把那一帧的曲线整个漏掉，于是动态纵轴那段量出来是 `0 → 0`。量和 `frame_checks` 同一条
    带子（画布高度的 40%–66%）。
    """
    left, right, top, bottom = box
    height = bottom - top + 1
    band = (left, right, top + (height * 40 // 100), top + (height * 66 // 100))

    return near(image, band, rgb("Emphasis")) + near(image, band, rgb("Fall"))


def pale(image, window):
    """一块窗口里**发白**的像素：牛熊徽章那张脸是近白的（红满、绿蓝也高），曲线和背景都不是。

    **为什么不能再用「两张图差了哪些像素」。** 背景那张山影是带水痕的，两张截图只要不是
    同一毫秒合成，它就差出几千个像素 —— 而卡片的底色是半透明的，底下的水痕变了，从卡片上
    透出来也跟着变。实测两个方向：同一帧量出 454 个（那次水痕恰好重合），另一次量出 3775
    个、外框 362×418，看着像「整幅重画」，其实徽章只有三百来个像素。判据只好改成**找颜色**
    而不是**找差**：徽章是画面上唯一一处近白的大块，它出现了就是出现了，水痕怎么动都不影响。
    """
    left, right, top, bottom = window
    px = image.load()
    found = []

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            r, g, b = px[x, y][:3]

            if r > 200 and g > 150 and b > 150:
                found.append((x, y))

    return found


def set_switch(win, automation_id, on, tries=6):
    """把一个复选框扳到 `on`，并读回确认。返回是否真的到了想要的状态。

    **`InvokePattern` 在 WinUI 的复选框上不翻面** —— 回调走了，框还是空的，看起来像「这个
    开关没实现」。翻面要走 `TogglePattern.Toggle()`，而且每趟读回 `ToggleState`：uiautomation
    拿到的状态偶尔是上一次的快照，不读回就等于在猜。
    """
    control = winui.find(win, lambda c: c.AutomationId == automation_id)
    wanted = 1 if on else 0

    for _ in range(tries):
        if control is None:
            return False

        try:
            pattern = control.GetTogglePattern()
        except Exception:  # noqa: BLE001
            return False

        if pattern.ToggleState == wanted:
            return True

        try:
            pattern.Toggle()
        except Exception:  # noqa: BLE001
            press(win, control)

        time.sleep(0.9)
        control = winui.find(win, lambda c: c.AutomationId == automation_id)

    if control is None:
        return False

    try:
        return control.GetTogglePattern().ToggleState == wanted
    except Exception:  # noqa: BLE001
        return False


def set_progress(win, progress):
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is None:
        return False

    slider.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.8)

    return True


def changed_pixels(first, second, box, floor=26):
    """两张**同一窗口**的截图之间变了的地方，只在画布框里取。"""
    left, right, top, bottom = box
    a = first.load()
    b = second.load()
    found = []

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pa, pb = a[x, y][:3], b[x, y][:3]

            if sum(abs(pa[i] - pb[i]) for i in range(3)) > floor:
                found.append((x, y))

    return found


def shot_at(win, name, progress):
    """停在某个进度上抓一张 —— 先 re-seek 再截图。

    不 re-seek 直接抓，两张图可能停在不同进度（动画余势、合成线程还在画上一帧），
    整个曲线错位几千像素，把「多了一块徽章」量成「整幅重画」。
    """
    set_progress(win, progress)
    time.sleep(0.5)

    return grab(win, name)


def band(box, from_permille, to_permille):
    """画布高度上的一段，按千分比给。

    渲染器用「帧高的分数」排行，判据就用同一套分数去找那一行。换成绝对像素去找，换台机器、
    换个窗口大小就错位一行，而错位的样子是「这里没有那个颜色」—— 看起来像功能没做。
    """
    left, right, top, bottom = box
    height = bottom - top + 1

    return (left, right, top + (height * from_permille // 1000), top + (height * to_permille // 1000))


def ink(image, box, floor=90):
    """一段区域里比背景亮的像素：文字是亮的，深蓝背景三个通道都在 64 以下。

    不挑色相，因为这一行既有灰字又有红数字 —— 要量的是「这一行画了多宽」，不是「红色有多少」。
    """
    pixels = image.load()
    left, right, top, bottom = box
    found = []

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if max(pixels[x, y][:3]) >= floor:
                found.append((x, y))

    return found


def baseline_px(count, box):
    """截图里的长度折回帧的基准像素（画布 1920 高）。

    9:16 的画布，高就是 1920 个基准像素，横竖同一个比例 —— 于是「这一行的字形多高」能直接
    拿去和渲染器里的 `context.Px(40)` 比，不受窗口大小影响。
    """
    return count * 1920.0 / (box[3] - box[2] + 1)


def extent(spots, axis):
    """一堆像素在某一轴上的跨度，一个都没有时为 0。"""
    values = [point[axis] for point in spots]

    return (max(values) - min(values)) if values else 0


def clusters(spots, gap=8):
    """按 y 把像素分成几块（相邻两行差超过 `gap` 就断一块），给回每块的 `(top, bottom)`。

    页眉里那几行的位置**不是常数**：标题换行，整块页眉就跟着往下挪一行（`HeaderRow` 的
    `TitleShift`）。所以判据不能按分数去切固定的一条带子 —— 那在标题占两行时正好落在
    日期和钟中间，量到的是空气。琥珀色在这块区域里只有日期和钟两处，按 y 断开就行。
    """
    rows = sorted({y for _, y in spots})
    blocks = []
    first = last = None

    for y in rows:
        if first is None:
            first = last = y
            continue

        if y - last > gap:
            blocks.append((first, last))
            first = y

        last = y

    if first is not None:
        blocks.append((first, last))

    return blocks


def header_checks(win, name="verify-portfolio-header.png"):
    """页眉那几行：日期单独一行、变大变亮；第二行只剩成交笔数；钟还在它下面走着。

    停在结尾抓一张。三条判据都折回**帧的基准像素**去量 —— 抄窗口里的绝对像素，换台机器
    就当场作废，而它作废的样子和「功能没做」一模一样。
    """
    print("\n页眉")

    shot = shot_at(win, name, 1.0)

    check("截得到结尾那一帧", shot is not None)

    if shot is None:
        return

    image, box = shot

    # 整块页眉（标题之下、大数字之上）里找琥珀色：日期一行、钟一行，中间夹着成交笔数那行。
    # 标题是白的、大数字是红的，都不在这支色相里。
    gold = near(image, band(box, 120, 310), rgb("Moving"))
    blocks = clusters(gold)

    check("页眉上有日期和钟两处琥珀色（标题白、大数字红，都不算）", len(blocks) == 2,
          "读到 %d 处" % len(blocks))

    if len(blocks) != 2:
        return

    (date_top, date_bottom), (clock_top, clock_bottom) = blocks

    tall = baseline_px(date_bottom - date_top, box)

    check("日期换了颜色（`Moving` 那支琥珀色，不再是灰的）",
          len([1 for _, y in gold if date_top <= y <= date_bottom]) > 150)

    # 旧副标题 25 号，字形高约 18 个基准像素；40 号约 28。窗口里画布只有 422 像素宽，
    # 一像素折回帧里是 2.5 个基准像素 —— 门槛放在 22，既不碰 18 那头，也离 28 那头够远。
    check("日期字号真的放大了（字形高 %.0f 基准像素，25 号字只有 18）" % tall, tall >= 22)

    # 第二行夹在这两块琥珀色中间 —— 它的位置由上下两块定，不靠分数猜。
    second = ink(image, (box[0], box[1], date_bottom + 2, clock_top - 2))
    wide = baseline_px(extent(second, 0), box)

    # 只有「成交 N 笔」。「截至 15:00 · 成交 0 笔」横跨 200 多个基准像素，这一版不到 110，
    # 门槛 160 分得开，也不至于因为哪种语言翻得长一点就误伤。
    check("第二行只剩成交笔数（横跨 %.0f 基准像素，带「截至 15:00」那版是 200 多）" % wide,
          0 < wide < 160)

    reds = near(image, (box[0], box[1], date_bottom + 2, clock_top - 2), rgb("Emphasis"))

    check("笔数那个数字还在，而且是强调色", len(reds) > 25, "%d 像素" % len(reds))

    check("走着的钟和日期同一支颜色（也在页眉里、也放大到同一档）",
          baseline_px(clock_bottom - clock_top, box) >= 22,
          "钟的字形高 %.0f 基准像素" % baseline_px(clock_bottom - clock_top, box))


def counter_checks(win):
    """「成交 N 笔」跟着曲线走：半场之前一直是 0，走到底才数到导入的那两笔。

    脚本不认字，所以不判「那个字形是不是 2」，判的是**它在什么时候变**：十五分之一处
    和半场那两帧必须一模一样（那两刻都还没走到 14:57），结尾必须不一样（走到了）。改动
    之前这个数是全天总数，三帧一模一样 —— 而它和做对了的样子在结尾那一帧完全一致，
    光看结尾分不出来。

    三张图必须各自比在自己那张画布框里，所以先验三张图的框一致。实测吃过一次：导入之后
    状态行那句变长、多折了一行，预览从 422×749 缩到 384×683，「同一个数字」量出八十几个
    像素的差 —— 差得像是数变了，其实是整个画面缩了。
    """
    early = shot_at(win, "verify-portfolio-count-early.png", 0.15)
    mid = shot_at(win, "verify-portfolio-count-mid.png", 0.5)
    end = shot_at(win, "verify-portfolio-count-end.png", 1.0)

    if early is None or mid is None or end is None:
        check("截得到「早段 / 半场 / 结尾」三张图", False)
        return

    check("三张图的画布框一样（布局没有在两次抓图之间变过）",
          early[1] == mid[1] == end[1], "%r / %r / %r" % (early[1], mid[1], end[1]))

    if not early[1] == mid[1] == end[1]:
        return

    box = early[1]

    # 页眉那一块里唯一的红是笔数那个数字：日期与钟是琥珀色的，大数字在更下面（标题占两行
    # 时它跟着往下挪，0.31 这条线仍然在它上面）。
    reds = near(early[0], band(box, 120, 310), rgb("Emphasis"))

    check("早段那一帧找得到笔数那个红数字", len(reds) > 25, "%d 像素" % len(reds))

    if len(reds) <= 25:
        return

    xs = [x for x, _ in reds]
    ys = [y for _, y in reds]

    # 框比字形本身大 3 像素：换数字时字形边缘也可能差一像素，框要盖得住。
    number = (min(xs) - 3, max(xs) + 3, min(ys) - 3, max(ys) + 3)

    at_mid = changed_pixels(early[0], mid[0], number)
    at_end = changed_pixels(mid[0], end[0], number)

    check("半场之前笔数不动（15% 与 50% 那两帧一模一样）", len(at_mid) <= 6,
          "差 %d 个像素" % len(at_mid))

    check("走到底数字变了（那两笔 14:57 的成交数进来了）", len(at_end) >= 20,
          "差 %d 个像素" % len(at_end))

    set_progress(win, 1.0)


def counter_phase(day, pristine):
    """往账本里直接写两笔当天的成交，再起一趟应用，看页眉那个数是不是跟着曲线走。

    **为什么不借导入对话框**：对话框的日期默认是**今天**，而这一页画的是「最后一个有成交
    的日子」。凌晨跑这一趟时两者不是同一天 —— 那两笔落在画外，页眉从头到尾都是 0，量出来
    像是「这个数不会动」。导入那条路已经单独验过（识别、重复、账本抵平），这里要验的只是
    渲染器会不会按曲线已经走到的那一分钟去数。

    两笔一买一卖、同一分钟、同价同量：现金相抵、持仓一进一出，于是**整条曲线一个像素都不
    变**，变的只有页眉那个数 —— 这正是要量的东西。

    账本先备份在 `pristine` 里，跑完原样写回；写回之后比一次字节，别让测验的成交留在
    读者真金白银的账本里。
    """
    print("\n成交笔数跟着曲线走")

    book = json.loads(pristine.decode("utf-8"))

    book["Trades"] = [
        {"Day": day, "Time": "14:57:00", "Code": "sz300036", "Name": "超图软件",
         "Side": 0, "Price": 10.0, "Shares": 100.0},
        {"Day": day, "Time": "14:57:30", "Code": "sz300036", "Name": "超图软件",
         "Side": 1, "Price": 10.0, "Shares": 100.0},
    ]

    winui.kill(winui.EXE)
    time.sleep(2)

    with open(STATE, "w", encoding="utf-8") as handle:
        json.dump(book, handle, ensure_ascii=False, indent=2)

    try:
        win = winui.launch(winui.EXE)

        check("第二趟起得来应用", win is not None)

        if win is None:
            return

        win.SetActive()
        time.sleep(1)

        try:
            win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(1.5)
        except Exception:  # noqa: BLE001
            pass

        check("第二趟也进得了这一页", goto(win, "实时持仓收益"))

        got = wait_for(win, UPDATED, 180)

        check("第二趟自己取完了一次数", got is not None,
              got.group(0) if got else "等到 180 秒没有「最后更新」")

        if got is not None:
            counter_checks(win)
    finally:
        winui.kill(winui.EXE)
        time.sleep(1)

        with open(STATE, "wb") as handle:
            handle.write(pristine)

        check("第二趟之后账本还是跑之前那本",
              open(STATE, "rb").read() == pristine)


def look_checks(win, profit):
    """三个观感开关在**画面上**的证据。

    三个都只改「同一批数字放在哪儿」，所以证据只能是画面：源码里三个构造参数都写对了、
    渲染器却一个都没读，长得和「这三项没做」一模一样。三处的判据都是**前后两张图的差**：
    停在同一进度上的同一帧，开着与关着应当只有那一处不同。

    开头先把三个开关摆回关 —— 它们是**偏好**，上一趟跑完留着「开」，这一趟的「关」就量成
    了「开」，三条全绿而什么都没验。
    """
    print("\n三个观感开关")

    names = (("CrossCheck", "越过右侧安全线"),
             ("MascotCheck", "显示牛熊图标"),
             ("DynamicAxisCheck", "动态纵轴"))

    check("三个开关都在页面上，而且扳得动",
          all(set_switch(win, control, False) for control, _ in names))

    # 每一张图都先 re-seek 到目标进度再抓（`shot_at`）—— 这样「开 / 关」两张图永远停在同一
    # 帧，量到的差就只有那个开关本身。

    # ---- 越过右侧安全线 ---------------------------------------------------------
    off = shot_at(win, "verify-portfolio-cross-off.png", 1.0)

    check("开关扳到开", set_switch(win, "CrossCheck", True))
    on = shot_at(win, "verify-portfolio-cross-on.png", 1.0)

    set_switch(win, "CrossCheck", False)

    if off is None or on is None:
        check("截得到「越线前 / 越线后」两张图", False)
    else:
        before = curve_any(off[0], off[1])
        after = curve_any(on[0], on[1])

        x_off = max((x for x, _ in before), default=0)
        x_on = max((x for x, _ in after), default=0)

        # 边距 150 比那条轨的 194 窄，所以「越过」这一下在 1080 宽的画面里是 44 像素，
        # 折到窗口里约 17 像素。判据只要 6 像素：量的是方向，不是那 44 的绝对值。
        check("打开之后曲线真的往右伸了（越过了那条轨）", x_on - x_off >= 6,
              "曲线右端 %d → %d 像素（+%d）" % (x_off, x_on, x_on - x_off))

    # ---- 显示牛熊图标 -----------------------------------------------------------
    off = shot_at(win, "verify-portfolio-mascot-off.png", 1.0)

    check("开关扳到开", set_switch(win, "MascotCheck", True))
    on = shot_at(win, "verify-portfolio-mascot-on.png", 1.0)

    set_switch(win, "MascotCheck", False)

    if off is None or on is None:
        check("截得到「牛熊关 / 牛熊开」两张图", False)
    else:
        left, right, top, bottom = off[1]

        # 徽章骑在曲线头上，所以先找曲线头：关掉时那一段曲线最靠右的那一列。
        line = curve_any(off[0], off[1])
        head_x = max((x for x, _ in line), default=left + (right - left) // 2)
        at_head = [y for x, y in line if x >= head_x - 2]
        head_y = int(sum(at_head) / len(at_head)) if at_head else (top + bottom) // 2

        # 窗口只要够装下那枚徽章（半径 30 基准像素 ≈ 12 个窗口像素，再加一点余量）：
        # 开得越大，水痕、卡片这些与开关无关的东西就越容易混进来。
        window = (max(left, head_x - 80), min(right, head_x + 40),
                  max(top, head_y - 80), min(bottom, head_y + 40))

        before = pale(off[0], window)
        after = pale(on[0], window)

        check("打开之后曲线头上多了一枚浅色的徽章",
              len(after) - len(before) > 120,
              "近白像素 %d → %d（窗口 x %d~%d, y %d~%d）"
              % (len(before), len(after), window[0], window[1], window[2], window[3]))

        xs = [x for x, _ in after]
        ys = [y for _, y in after]

        wide = (max(xs) - min(xs)) if after else 0
        tall = (max(ys) - min(ys)) if after else 0

        # 一块徽章，不是整幅重画：它自己的外框就那么点大（画布 422×749）。
        check("徽章是一小块（不是整幅重画）", after and wide < 60 and tall < 60,
              "徽章 %d×%d 像素，画布 %d×%d" % (wide, tall, right - left + 1, bottom - top + 1))

        # 它骑在曲线头上：重心在那一点附近，不跑到卡片那一带去。
        centre = (sum(ys) / len(ys)) if after else bottom

        check("徽章跟着曲线头，不掉到卡片那边", after and abs(centre - head_y) < 70,
              "徽章重心 y=%d / 曲线头 y=%d" % (centre, head_y))

    # ---- 动态纵轴 ---------------------------------------------------------------
    #
    # 停在 25%：这一天「已经画出来的那一段」只占全天的一小段，动态纵轴才拉得开差距 —— 停在
    # 结尾两者相等（那正是设计：封面要和关掉时一模一样），量出来是 0。曲线颜色跟着曲线头那个
    # 点的正负走，中段某一刻可能是绿也可能是红，所以量两条颜色都算。
    off = shot_at(win, "verify-portfolio-axis-fixed.png", 0.25)

    check("开关扳到开", set_switch(win, "DynamicAxisCheck", True))
    on = shot_at(win, "verify-portfolio-axis-dynamic.png", 0.25)

    set_switch(win, "DynamicAxisCheck", False)
    set_progress(win, 1.0)

    if off is None or on is None:
        check("截得到「固定纵轴 / 动态纵轴」两张图", False)
    else:
        fixed = curve_any(off[0], off[1])
        dynamic = curve_any(on[0], on[1])

        span_fixed = (max(y for _, y in fixed) - min(y for _, y in fixed)) if fixed else 0
        span_dynamic = (max(y for _, y in dynamic) - min(y for _, y in dynamic)) if dynamic else 0

        check("同一进度下，动态纵轴把这半场画得更高（轴跟着已经画出来的那一段）",
              span_dynamic > span_fixed * 1.2 and span_fixed > 0,
              "曲线高度 %d → %d 像素" % (span_fixed, span_dynamic))


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


def wait_for_new(win, pattern, previous, seconds=120):
    """等某个数**变成别的**。`previous` 是按下按钮之前读到的那个数（或 None）。

    这个页面把结果常驻在界面上，所以「等它出现」永远是立刻满足的；能证明「又算了一次」的
    只有「它换了」。
    """
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(1)

        hit = winui.find(win, lambda c: pattern.search(c.Name) if c.Name else False)

        if hit is not None:
            found = pattern.search(hit.Name).group(1)

            if found != previous:
                return found

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
        lines.append("    %-10s %6.0f 股（开盘 %6.0f）× (%s − %s) + 现金 %+.0f = %+9.2f"
                     % (row["code"], row["shares"], row["open"], row["last"], row["prev"],
                        row["cash"], row["delta"]))

    return "\n" + "\n".join(lines)


def book_rows(win):
    return [name for name in texts(win) if DETAIL.match(name)]


def main():
    for old in ("verify-portfolio-frame.png", "verify-portfolio-import.png",
                "verify-portfolio-cross-off.png", "verify-portfolio-cross-on.png",
                "verify-portfolio-mascot-off.png", "verify-portfolio-mascot-on.png",
                "verify-portfolio-axis-fixed.png", "verify-portfolio-axis-dynamic.png",
                "verify-portfolio-header.png", "verify-portfolio-count-early.png",
                "verify-portfolio-count-mid.png", "verify-portfolio-count-end.png"):
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

    print("  起手的账：%d 只持仓 · %d 笔成交"
          % (len(json.loads(original.decode("utf-8"))["Holdings"]), len(started)))

    # **这本账可能本来就有成交** —— 读者自己导进来的就是。所以这里不能要求它是空的
    # （那样每跑一趟都会红，而红的原因和「功能坏了」毫无关系），要保证的只有一件：
    # 这一趟要导的那两笔，账上还没有。不然第一次导入全被认成重复，后面每一条判据都在
    # 验一件没有发生的事。
    clash = [t for t in started
             if t.get("Day") == guess["day"] and t.get("Code") == "sz300036"
             and str(t.get("Time", "")).startswith("14:57")]

    check("要导的那两笔（14:57 一买一卖）账上还没有，否则会被认成重复", not clash,
          "账上已有 %r" % (clash[:2] if clash else "无"))

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
        #
        # **成本按显示的三位小数比。** 账里存的是四位（`Portfolio.Put` 用 `Math.Round(…, 4)`），
        # 摊薄成本除不尽，列表又只印三位（`0.###`）：6.5295 印成 6.53、14.3787 印成 14.379。
        # 拿四位去比印出来的三位，差 5e-4 就红，而红的原因和账错了毫无关系。
        shown = sorted((float(a.replace(",", "")), round(float(b), 3))
                       for a, b in (DETAIL_ROW.match(n).groups() for n in rows if DETAIL_ROW.match(n)))
        wanted = sorted((shares, round(cost, 3)) for _, shares, cost in book)

        missed = [n for n in rows if not DETAIL_ROW.match(n)]

        check("列表上的股数与成本就是文件里那本账",
              len(shown) == len(wanted)
              and all(abs(a - b) < 1e-6 and abs(c - d) < 5e-3
                      for (a, c), (b, d) in zip(shown, wanted)),
              "列表 %d 行 / 文件 %d 行%r" % (len(shown), len(wanted), missed[:3]))

        closed_rows = [name for name in texts(win) if name == "休市"]

        check("休市的那几只标着「休市」，不是拿上一场的价冒充今天",
              len(closed_rows) == len(guess["closed"]),
              "页面 %d 行 / 脚本算出 %d 只休市（%s）"
              % (len(closed_rows), len(guess["closed"]), "、".join(guess["closed"]) or "没有"))

        print("\n取数")
        fetch = winui.find(win, lambda c: c.AutomationId == "FetchButton")

        # **等「最后更新」的时间戳换掉，而不是等那句话出现。** 那句话现在是常驻行（`Adopt`
        # 里写的），打开页面就有 —— 等它「出现」会立刻拿到上一次的数，于是「按得动」这一条
        # 变成什么都没验。时间戳换掉才说明真的又读了一次。
        stamp = find_text(win, UPDATED)

        check("按得动「获取数据」", press(win, fetch))

        fresh = wait_for_new(win, UPDATED, stamp.group(1) if stamp else None, 180)

        check("按下之后真的重取了一次（最后更新换了时间）", fresh is not None,
              ("原来的 " + stamp.group(1) if stamp else "按下之前没有时间戳"))

        got = find_text(win, FETCHED)

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

            # 三个观感开关：画面上的前后对照，只能真机量。
            look_checks(win, guess["profit"])

            # 页眉那几行。放在导入之前量：这会儿页面是刚取完数、账上还没有成交的样子，
            # 也就是读者平时看到的那一帧。
            header_checks(win)

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

            # 导入之后页面自己也重取一次（`OnImport` 里那句 `SilentRefreshAsync`），所以这里
            # 同样等时间戳换掉再读 —— 不然读到的是导入**之前**那一行，而它当然还是对的。
            refetched = wait_for_new(win, UPDATED, fresh, 180)
            again = find_text(win, FETCHED)

            if again is None or refetched is None:
                check("导入之后再取一次数", False,
                      "时间戳没换" if refetched is None else "读不到收益那句话")
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
            # **先请它出去，再还原文件。** App 手里攥着它自己那份账，退出或下一次保存时会把
            # 内存里那本**写回磁盘** —— 还原在前、它写在后，还原就等于没做。实测撞过一次：
            # 文件里剩下的正是「测验那两笔成交 + 还原后的股数成本」，两半来自两个时刻，
            # 而每一半单独看都自洽，于是当天收益比脚本算的多了整整 1803 元。
            winui.kill(winui.EXE)
            time.sleep(1)

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

    # ---- 成交笔数跟着曲线走（另起一趟）--------------------------------------------
    #
    # 单独一趟的理由写在 `counter_phase` 里：导入对话框的日期默认是**今天**，而这一页画的是
    # 「最后一个有成交的日子」，凌晨跑这一趟时两者不是同一天 —— 那两笔落在画外，量出来
    # 像是「这个数不会动」。
    counter_phase(guess["day"], original)

    report()


if __name__ == "__main__":
    sys.exit(main() or 0)
