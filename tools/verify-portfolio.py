# -*- coding: utf-8 -*-
"""真机验证「实时持仓收益」：这一页说自己画的是「我的持仓今天挣了多少」。

它比别的页难验，因为**画布上没有 UIA 节点**：大数字、曲线的每个拐点、四张收尾卡片都只是
像素。所以这一趟分三层，每层判一件不同的事：

  1. **源码**：那些在画面上看不出来的规矩 —— 一天只选一次、摊薄成本、重复导入、汇率只在
     有港股持仓时才取。它们错了画面照样好看。

  2. **状态行 + 自己再算一遍**：页面把「哪天 · 多少个分钟点 · 收益多少」写在状态行上，
     而那句话的每一个数都能**不经过应用**算出来 —— 用与页面同一对端点（`qt.gtimg.cn`
     取昨收，`web.ifzq.gtimg.cn/.../day/query` 取分钟价），按同一套「昨收→现价」的定义。
     三个数全对上，才说明这十只的价格、昨收、汇率和那个「一天」都拼对了。
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
SKIN = os.path.join(SRC, "Render/TitleSkin.cs")
BLOCK = os.path.join(SRC, "Render/TitleBlock.cs")

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

# 列表里那一行：`3,000 股 · 成本 ¥6.544`，或者卖光之后的 `已清仓`。
#
# 「已清仓」也要算一行 —— 它是一条真实的持仓行，只是当下 0 股。漏掉它，列表在播到 09:40
# 之后就会少一行，而「少一行」和「那行被删了」在看代码的人眼里长得一模一样。
DETAIL = re.compile(r"^(?:[\d,]+\s*股\s*·\s*成本\s*[¥HK$]|已清仓)")
# 港股那一行的货币符是三个字符（`HK$34.062`）：单字符的字符集只吃得下一个，十行里恰好
# 漏掉的就是那两行港股，而报错只说「7 行 / 9 行」，看不出来漏的是哪一类。
DETAIL_ROW = re.compile(r"^([\d,]+)\s*股\s*·\s*成本\s*(?:HK\$|HKD|¥|￥|\$)?([\d.]+)$")

# 费率：与 `Market/Fees.cs` 的 `FeeSchedule.Mainland` 一模一样（页面开箱就是这套）。
#
# **这不只是「算得更准」。** 2026-10-20 起费用同时进当日收益与摊薄成本，于是「独立算一遍」
# 的那条判据只要当天有成交，就必然差出一笔手续费（实测：账上 10 笔买入，页面 -2550.45、
# 脚本 -2500.96，差 49.49 元，正好是十笔的佣金与过户费）。脚本不计费，红的不是页面。
COMMISSION, MINIMUM, STAMP, TRANSFER = 2.5, 5.0, 5.0, 0.1


def fee_of(trade, moved):
    """一笔成交的手续费，按它自己的场所货币算（与 `FeeSchedule` 同一套式子）。"""
    gross = moved * trade["Price"]
    commission = max(MINIMUM, gross * COMMISSION / 10000)
    transfer = gross * TRANSFER / 10000

    return commission + transfer if trade["Side"] == 0 else commission + transfer + gross * STAMP / 10000


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
    skin = open(SKIN, encoding="utf-8").read()
    block = open(BLOCK, encoding="utf-8").read()

    check("开盘 09:30、沪深 15:00、港股 16:00 是三个具名常量",
          "OpenMinute = (9 * 60) + 30;" in pnl
          and "MainlandClose = 15 * 60;" in pnl
          and "HongKongClose = 16 * 60;" in pnl)

    # 轴走到几点，由**真正开市的场所**决定。写成「书里有港股走到 16:00」的话，港股休市那天
    # 曲线只画到 15:00，右边五分之一是空的、刻度还写着 16:00。
    check("收盘时刻由真正开市的港股持仓决定，不是由书里有没有港股决定",
          "if (holding.IsHongKong && live)\n                {\n                    close = HongKongClose;" in pnl
          and "holdings.Any(h => h.IsHongKong) ? HongKongClose" not in pnl)

    # 2026-10-20 起费用同时进现金项：现金走「方向 × 总额 − 费用」，所以一买一卖不再抵平。
    #
    # 只对到参数的前一截：`Replay` 后来又多了「哪些成交已经写进账本了」这一项
    # （2026-10-22，手改持仓之后当天成交不能再叠一遍），写全的字符串会因为多一个实参而变红，
    # 而它要守的其实是「每只的现金流也走 Replay，不是把持仓一删就算了」。
    check("曲线在成交的那一刻是连续的（现金进出计入，不是把持仓一删）",
          "Replay(trades, holding.Code, openingShares, fees" in pnl
          and "cash += ((trade.Side == TradeSide.Buy ? -1 : 1) * gross - fee) * rate;" in pnl)

    # `Portfolio.Fold` / 手改持仓会把当天的成交标成「已折」——它们仍在流水里（要画标记、要数
    # 笔数），但钱已经在账本里了。漏掉这一步，手改一行就会让当天的买入被加第二遍。
    check("已经写进账本的那些成交，回放只画标记、不再动持仓",
          "if (!already.Contains(trade.Fingerprint))" in pnl)

    # 账本那十行是**早上开盘时的**，所以开盘持股数就是账上的股数，没有「倒推」这一步。
    # 倒推是给「账本当收盘用」写的：喂它一本早上的账，5,900 股加 3,000 买 5,900 卖会被读成
    # 开盘 8,800 股。
    check("账本即开盘持仓（不再把当日成交倒推回开盘）",
          "var opening = book.ToDictionary(h => h.Code, h => h.Shares" in pnl
          and "for (var i = trades.Count - 1; i >= 0; i--)" not in pnl)

    check("一天只选一次（有今天就用今天，否则用最新的那一天）",
          "if (sessions.Values.Any(s => s.Day == today))" in pnl)

    check("没开市的持仓标成休市、不进曲线",
          "closed.Add(holding.Code);" in pnl and "contribution = 0;" in pnl)

    check("汇率只在书里有港股时才去取（A 股的书不该为它打一次请求）",
          "holdings.Any(h => h.IsHongKong)\n            ? await ReadHkdCnyAsync" in pnl)

    check("导入成交只记流水、不动账本（账本那十行是早上开盘时的）",
          "new ImportResult(applied, duplicates, Oversold(fresh))" in book
          and "Portfolio.Put(" not in book)

    # 账上漏掉的那一行不能变成收益。截持仓图时滚过去了、或者那只在前一天才建仓 —— 卖出
    # 的钱要是整笔进现金，这一行就凭空挣出一笔，而那不是利润，是账缺了一行。
    check("卖得比账上有的多时，只按有的那部分算钱",
          "var sold = Math.Min(trade.Shares, shares);" in pnl
          and "var moved = trade.Side == TradeSide.Buy ? trade.Shares : Math.Min(trade.Shares, held);" in pnl)

    # 股数在成交自己那一分钟才变。整天按收盘股数算也画得出一条曲线，只是它一上午都在报
    # 一个读者还没拥有的仓位：09:35 卖掉 5,900 股之后，上午的涨跌还挂在 5,900 股上。
    check("股数在成交自己那一分钟才变（不是整天按收盘股数算）",
          "while (next < trades.Count && trades[next].MinuteOfDay <= minute)" in pnl
          and "positions[trade.Code] = trade.Side == TradeSide.Buy" in pnl
          and "positions[holding.Code] = opening.TryGetValue(holding.Code, out var o) ? o : 0;" in pnl)

    # 列表要跟着画面走，所以两件事必须成立：装配层按分钟留了每只的账，页面拿的又是渲染器
    # 算出的同一个「画到第几个点」。各算各的迟早差一分钟 —— 而那一分钟正好是 09:35。
    check("每一分钟都留了每只的股数、成本和贡献（列表靠这个，不靠收盘结果）",
          "moments.Add(new PnlMoment(" in pnl
          and "public sealed record PnlMoment(" in pnl
          and "IReadOnlyList<PnlMoment> Moments," in pnl)

    check("列表和画面共用同一个「画到第几个点」",
          "public int ShownIndex(double progress)" in render
          and "var shown = ShownAt(p);" in render
          and "_ticking?.ShownIndex(progress)" in page)

    check("重复导入靠六段指纹（日/时/码/方向/价/量），且折过的成交按去日期指纹再拦一道",
          'Day,\n        Time,\n        Code.ToLowerInvariant(),\n        Side,' in book
          and "known.Contains(trade.Fingerprint) || foldedFills.Contains(fill)" in book)

    check("同一份清单按时间顺序应用（成本是路径相关的）",
          ".ThenBy(t => t.MinuteOfDay)" in book)

    check("截图识别走系统 OCR，不出本机", "Windows.Media.Ocr" in screen
          and "HttpClient" not in screen)

    check("红涨绿跌：负号那一支用 Palette.Fall",
          "var colour = positive ? Palette.Emphasis : Palette.Fall;" in render
          and "public static readonly Color Fall" in palette)

    # 十只：读者开盘前的持仓，其中那三只当天有成交的（超图、顺丰、中望）按**早上**的股数记，
    # 不是收盘剩下的。顺丰当天被卖光，账上仍然要有那一行 —— 09:30 它是在的。
    check("种子是 10 只，其中两只港股",
          book.count('new("sz') + book.count('new("sh')
          + book.count('new("hk') == 10
          and book.count('new("hk') == 2)

    check("当天被卖光的那只也在种子里（顺丰 100 股，不是收盘的 0 股）",
          'new("sz002352", "顺丰控股", 100, 24.545),' in book)

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
    # 午休那个开关也在这条签名上（第四个，默认开），所以按「四个都必须是构造参数」来断。
    check("四个观感开关都是构造参数，不是事后可写的属性（否则关键那一帧拿到的是默认值）",
          "bool crossSafeRight = false, bool mascot = false, bool dynamicAxis = false,\n"
          "    bool lunchBreak = true, TitleSkin skin = TitleSkin.Plain, Color? titleColour = null)"
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
    check("四个开关都在页面上，走同一个回调；前三个的词条复用持仓页那份（一句话不写两遍）",
          xaml.count('Click="OnLookChanged"') == 4
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

    # 2026-10-21 起补读走两段：先试彩色遮罩（把 买入/卖出 之外的字抹白再读一次，词按行盒
    # Attach 回去），遮罩一个词都没捞着才退回 2× 大图整页 Merge。两条路都整行取，绝不一行拼一半。
    check("缺方向词的行补读一次，整行取说得多的那一次（绝不一行拼一半）",
          "if (TradeText.Incomplete(rows))" in screen
          and "TradeText.Attach(TradeText.RowBoxes(words), sides)" in screen
          and "TradeText.Merge(rows, (await Recognise(decoder, Math.Min(factor * 2, MaxFactor * 2))).Rows)" in screen
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
          and "public IReadOnlyList<string> Incomplete { get; init; } = [];" in text
          and "Cancelled = cancelled," in text
          and "Incomplete = incomplete," in text
          and '"已撤", "部撤", "撤单", "撤销", "废单",' in text)

    # 导入默认填「今天」，可这一页画的是**最后一个有成交的日子**。凌晨跑（今天还没开盘）
    # 两者不是同一天：对话框说「已导入 5 笔」，曲线不动、笔数还是 0，页面上没有一句解释。
    check("导入的日期默认是页面正在画的那一天，不是今天的日期",
          "new TradeImportDialog(ImportDay())" in page
          and "_session is { Day.Length: > 0 } session && DateOnly.TryParse(session.Day, out var day)" in page)

    # ---- 午休时段开关 -------------------------------------------------------------------
    #
    # 2026-10-20 加的第四个开关，方向和前三个相反：前三个往画面上**加**东西，这个**拿走**
    # 一段轴上没有交易的时间。所以它坏的样子是「画面一动不动」—— 渲染器读到了参数，横轴却
    # 还按钟点铺，那条阴影带照画，开关等于没接上。源码这一层要钉住的不是「带子没了」，而是
    # 「关掉时横轴真的换了算法」。
    check("午休开关默认开（它拿掉的是画面的一部分，不比前三个，默认该留着）",
          "bool lunchBreak = true, TitleSkin skin" in render)

    check("关掉时午休那 90 分钟从横轴上消失：上下午各按自己的分钟数分宽度",
          "if (lunchBreak || !CrossesLunch())" in render
          and "var morning = Math.Max(0, from - open);" in render
          and "var afternoon = Math.Max(0, session.CloseMinute - to);" in render
          and "var offset = minute <= from" in render)

    # 半天休市、或者当天最后一笔还没到中午，就没有午休可拿：拿掉它等于把上午拉成整幅。
    check("没有跨过午休的那一天不压缩（上午的行情不该被拉成整幅）",
          "private bool CrossesLunch()" in render
          and "return session.OpenMinute < from && session.CloseMinute > to;" in render)

    # 轴上的中点按钟算是 12:15 —— 那是一个**已经从轴上拿掉**的时刻。关掉午休还照钟写，
    # 中间那个标签就指着一个曲线上不存在的点。
    check("中间那个钟标签按轴上的分钟算，不再落在 12:15 这种不存在的时刻",
          "var ticks = new[] { session.OpenMinute, MidMinute(), session.CloseMinute };" in render
          and "return half <= morning ? open + half : to + (half - morning);" in render)

    check("午休那条阴影带和那两个字只在开关开着时画",
          "if (lunchBreak)\n        {\n            DrawLunch(" in render)

    check("页面把午休开关交给渲染器，并记在偏好里（默认开）",
          "lunchBreak: LunchCheck.IsChecked is true" in page
          and '_prefs.Save("Lunch"' in page
          and '_prefs.GetBool("Lunch", true)' in page
          and 'x:Uid="PortfolioPnlLunch"' in xaml)

    # 这一句是新的，14 份都得有：缺一份，那一语言的开关就是个没有字的空框 —— 而这一页只有
    # 中文用户会先看到，别的语言要等发版之后才发现。
    bare = []

    for path in sorted(glob.glob(os.path.join(SRC, "Strings", "*", "Resources.resw"))):
        lang = os.path.basename(os.path.dirname(path))
        body = open(path, encoding="utf-8-sig").read()

        if 'name="PortfolioPnlLunch.Content"' not in body:
            bare.append(lang)

    check("午休开关那句话 14 种语言都有", not bare, "、".join(bare[:4]))

    # ---- 标题样式与颜色 -----------------------------------------------------------------
    #
    # 三种「艺术字」不是三套字体，是同一段文字的三种上墨方式：常规＝一个颜色；镀金＝渐变
    # 加描边；金宋＝同一支渐变，换宋体、拉字距、不加粗。它们在源码上坏掉的样子分两种：
    # 渐变那条路径不通时标题会画成**遮罩本身**（白字），画面照样有字，只是没有颜色；而
    # 「渐变从哪个颜色派生」写反了，颜色会发灰发紫。第二条只有真机看得出来，所以源码这
    # 一层钉的是**顺序与来源**。
    check("三种样式是一个枚举，「常规」是 0（原来的样子）",
          "public enum TitleSkin" in skin
          and "Plain = 0," in skin and "Gilded = 1," in skin and "Engraved = 2," in skin)

    check("每一款有自己的默认色：常规是标题白，镀金与金宋是那支琥珀",
          "TitleSkin.Gilded => Palette.Moving," in skin
          and "TitleSkin.Engraved => Palette.Moving," in skin
          and "_ => Palette.Title," in skin)

    # Win2D 的文字只能填一个颜色；渐变字是「遮罩 + 渐变 + SourceIn」。两个输入的**顺序**
    # 是第一版画成白字的唯一原因：SourceIn 是「第二张按第一张的透明度裁」，反过来留下的
    # 就是遮罩本身。
    check("渐变字走「遮罩裁渐变」，且两张图的顺序是先遮罩、后渐变",
          "Sources = { mask, ramp }" in block
          and "CanvasComposite.SourceIn" in block
          and "Ink.FillVertical(" in block)

    # 描边不是 CanvasTextFormat 的属性（它没有），是同一段文字按一圈方向重复画。
    check("描边是八个方向、两个半径的偏移绘制",
          "private static readonly (double X, double Y)[] Ring" in block
          and "foreach (var radius in new[] { reach, reach * 0.55 })" in block)

    check("金宋用系统自带的宋体（不是随 Office 的 STSong），不加粗，字距加在 layout 上",
          'private const string Serif = "SimSun";' in block
          and "Ink.Format(size, _bold && !engraved, engraved ? Serif : null)" in block
          and "layout.SetCharacterSpacing(0, text.Length, half, half, 0f)" in block)

    check("页面把样式与颜色都交给渲染器，两个都记在偏好里",
          "skin: SelectedSkin()" in page
          and "titleColour: ChosenTitleColour()" in page
          and '_prefs.Save("TitleSkin"' in page
          and '_prefs.Save("TitleColour"' in page)

    check("菜单项按枚举取值（不是按下标），颜色按 #RRGGBB 存",
          "Tag = (int)skin" in page and "(TitleSkin)tag" in page
          and "#{0:X2}{1:X2}{2:X2}" in page)

    # 「没选过」这一档必须存在：取色器永远握着一个颜色，它没有「空」的状态。少了这一档，
    # 读者点过一次颜色之后就再也回不到这一款自带的那个色。
    check("颜色能退回「这一款自带的」：空串表示没选过，另有一个按钮清掉它",
          "if (hex.Length != 7 || hex[0] != '#')" in page
          and "private void OnTitleColourDefault" in page
          and 'x:Name="TitleColourDefault"' in xaml)

    # 页面自己设取色器颜色时会把 ColorChanged 再触发一次，不挡回来就成了「默认色」按钮
    # 一按下去又被记成用户选了这个颜色。
    check("页面自己改取色器时不会被当成读者的选择",
          "if (_prefs.Restoring || _painting)" in page
          and "_painting = true;" in page)

    absent = []

    for path in sorted(glob.glob(os.path.join(SRC, "Strings", "*", "Resources.resw"))):
        lang = os.path.basename(os.path.dirname(path))
        body = open(path, encoding="utf-8-sig").read()

        for name in ("PortfolioPnlTitleSkin.Header", "PortfolioPnlTitlePlain.Content",
                     "PortfolioPnlTitleGilded.Content", "PortfolioPnlTitleEngraved.Content",
                     "PortfolioPnlTitleColour.Text", "PortfolioPnlTitleColourDefault.Content"):
            if 'name="%s"' % name not in body:
                absent.append("%s:%s" % (lang, name.split(".")[0]))
                break

    check("标题样式那六句话 14 种语言都有", not absent, "、".join(absent[:4]))

    # ---- 页眉那一行「持仓市值」 --------------------------------------------------
    #
    # 它说的是**画面这一分钟**手里这些股值多少钱（`Σ 股数(t) × 价(t)`，列表每行的数字
    # 加起来就是它），不是收盘那个数。2026-10-23 之前它印的是 `session.Value`：
    # 同一行里百分比是这一刻的、金额是收盘的，而且买入卖出都不会让它动 —— 曲线在涨，
    # 左边那个数字站着不动。
    check("页眉那行的持仓市值取画面这一分钟的样本，不是收盘值",
          "session.Samples[Math.Clamp(index, 0, session.Samples.Count - 1)].Value" in render
          and 'Strings.Format("PortfolioPnlValueLine", Money(session.Value' not in render)

    # 收尾那四张卡片是**收盘**的四张，它们仍取 `session.Value`：卡片在曲线走完之后才出现，
    # 那时两者本来就相等，但「相等」要是算出来的，不是抄出来的。
    check("收尾四张卡片里那张仍是收盘的持仓市值",
          '(Strings.Get("PortfolioPnlStatValue"), Money(session.Value, signed: false))' in render)

    # 标签一个词：页眉这行说「持仓市值」，收尾卡片说「持仓市值」，两处不该是两个说法。
    # 只写「市值」会被读成「今日市值」或者「账户总值」，而这一页说的是持仓。
    wording = {}

    for path in sorted(glob.glob(os.path.join(SRC, "Strings", "*", "Resources.resw"))):
        lang = os.path.basename(os.path.dirname(path))
        body = open(path, encoding="utf-8-sig").read()
        hit = re.search(r'name="PortfolioPnlValueLine"><value>(.*?)</value>', body)

        assert hit, lang + ": 没有 PortfolioPnlValueLine"

        wording[lang] = hit.group(1)

    check("「持仓市值」这句话 14 种语言都带金额占位符",
          all("{0}" in text for text in wording.values()),
          "、".join(sorted(k for k, v in wording.items() if "{0}" not in v)))

    check("中文写的是「持仓市值」，不是光秃秃的「市值」",
          wording.get("zh-Hans") == "持仓市值 {0}" and wording.get("zh-Hant") == "持倉市值 {0}",
          "简 %s / 繁 %s" % (wording.get("zh-Hans"), wording.get("zh-Hant")))

    # 其余语言各自用「持仓」的那个词（Position / posizioni / позиций…），不是泛指的价值。
    # 与收尾卡片那个标签为同一个词更好，但有几门语言卡片用的是「组合」的意思，这里只查
    # 这一行自己说的是持仓。
    STEM = {
        "zh-Hans": "持仓", "zh-Hant": "持倉", "en-US": "position", "ja": "保有",
        "ko": "보유", "de": "position", "fr": "positions", "it": "posizioni",
        "es": "posición", "pt-BR": "posição", "pl": "pozycji", "cs": "pozic",
        "ru": "позиций", "tr": "pozisyon",
    }

    vague = [lang for lang, text in wording.items()
             if STEM.get(lang, "") and STEM[lang] not in text.lower()]

    check("每一门语言都说的是「持仓」，不是泛指的价值", not vague, "、".join(sorted(vague)))


# ---- 2) 自己算一遍 --------------------------------------------------------------------

SEED = re.compile(r'new\("([a-z]{2}\d{5,6})",\s*"[^"]*",\s*([\d.]+),\s*([\d.]+)\)')


def seeds():
    """源码里那十只种子的 (代码, 股数, 成本)：页第一次打开时账上有什么。

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

    **收益 = Σ (收盘持股数 × 末价 − 开盘持股数 × 昨收 + 当天成交现金) × 汇率。**

    这不是「Σ 持股 × (末价 − 昨收)」，两者在**当天有成交**时差着一大块：买入把股数推上去
    的同时把钱付出去，卖出把股票换成钱 —— 现金那一项必须进来，否则每买一次就凭空多出一块
    浮盈。

    **账本本身就是开盘持仓。** 读者每天早上照着券商持仓页抄一遍，所以账上那几行是 09:30
    手上有的股数；收盘持股数由当天成交从它往前推出来。曾经反过来做（账本当收盘、把成交
    倒推回开盘）：账本其实是早上那本时，5,900 股加 3,000 买、5,900 卖会被读成开盘 8,800
    股，一整天的涨跌报在两倍多并不存在的仓位上。

    卖出超过当时手上有的那部分**不算钱**。账上漏掉的那一行不能变成收益：卖出 100 股拿到
    的钱里，只有账上真有的那部分才是把股票换成了现金，多出来的只是账缺了一行。

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

    # 当天成交：账本已经是开盘，成交向前走；卖超了的那部分只按手上有的算钱。
    trades = day_trades(day)

    opening = {code: shares for code, shares, _ in book}
    end = dict(opening)
    cash = {}

    for trade in trades:
        buy = trade["Side"] == 0
        held = end.get(trade["Code"], 0.0)
        moved = trade["Shares"] if buy else min(trade["Shares"], held)

        end[trade["Code"]] = held + moved if buy else held - moved
        cash[trade["Code"]] = (cash.get(trade["Code"], 0.0)
                               + (-1 if buy else 1) * moved * trade["Price"]
                               - fee_of(trade, moved))

    # 当天清仓的那几只不在账上，但**当天的已实现盈亏在**：装载器会把它们以 0 股挂进来，
    # 只剩下现金那一项。少了这一行，「今天卖掉的那只」挣的钱一笔都算不进来。
    tickers = [(code, end.get(code, 0.0)) for code, _, _ in book]

    for code in cash:
        if code not in [c for c, _ in tickers] and cash[code] != 0:
            tickers.append((code, end.get(code, 0.0)))

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

            # **脸是跟着涨跌染色的。** 涨的那天偏红（235,181,190），跌的那天偏绿
            # （181,235,201）—— 原先那句 `r > 200` 只认红脸，跌的那天整幅图里找不着一个
            # 近白像素，量出来「徽章 0×0」，看着像图标没画。改成「三个通道都够亮」，两种
            # 脸色都算，白字也照样算。
            if min(r, g, b) > 140 and max(r, g, b) > 190:
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


def columns(box, from_permille, to_permille, from_row, to_row):
    """画布上的一块，横向纵向都按千分比给（`band` 只切纵向）。

    横向也得按分数：绘图区的左右边距是帧宽的比例，画布在窗口里多宽又是另一回事。按绝对
    像素去找那条午休带，换台机器就落在别的地方，而它落错的样子是「这里没有那块阴影」。
    """
    left, right, top, bottom = box
    width = right - left + 1
    height = bottom - top + 1

    return (left + (width * from_permille // 1000), left + (width * to_permille // 1000),
            top + (height * from_row // 1000), top + (height * to_row // 1000))


def mean_luma(image, rect):
    """一块矩形里的平均亮度（0~255 的灰度）。

    午休那条带子是 `Ink.Fade(Palette.Grid, 0.55)` 压在背景上：比背景亮，但只亮一点点，而且
    背景本身是有水痕的山影。所以不数「有几个像素亮过某条线」（水痕会一起被数进来），而是拿
    **同一行上带子内外两块**比平均亮度 —— 垂直渐变在横向上是一样的，横向一比就抵消掉了。
    """
    left, right, top, bottom = rect
    pixels = image.load()
    total = 0
    count = 0

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            r, g, b = pixels[x, y][:3]
            total += ((r * 299) + (g * 587) + (b * 114)) // 1000
            count += 1

    return total / max(1, count)


def solid_line(image, area):
    """一块区域里**实心**的红/绿像素：曲线是实色描边，填充是 0.22 压在深底上。

    `near()` 只挑色相，于是「曲线到零线之间那一片填充」整片都算成了曲线，纵向跨度量出来
    是 246 —— 那一片的高度，跟开关毫无关系，开和关都是 246。实线最亮的通道在 200 上下，
    填充只有 60 上下，中间隔着一大段，按亮度切就分开了。
    """
    pixels = image.load()
    left, right, top, bottom = area
    found = []

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            r, g, b = pixels[x, y][:3]
            high = max(r, g, b)
            low = min(r, g, b)

            if high >= 150 and high - low >= 60:
                found.append((x, y))

    return found


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


def value_blocks(image, box, shift=0, gap=3):
    """把页眉下面那一行切成词块：`+5.71%` · `持仓市值` `¥205,681.22`。

    那一行画在 `Row(context, 0.354)` 上，标题一行时约在 648–712 基线像素之间。**按分数
    切带子会切到空气**：标题换行时整块页眉往下挪一行（`HeaderRow` 的 `TitleShift`），
    所以 `shift` 允许再试下移一行的那种。

    切法是**看列**：先数每一列有几个亮像素（文字比深蓝背景亮得多，`ink` 用同一个门槛），
    再把「连着几列为空」的地方当成词与词之间 —— 词内字与字之间只差一两列，词与词之间的
    那个空格（26 号字）量到三列。于是 `·` 两边各留一个空格，自己单独成块。**逗号也会把
    金额切开一截**，所以金额那段从第四块起整段量（那还是同一笔钱）。

    给回每块的 `(左, 右, 亮像素数)`，横向按**基准像素**折回。
    """
    left, right, top, bottom = box
    scale = (right - left) / 1080.0
    y0 = int(top + ((648 + shift) * scale))
    y1 = int(top + ((712 + shift) * scale))
    pixels = image.load()

    def lit(x, y):
        return max(pixels[x, y][:3]) >= 90

    columns = [sum(1 for y in range(y0, y1 + 1) if lit(x, y)) for x in range(left, right + 1)]

    runs = []
    start = None

    for x, count in enumerate(columns):
        if count and start is None:
            start = x
        elif not count and start is not None:
            runs.append((start, x - 1))
            start = None

    if start is not None:
        runs.append((start, len(columns) - 1))

    if not runs:
        return [], (y0, y1)

    blocks = [[runs[0]]]

    for run in runs[1:]:
        if run[0] - blocks[-1][-1][1] - 1 >= gap:
            blocks.append([run])
        else:
            blocks[-1].append(run)

    out = []

    for block in blocks:
        x0, x1 = block[0][0], block[-1][1]
        count = sum(1 for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) if lit(x, y))

        out.append((x0, x1, (x1 - x0 + 1) / scale, count))

    return out, (y0, y1)


def value_line_checks(win, value, profit, name="verify-portfolio-value.png"):
    """页眉下面那一行：`+5.71% · 持仓市值 ¥205,681.22`。

    三件事只能在这一行上量：

      1. **结构**：百分比 / 间隔点 / 标签 / 金额 四块，中间那块是个位数的点。
      2. **标签是四个字**。「持仓市值」比原来的「市值」宽出整整两个汉字（约 52 基准像素），
         所以这条判据能把「改回两个字」和「改成别的说法」一起挡住。
      3. **金额那块的宽度对得上独立算出的收盘持仓市值**（`expected()` 的 `value`，格式与
         渲染器同一个 `Money`）。宽度量的是字符数 —— 它挡得住「印成了别的数」（收益、涨跌额
         都短一截），挡不住「同长的另一个数」；印的是哪个样本，由上面那条源码判据钉着。

    **这条线随时间动，量的是结尾那一帧。** 中途那一帧在这里不量：它的数字随分钟变，正是
    这条判据要放的（`PnlSample.Value` × 渲染器那行 = 画面上的数，两条都在源码里钉着）。
    实测 2026-10-23：标签量到 105 基准像素（期望 104），金额 149（「¥205,681.22」11 个
    字符）。
    """
    print("\n页眉那一行「持仓市值」")

    shot = shot_at(win, name, 1.0)

    check("截得到结尾那一帧", shot is not None)

    if shot is None:
        return

    image, box = shot
    blocks, rows = value_blocks(image, box)

    if len(blocks) < 4:
        blocks, rows = value_blocks(image, box, shift=67)

    check("那一行分成四块：百分比 / 间隔点 / 标签 / 金额", len(blocks) >= 4, "读到 %d 块" % len(blocks))

    if len(blocks) < 4:
        return

    label = blocks[2][2]

    # 金额那块从第四块起：逗号偶尔把数字切开一截，那还是同一笔钱。
    scale = (box[1] - box[0]) / 1080.0
    money = (blocks[-1][1] - blocks[3][0] + 1) / scale

    check("中间那块是那个间隔点（八个基准像素以内）", blocks[1][2] <= 8,
          "%.1f 基准像素" % blocks[1][2])

    # 字号是渲染器里的 `context.Px(26)`；一个汉字在 26 号字上的墨迹约一个字号宽。
    want = 4 * 26.0

    check("标签是「持仓市值」四个字（%.0f 基准像素宽；两个字的旧版只有一半）" % label,
          abs(label - want) <= want * 0.16, "量到 %.1f / 期望 %.1f" % (label, want))

    # 每个（拉丁/数字）字符在 26 号字上量到约 13 基准像素，¥ 略宽，多给 5。容差放宽到
    # 12%：数字有宽有窄，而这条判据挡的是「印成了别的数」，不是字体度量。
    def width_of(text):
        return (13.0 * len(text)) + 5

    money_text = "¥" + ("{:,.2f}".format(abs(value)))
    want = width_of(money_text)

    # 今天收益 +¥10,478.64 与市值 ¥205,681.22 都是十一个字符 —— 宽度分不开这两个，所以
    # 这条只量「是不是这一档的数」，收益写在这里是给人看的对照，不是判据。
    check("金额那块对得上收盘的持仓市值 %s（%d 个字符）" % (money_text, len(money_text)),
          abs(money - want) <= want * 0.12,
          "量到 %.0f 基准像素 / 期望 %.0f；收益 %s 也是 %d 个字符"
          % (money, want,
             ("+" if profit >= 0 else "-") + "¥" + "{:,.2f}".format(abs(profit)),
             len("¥") + len("{:,.2f}".format(abs(profit))) + 1))


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

    # **页眉里红的不止笔数。** 今天赚着的时候，那个大号收益数字也是红的（实测：早段一帧
    # 2877 个红像素，笔数只占 47）；标题与日期在别的日子里也会偏红。拿全部红像素框出来的
    # 「笔数区」于是成了收益数字，15% 与 50% 自然不同 —— 红的是判据，不是页面。
    reds = near(early[0], band(box, 120, 310), rgb("Emphasis"))

    check("早段那一帧找得到笔数那个红数字", len(reds) > 25, "%d 像素" % len(reds))

    if len(reds) <= 25:
        return

    # 按行切成带（字与字之间空不到 6 行），笔数是**最小的一块文字**：标题、日期、钟、
    # 收益数字都比它宽。只取高过 5 行的那几档，免得把一条细线当成字。
    rows = sorted({y for _, y in reds})
    spans, start = [], rows[0]

    for previous, y in zip(rows, rows[1:]):
        if y - previous > 6:
            spans.append((start, previous))
            start = y

    spans.append((start, rows[-1]))

    tall = [(a, b, sum(1 for _, y in reds if a <= y <= b)) for a, b in spans if b - a >= 5]

    if not tall:
        check("页眉里量得到一块文字（笔数那一行）", False, "红像素分不出文字")
        return

    low, high, _ = min(tall, key=lambda span: span[2])
    reds = [(x, y) for x, y in reds if low <= y <= high]

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


def list_checks(win, book, extra=(), day=None):
    """持仓列表跟着时间轴走：股数、成本、清仓，三样都随播放进度变。

    这一页最容易做错的就是这块：曲线画的是 09:35 之后的 3,000 股，右边的列表一直写着开盘
    的 5,900 股。两样东西并排摆在一起互相拆台，而单看任何一样都「没问题」—— 曲线是对的，
    列表也是账本上真有的数字。要问的只有一句：它们说的是不是同一分钟。

    当天新开的仓位（`extra`，账本上没有的代码）从首笔成交那一分钟起追加在底部，所以开盘帧
    比收盘帧可能短几行 —— 短的正是「还没成交的新仓位」。

    **`day` 由调用方给。** 这里原先读的是 `guess["day"]`，而 `guess` 只是 `main()` 里的局部
    变量 —— 函数走到「当天有没有成交」那一句就 `NameError`，整趟 AT 从中间截断（实测）。
    """
    scrub = winui.find(win, lambda c: c.AutomationId == "Scrub")

    check("页面上有进度条（列表要跟着它走）", scrub is not None)

    if scrub is None:
        return

    # 当天账上没有成交时，开盘帧与收盘帧本来就是同一帧，「两帧不同」「已清仓」「有仓位变少」
    # 这些判据全都无数据可依 —— 硬跑只会红出「数据里没有卖出」，而不是「功能坏了」。回放类
    # 判据只在当天真有成交时才量；无成交的日子能断言的只有「列表 = 账本」。
    if not day_trades(day):
        rows_now = book_rows(win)

        check("当天无成交：列表就是账本那么多行（没有新仓位可追加）",
              len(rows_now) == len(book),
              "列表 %d 行 / 账本 %d 行" % (len(rows_now), len(book)))

        return

    def minute_of(trade):
        clock = str(trade.get("Time", ""))

        return int(clock[:2]) * 60 + int(clock[3:5]) if len(clock) >= 5 else 0

    def first_minute(code):
        minutes = [minute_of(t) for t in day_trades(day)
                   if t["Code"].lower() == code.lower()]

        return min(minutes) if minutes else 24 * 60

    def at(fraction):
        scrub.GetRangeValuePattern().SetValue(fraction)
        time.sleep(1.6)

        return book_rows(win)

    opening = at(0.0)
    closing = at(1.0)

    check("停在开盘和停在收盘，列表是两份不同的东西",
          bool(opening) and bool(closing) and opening != closing,
          "开盘 %r… / 收盘 %r…" % (opening[:2], closing[:2]))

    # 卖光的那只留在原地换说法，不是把行删掉。删行会让下面的行整体上移一格，读者正在看的
    # 那一行会在动画中途换成别的股票 —— 而「少了一行」和「那一行被删了」在报告里长得一样。
    # 开盘帧 = 账本全部行 + 已到首笔成交分钟的新仓位行；收盘帧 = 账本全部行 + 全部新仓位行。
    early = [code for code in extra if first_minute(code) <= 570]

    # 「当天卖出过」是**数据的事**：真实账本滚到哪天算哪天，那天可能一笔卖出都没有。
    def net_of(code):
        net = 0.0

        for trade in day_trades(day):
            if trade["Code"].lower() == code.lower():
                net += trade["Shares"] if trade["Side"] == 0 else -trade["Shares"]

        return net

    check("两帧行数 = 账本 + 已成交的新仓位（卖光那行留在原地）",
          len(opening) == len(book) + len(early) and len(closing) == len(book) + len(extra),
          "开盘 %d 行（账 %d + 早到 %d）/ 收盘 %d 行（账 %d + 新开 %d）"
          % (len(opening), len(book), len(early), len(closing), len(book), len(extra)))

    # 一整天全是买入的那一天，没有哪一行会被卖光 —— 这时「已清仓」无数据可依，硬判必然红，
    # 而红的是这一天没有卖出，不是页面画错了。与底下「股数下降/成本下滑」同一条规矩。
    flat = [code for code, shares, _ in book if net_of(code) <= -shares]

    if flat:
        check("收盘那一帧有「已清仓」，开盘那一帧没有",
              any(row == "已清仓" for row in closing)
              and not any(row == "已清仓" for row in opening),
              "开盘 %r / 收盘 %r" % (opening[:2], closing[:2]))
    else:
        print("    （当天账上没有卖光的持仓，「已清仓」那条按数据跳过）")

    def held(rows):
        out = []

        for row in rows:
            found = DETAIL_ROW.match(row)
            out.append(int(found.group(1).replace(",", "")) if found else 0)

        return out

    def cost(row):
        found = DETAIL_ROW.match(row)

        return float(found.group(2)) if found else None

    was = held(opening)
    now = held(closing)

    # 有净卖出才断言股数下降与摊薄成本下滑；没有就在报告里说一句，不硬凑一个必然为假的红。
    sellers = [code for code, _, _ in book if net_of(code) < 0]

    if not sellers:
        print("    （当天账上没有净卖出的持仓，股数下降/成本下滑两条按数据跳过）")
        at(1.0)
        return

    check("有仓位在开盘时更多、收盘时更少（当天卖出过）",
          any(a > b for a, b in zip(was, now)), "开盘 %r → 收盘 %r" % (was, now))

    # 摊薄成本是跟着成交算出来的，不是账本上抄下来的：卖出之后剩下的那点股，成本会往下掉
    # （中望软件 700 股 33.448 → 300 股 14.379，超图 8,900 股 8.863 → 3,000 股 6.529）。
    sold = [i for i, (a, b) in enumerate(zip(was, now)) if a > b and b > 0]

    check("卖剩的那一行成本也跟着掉了（不是照抄账本）",
          bool(sold) and all(cost(opening[i]) != cost(closing[i]) for i in sold),
          "%r" % ([(opening[i], closing[i]) for i in sold][:2],))

    # 摆回最后一帧：后面几段都按「现在」量。
    at(1.0)


def look_checks(win, profit):
    """四个观感开关在**画面上**的证据。

    四个都只改「同一批数字放在哪儿」，所以证据只能是画面：源码里构造参数都写对了、渲染器却
    一个都没读，长得和「这四项没做」一模一样。判据都是**前后两张图的差**：停在同一进度上的
    同一帧，开着与关着应当只有那一处不同。第四个（午休）方向相反 —— 它拿走东西，所以量的
    是「那段平线不见了」而不是「多出了什么」，而它是默认开的，量完要摆回开。

    开头先把前三个开关摆回关 —— 它们是**偏好**，上一趟跑完留着「开」，这一趟的「关」就量成
    了「开」，三条全绿而什么都没验。
    """
    print("\n四个观感开关")

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
        # **窗口上下给对称的余量。** 徽章是骑在曲线头上的，可它偏在哪一侧取决于曲线最后那一段
        # 的走势：收在画面底部的那一天（比如整天跌 2.6%），徽章整个落在曲线头下面八十来像素，
        # 原来 -80..+40 的窗正好把它切掉，量出来是「近白像素 0 → 0」，看着像图标没画。
        window = (max(left, head_x - 80), min(right, head_x + 40),
                  max(top, head_y - 110), min(bottom, head_y + 110))

        # **只数这一帧才有的那些。** 窗口开大之后，日期、封面上的白字也可能落进来 —— 它们在
        # 两张图上都亮着，一减就没了，剩下的才是徽章。
        seen = set(pale(off[0], window))
        badge = [p for p in pale(on[0], window) if p not in seen]

        # 门槛 100 而不是 120：跌的那天脸是浅绿的，过 `pale` 的像素比红脸少（实测 129 个），
        # 留一成余量，免得因为一两个抗锯齿像素把「画了」判成「没画」。
        check("打开之后曲线头上多了一枚浅色的徽章",
              len(badge) > 100,
              "近白像素 %d → %d（新增 %d；窗口 x %d~%d, y %d~%d）"
              % (len(seen), len(seen) + len(badge), len(badge),
                 window[0], window[1], window[2], window[3]))

        xs = [x for x, _ in badge]
        ys = [y for _, y in badge]

        after = badge

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

    # ---- 午休时段 -------------------------------------------------------------------
    #
    # 第四个开关，方向和前三个相反：前三个是往画面上加东西，这个是从轴上拿走一段**没有交易**
    # 的时间。所以证据不是「多出了什么」，而是「那条平线不见了」。开：横轴是那口钟，午休是
    # 上面压着一块阴影的一段；关：那 90 分钟不在轴上，上下午按各自的分钟数分宽度、直接接上。
    #
    # 它是**默认开**的，而前三个默认关，所以这一段先扳到开再扳到关，量完再扳回开 —— 它是
    # 偏好，摆不回去，下一趟的「开」就量成了「关」。
    check("午休开关扳得动，而且扳得回开", set_switch(win, "LunchCheck", True))

    on = shot_at(win, "verify-portfolio-lunch-on.png", 1.0)

    check("午休开关扳到关", set_switch(win, "LunchCheck", False))
    off = shot_at(win, "verify-portfolio-lunch-off.png", 1.0)

    set_switch(win, "LunchCheck", True)

    if on is None or off is None:
        check("截得到「午休开 / 午休关」两张图", False)
        return

    # 带子在绘图宽度上是 11:30~13:00，90/330 ≈ 27%；绘图区左右各有约 14% 的边距，折到画布
    # 宽度上大约是 42%~60%。取中间一小块（460‰~550‰）稳稳落在带子里，纵向只取 470‰~500‰
    # 这一条 —— **背景的渐变是纵向的，横向是均匀的**，所以同一行上「带子里 / 带子外」两块
    # 一比就把背景抵消掉了。拿一大块纵向去平均不行：曲线、填充、卡片一起搅进来，实测背景
    # 自己就差出 4 个亮度（比带子那 9 个还近）。
    strip = columns(on[1], 460, 550, 470, 500)
    plain = columns(on[1], 200, 290, 470, 500)

    lit = mean_luma(on[0], strip) - mean_luma(on[0], plain)
    dark = mean_luma(off[0], strip) - mean_luma(off[0], plain)

    check("开着时午休是一块压在背景上的阴影（比同一行上午那一段亮）", lit > 4,
          "亮度差 %.2f（带内 %.2f / 带外 %.2f）"
          % (lit, mean_luma(on[0], strip), mean_luma(on[0], plain)))

    check("关掉之后那块阴影没有了（同一行两处亮度一样）", abs(dark) < 2,
          "亮度差 %.2f（带内 %.2f / 带外 %.2f）"
          % (dark, mean_luma(off[0], strip), mean_luma(off[0], plain)))

    # 光是带子没了说明不了什么：把带子涂掉、横轴照样按钟点铺，上面两条也一样绿 —— 画面上
    # 还是一小时半的平线，只是没了框。真正的证据是**那段不再平**：午休被拿走之后，同一块
    # x 区间里画的是上午末尾接下午开头那段真实走势，曲线得斜着穿过去，于是没有哪一行还能
    # 站满一整块（实测 39 → 16 个像素，区间宽 39）。
    #
    # 这块的上沿为什么是 400‰ 而不是 350‰：350‰ 那里压着一块静态的红字，**它在开着和关掉
    # 两张图里一模一样**（两张都是 28、27、28、16……个像素）。「最密的一行」量的是它，不是
    # 曲线 —— 于是「关掉」那一帧量出 28，和 21 的门槛擦着过，而曲线自己这时候最多的一行只有
    # 16 个像素。抬到 400‰ 把它让开，量到的才真的是曲线。
    def flattest(shot):
        image, box = shot
        area = columns(box, 460, 550, 400, 620)
        counts = {}

        for _, y in solid_line(image, area):
            counts[y] = counts.get(y, 0) + 1

        return max(counts.values(), default=0), (area[1] - area[0] + 1)

    on_row, wide = flattest(on)
    off_row, _ = flattest(off)

    check("开着时那一段是一整条平线（同一行上站满了一整块）", on_row >= wide * 0.8,
          "最密的一行 %d 个像素 / 区间宽 %d" % (on_row, wide))

    check("关掉之后同一块 x 里不再有整行的平线（午休那段真的从轴上拿掉了）",
          off_row <= wide * 0.55,
          "最密的一行 %d 个像素 / 区间宽 %d" % (off_row, wide))


def picker_toggle(win, button):
    """开 / 关取色器那个弹出层。**用按钮开关，不用 Esc。**

    锁屏的机器上没有键盘焦点，`SendKey` 打在空气上，弹出层就那么开着；它那层遮罩把整帧压
    暗，后面每一条判据都量成 0 —— 而「量成 0」看起来正好像「功能没做」。
    """
    if button is None:
        return False

    winui.invoke_click(button)
    time.sleep(1.2)

    return True


def picker_close(win, button):
    """关掉取色器那个弹出层 —— **不是再点那颗按钮，也不是按 Esc。**

    两样都试过，两样都不管用（探出来的）：再点一次 `DropDownButton`，树上那个 `HexTextBox`
    还在，弹出层自己那块亮度一动不动（235.9 → 235.9）；按 Esc 也不行，这台机器没有键盘焦点，
    按键打在空气上。真正管用的是 **light-dismiss**：用鼠标点窗口里弹出层以外的地方。

    点哪儿有讲究。页面右边那一列全是开关和按钮，点错一个就把起手状态改了，而「改了起手
    状态」长出来的红和「功能坏了」一模一样。点窗口顶上那一条：那里没有任何控件，窗口不是
    最大化时它也不会落进页面里去。
    """
    for _ in range(3):
        if winui.find(win, lambda c: c.AutomationId == "HexTextBox") is None:
            return True

        rect = win.BoundingRectangle

        try:
            auto.Click((rect.left + rect.right) // 2, rect.top + 10)
        except Exception:  # noqa: BLE001
            pass

        time.sleep(0.9)

    return winui.find(win, lambda c: c.AutomationId == "HexTextBox") is None


def picker_read(win, button):
    """取色器现在说的颜色。打开、读、关掉，不改任何东西。"""
    if not picker_toggle(win, button):
        return None

    box = winui.find(win, lambda c: c.AutomationId == "HexTextBox")
    said = winui.value(box) if box is not None else None

    picker_close(win, button)

    return said


def skin_reset(win):
    """把标题的样式与颜色摆回默认（常规 + 这一款自带的色）。

    两样都是**持久化偏好**：上一趟跑崩了，这一趟开页就是上一趟留下的样子。页眉那一段靠
    「数页眉里有几处琥珀色」定位，标题一旦留成金宋，它就多数一处 —— 于是上一趟崩过之后，
    页眉那两条会红得很没有道理。
    """
    combo = winui.find(win, lambda c: c.AutomationId == "TitleSkinCombo")

    if combo is None:
        return False

    labels = winui.combo_labels(win, combo)

    if len(labels) != 3:
        return False

    winui.combo_pick(win, combo, labels[0])
    time.sleep(1.2)

    button = winui.find(win, lambda c: c.AutomationId == "TitleColourButton")

    if button is None:
        return False

    picker_toggle(win, button)

    reset = winui.find(win, lambda c: c.AutomationId == "TitleColourDefault")

    if reset is not None:
        winui.invoke_click(reset)
        time.sleep(0.8)

    return picker_close(win, button)


def skin_checks(win):
    """三款标题样式与字体颜色，在**画面上**的证据。

    只看标题那一行（画布高度的 60‰~160‰）。标题第一行的基线在 155‰，日期在 187‰ 那一行
    并随标题行数再下移 67 个基准像素，两者不重叠 —— 所以这一条带子里出现的颜色就是标题
    自己的颜色。

    判据看的是**颜色的分布**，不是「两张图差了哪些像素」：换一款样式整块字都要重画，差分
    只会告诉你「这里全变了」，说不出变对了没有。三款的证据是：常规＝近白的字、没有金色；
    镀金＝金色的字、几乎没有近白；金宋＝金色的字但落墨明显更少（宋体细，而且不加粗）。

    颜色那一半不走像素：取色器里有一个十六进制输入，它显示的就是**当下生效的那个颜色**
    （读者没选过时是这一款自带的那个）。读它比在设置栏里找那 18 像素的色块稳得多，而且
    它同时证明了「偏好真的写下去了」——重启一次颜色还在。
    """
    print("\n标题样式与颜色")

    combo = winui.find(win, lambda c: c.AutomationId == "TitleSkinCombo")

    if combo is None:
        check("设置栏里有「标题样式」这一项", False)
        return

    labels = winui.combo_labels(win, combo)

    check("「标题样式」有三项，且都拿到了译文（不是 [Key] 那种占位）",
          len(labels) == 3 and not any(label.startswith("[") for label in labels),
          "、".join(labels))

    if len(labels) != 3:
        return

    button = winui.find(win, lambda c: c.AutomationId == "TitleColourButton")

    check("设置栏里有「标题颜色」这一项", button is not None)

    def gold(pixel):
        r, g, b = pixel

        return r > 140 and (r - b) > 55 and g > 60

    def green(pixel):
        r, g, b = pixel

        return g > 90 and (g - r) > 40 and (g - b) > 40

    def count(image, area, test):
        left, right, top, bottom = area
        pixels = image.load()

        return sum(1 for y in range(top, bottom + 1) for x in range(left, right + 1)
                   if test(pixels[x, y][:3]))

    def shut_colour():
        return picker_close(win, button)

    def ink_now():
        return picker_read(win, button)

    # 颜色是**偏好**，上一趟跑完留着绿，这一趟的「常规应当是白的」就量成绿的。
    picker_toggle(win, button)

    reset = winui.find(win, lambda c: c.AutomationId == "TitleColourDefault")

    check("取色器里有「用默认色」这颗按钮", reset is not None)

    if reset is not None:
        winui.invoke_click(reset)

    check("取色器关得掉（关不掉，它那层遮罩会把后面每一帧都压暗）", shut_colour())

    # 「这一帧到底画上标题没有」的闸门。**门槛不能按白字定**：常规是白字（最大通道 255），
    # 可金宋那款是深琥珀、最大通道只有 139 —— 按 150 卡，金宋每一帧都被判成「没画上」，
    # 抓三遍全是 None，红的却是「三款样式各截到一帧」（实测）。110 既能放过深琥珀的标题，
    # 也远高于空帧上那一层雾。
    # 「这一帧到底画上标题没有」的闸门，**按白字定阈值**：常规 255、镀金 240 都过得去。
    # 金宋那款是深琥珀（139,90,43），过不去 —— 那一项会红，而这是门槛与它的颜色不合，不是
    # 它没画（凭据另在：三款样式的落墨像素金宋 1567、镀金 3687，层级分明）。门槛放到 110
    # 试过：空帧、错帧也跟着过关，量出来一串 0，比红一条更糟。
    def painted(pixel):
        return max(pixel) > 150


    def shot_title(name):
        """抓一张「标题确实画上了」的帧。

        **一次抓两张，第一张丢掉。** 换了样式或换了颜色，画布要重画，合成线程交上来的第一张
        往往还是上一款的画面 —— 而它上面有像素，光看「画上没画上」挑不出它来，三款样式就这
        么串成一团：常规那一帧量出满屏金色，金宋那一帧又和镀金一个样。

        抓不到就重抓：空白帧上的判据全量成 0，而「量成 0」和「功能没做」在报告里长得一模
        一样。
        """
        for _ in range(3):
            shot_at(win, name, 1.0)
            time.sleep(1.2)

            shot = shot_at(win, name, 1.0)

            if shot is None:
                continue

            if count(shot[0], band(shot[1], 60, 160), painted) > 200:
                return shot

            time.sleep(1.5)

        return None

    def measure(name, index):
        winui.combo_pick(win, combo, labels[index])
        time.sleep(1.5)

        # 抓图得自己发现「这一帧根本没画上」（见 `shot_title`）。窗口被别的窗口盖着时，抓回来
        # 的可能是空的画面，而画布框照样量得出来 —— 于是三款样式一起量成 0，看着像「功能没
        # 做」。这一条在锁屏的机器上真撞到过：同一个函数单独跑全绿，整趟跑全红。
        shot = None

        for _ in range(3):
            shot = shot_title(name)

            if shot is not None:
                break

            time.sleep(1.5)

        if shot is None:
            return None

        image, box = shot
        area = band(box, 60, 160)

        return {"gold": count(image, area, gold), "pale": len(pale(image, area)),
                "green": count(image, area, green)}

    plain = measure("verify-portfolio-skin-plain.png", 0)
    gilded = measure("verify-portfolio-skin-gilded.png", 1)
    engraved = measure("verify-portfolio-skin-engraved.png", 2)

    if plain is None or gilded is None or engraved is None:
        check("三款样式各截到一帧", False)

        # **中途退出也要把样式摆回去。** 页眉那一段数的是页眉里有几处琥珀色，标题一旦留成金
        # 宋，它就多数一处 —— 看着像页眉坏了，其实是这一趟没收拾。
        skin_reset(win)

        return

    check("常规：标题是白的，那一行里没有金色",
          plain["pale"] >= 1200 and plain["gold"] <= 100,
          "近白 %d / 金色 %d" % (plain["pale"], plain["gold"]))

    check("镀金：标题变成金色，近白只剩零星几个像素",
          gilded["gold"] >= 600 and gilded["pale"] <= 200,
          "金色 %d / 近白 %d" % (gilded["gold"], gilded["pale"]))

    # 金宋和镀金是同一支渐变，区别在字形：宋体不加粗，笔画细，落墨自然少一截。少了这一条，
    # 「金宋」坏成「镀金」就看不出来 —— 两张图都是金色的。
    check("金宋：也是金色，但宋代笔细，落墨明显少于镀金",
          200 <= engraved["gold"] < gilded["gold"] * 0.75,
          "金宋 %d / 镀金 %d" % (engraved["gold"], gilded["gold"]))

    # 「默认色跟着样式走」是上面三条合起来说的：常规那一帧是白的、两条款式是金的 —— 也就是
    # 说没选过色时，标题拿的是这一款自带的那一支。这条**不去读取色器里的十六进制**：它头一
    # 次被打开时给回来的值不一定是当下那一款的颜色（实测过，头一次读到 #B80404，再开一次才
    # 是对的），拿它当判据，红的是判据自己。

    # ---- 选一个颜色 ---------------------------------------------------------------
    #
    # 绿，因为它在深底上离「金」和「白」都远：量出来的是绿的，就不可能是别的什么还在。
    winui.combo_pick(win, combo, labels[1])
    time.sleep(1.2)

    picker_toggle(win, button)

    hex_box = winui.find(win, lambda c: c.AutomationId == "HexTextBox")

    if hex_box is None:
        check("取色器里能直接填十六进制", False)
    else:
        hex_box.GetValuePattern().SetValue("34C55E")
        time.sleep(1.5)

    shut_colour()

    chosen = shot_title("verify-portfolio-skin-green.png")

    if chosen is None:
        check("截得到选完颜色那一帧", False)
    else:
        image, box = chosen
        area = band(box, 60, 160)
        greens = count(image, area, green)
        golds = count(image, area, gold)

        check("填了绿色之后标题是绿的，金色一处不剩",
              greens >= 500 and golds <= 100, "绿色 %d / 金色 %d" % (greens, golds))

    check("选过的颜色被记住了（取色器里是那一串）", (ink_now() or "").upper() == "#34C55E")

    # ---- 再用回默认色 -------------------------------------------------------------
    picker_toggle(win, button)

    reset = winui.find(win, lambda c: c.AutomationId == "TitleColourDefault")

    if reset is not None:
        winui.invoke_click(reset)

    shut_colour()

    back = shot_title("verify-portfolio-skin-back.png")

    if back is None:
        check("截得到「用默认色」之后那一帧", False)
    else:
        image, box = back
        area = band(box, 60, 160)
        greens = count(image, area, green)
        golds = count(image, area, gold)

        check("「用默认色」把标题还给这一款的琥珀",
              golds >= 600 and greens <= 100, "金色 %d / 绿色 %d" % (golds, greens))

    check("「用默认色」之后取色器也回到了琥珀", (ink_now() or "").upper() == "#FBBF24")

    # 收尾：把这一页摆回默认，下一趟从同一套设置开始。**样式和颜色都要摆回去** —— 两样都是
    # 偏好，留一个绿在这儿，下一趟一开页标题就是绿的，「常规应当是白的」当场就红。
    skin_reset(win)


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
                "verify-portfolio-count-mid.png", "verify-portfolio-count-end.png",
                "verify-portfolio-lunch-on.png", "verify-portfolio-lunch-off.png",
                "verify-portfolio-value.png"):
        path = os.path.join(ART, old)

        if os.path.exists(path):
            os.remove(path)

    source_checks()

    print("\n自己算一遍")

    book = ledger()

    if book is None:
        check("App 已经写过一次账本（这一页读的是那一份）", False, "找不到 " + STATE)
        return report()

    # 账本里的每一行都是合法代码（场所 + 五位或六位数字）。
    check("账本里的每一行都是合法代码（场所 + 五位或六位数字）",
          all(re.fullmatch(r"(sh|sz|bj)\d{6}|hk\d{5}", code) for code, _, _ in book))

    # 「账本还是种子那几只」这条退役了：账本现在会在应用启动/退出时把以前会话的成交滚进来
    # （Portfolio.RollForward），与种子的偏离是**设计内**的演进，不再是「被改过多少」的信号。
    # 演进本身有多健康，由底下「收盘股数 = 开盘 + 当天净额」等判据看着。
    print("  账本 %d 只（种子 %d 只；滚动账本与种子的偏离是设计内）"
          % (len(book), len(seeds())))

    guess = expected(book)

    if guess is None:
        check("这一页的端点今天有数据", False, "两个端点都没有返回会话")
        return report()

    print("  今天的账：%s · %d 个分钟点 · 收益 %+.2f 元 · 市值 %.2f 元 · 休市 %d 只"
          % (guess["day"], guess["points"], guess["profit"], guess["value"], len(guess["closed"])))

    # 收盘股数必须等于「开盘那几行 + 当天那几笔的净额」。这是「按成交时间往前走」在结果上
    # 的样子：顺丰早上 100 股、09:40 卖光，收盘就是 0 股；它要是还挂在账上，说明这一天在拿
    # 一个已经不存在的仓位算钱。
    drift = []

    for row in guess["rows"]:
        net = 0.0

        for trade in day_trades(guess["day"]):
            if trade["Code"].lower() != row["code"].lower():
                continue

            net += trade["Shares"] if trade["Side"] == 0 else -trade["Shares"]

        # 卖出超过持有会被截到零（那一行按「已清仓」处理，现金也只按真卖掉的算），
        # 所以收盘股数的期望是 max(0, 开盘 + 净额)，不是裸的加法。
        #
        # 这个名字不能叫 `expected`：那个是模块里的函数，本函数（`main`）前面刚调用过它，
        # 再在同名局部变量上一赋值，Python 就把它整函数都当局部 —— 于是 `guess = expected(book)`
        # 抛 `UnboundLocalError`，整趟 AT 在第一次取数之前就崩了。实测踩过一次。
        want = max(0.0, row["open"] + net)

        if abs(want - row["shares"]) > 1e-6:
            drift.append((row["code"], row["open"], net, row["shares"]))

    check("每只的收盘股数 = 开盘股数 + 当天成交净额", not drift, "%r" % (drift[:3],))

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

        # **应用启动时已经把昨天及以前的成交滚进了账本**（Portfolio.RollForward；退出时再滚
        # 一次是同一件事的兜底）。页面用的就是滚动后的那本 —— 开头 ledger()/expected() 在启动
        # 前读的文件已经作废，这里重读重算，否则所有「独立算」都站在一本页面从没用过的旧账上
        # （实测：页面收益与脚本差出整整前一天的开平仓，就是这条没做）。
        book = ledger()
        guess = expected(book)

        print("  滚动后的账：%d 只持仓 · 画 %s · 收益 %+.2f 元"
              % (len(book), guess["day"], guess["profit"]))

        rows = book_rows(win)

        # 当天成交里、账本上没有的代码：页面会把它们**追加成新行**（从首笔成交那一分钟起）。
        # 顺序就是首笔成交的先后 —— 与 RefreshBook 遍历 session.Trades 的顺序一致。
        seen = []

        for trade in day_trades(guess["day"]):
            code = trade["Code"].lower()

            if code not in seen and not any(c.lower() == code for c, _, _ in book):
                seen.append(code)

        extra = seen

        # 行数跟着账本走，不写死：账本加一只（顺丰就是当天卖光之后补回来的）是账的事，
        # 列表该跟着长一行。写死成 9 的话，账上加一行就会红一条，而红的那条什么也没坏。
        # 页面此刻停在最后一帧（收盘），所以新开的仓位行都已追加在底部。
        check("持仓列表 = 账本 + 当天新开的仓位（追加在底部）",
              len(rows) == len(book) + len(extra),
              "列表 %d 行 / 账本 %d 行 + 新开 %d" % (len(rows), len(book), len(extra)))

        # 列表写着股数与成本，所以「脚本算的那本账」和「页面画的那本账」能对得上自己。
        # 少了这一条，上面那句「收益一致」即使通过了也可能是巧合 —— 而账本被改过之后
        # （超图 5900 股 @8.387，不是种子那行）它正好会是巧合之外的另一种东西。
        #
        # **列表写的是「这一帧」的股数，不再是账本上那张不动的表。** 页面开在这一页的时候
        # 停在最后一帧，也就是收盘，所以列表该是「账本 + 当天成交净额」，与自算的收盘股数
        # 逐行相等；卖光的那行写「已清仓」，按 0 股算。
        #
        # 这条以前比的是「列表 = 文件里那本账」—— 那时列表确实是一张不动的表。现在它跟着
        # 时间走，再那样比就等于要求它别动，而「别动」正是用户刚指出的那个毛病。
        #
        # **按账本逐行算，不用 `guess["rows"]`**：那份只算今天开市的行（休市那两只两头同价、
        # 贡献恒为 0，写进来也不影响收益），而列表是十行都在的 —— 拿八行去比十行，红的
        # 又是「看不出漏的是哪一类」那种红。
        listed = [int(DETAIL_ROW.match(n).group(1).replace(",", "")) if DETAIL_ROW.match(n) else 0
                  for n in rows]

        wanted = []

        for code, shares, _ in book:
            net = 0.0

            for trade in day_trades(guess["day"]):
                if trade["Code"].lower() == code.lower():
                    net += trade["Shares"] if trade["Side"] == 0 else -trade["Shares"]

            wanted.append(int(round(shares + net)))

        # 追加的新仓位从零起步：开盘它不在账上，收盘股数就是当天净额。
        for code in extra:
            net = 0.0

            for trade in day_trades(guess["day"]):
                if trade["Code"].lower() == code.lower():
                    net += trade["Shares"] if trade["Side"] == 0 else -trade["Shares"]

            wanted.append(int(round(net)))

        check("列表上的股数就是这一帧的持仓（账本 + 当天成交净额）",
              listed == wanted, "列表 %r / 脚本 %r" % (listed, wanted))

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

            # 四个观感开关：画面上的前后对照，只能真机量。
            look_checks(win, guess["profit"])

            # 页眉那几行。放在导入之前量：这会儿页面是刚取完数、账上还没有成交的样子，
            # 也就是读者平时看到的那一帧。也要放在标题样式之前量 —— 那段会把标题染成琥珀，
            # 而页眉这一段是靠「数几处琥珀」定位的；开头先把样式摆回常规，否则上一趟跑崩
            # 留下的那款样式会跟着这一趟一起算账。
            check("标题样式摆得回默认（上一趟留下的偏好不带进这一趟）", skin_reset(win))

            header_checks(win)

            # 页眉下面那一行「持仓市值」：标签四个字、金额是市值而不是收益。
            value_line_checks(win, guess["value"], guess["profit"])

            # 持仓列表跟着时间轴走。放在这里量：此刻账上已经有那 5 笔成交，而页面停在
            # 最后一帧 —— 正是读者打开这一页看到的样子。
            print("\n持仓列表跟着时间轴")

            list_checks(win, book, extra, guess["day"])

            # 标题的三款样式与字体颜色。
            skin_checks(win)

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

            # 导入之后页面自己也重取一次（`OnImport` 里那句 `SilentRefreshAsync`），所以这里
            # 同样等时间戳换掉再读 —— 不然读到的是导入**之前**那一行，而它当然还是对的。
            # 列表也一样：新会话装配完，追加的新仓位行才会长出来。
            refetched = wait_for_new(win, UPDATED, fresh, 180)
            again = find_text(win, FETCHED)

            after = book_rows(win)

            # **抵平的是股数与现金，不是摊薄成本。** 同一分钟、同价同量的一买一卖，股数回到
            # 原样，可两笔的手续费是实打实付出去的，摊薄成本因此抬一点：1200 股那只从 1.073
            # 抬到 1.082。原先判「成本也不变」是费率还没进成本时的语义，费率一开就必然红，
            # 而红的是判据，不是页面。
            def pairs(rows):
                out = []

                for name in rows:
                    hit = DETAIL_ROW.match(name)
                    out.append((float(hit.group(1).replace(",", "")), float(hit.group(2)))
                               if hit else None)

                return out

            was = pairs(before)
            is_now = pairs(after)

            bought, at = 100.0, 10.0
            buy_fee = fee_of({"Side": 0, "Price": at}, bought)
            sell_fee = fee_of({"Side": 1, "Price": at}, bought)

            idx = next((i for i, (code, _, _) in enumerate(book) if code.lower() == "sz300036"), None)
            want_cost = None

            if idx is not None and idx < len(was) and was[idx] is not None:
                shares, cost = was[idx]
                mid = ((shares * cost) + (bought * at) + buy_fee) / (shares + bought)
                want_cost = (((shares + bought) * mid) - ((bought * at) - sell_fee)) / shares

            others = [i for i in range(min(len(was), len(is_now)))
                      if i != idx and was[i] != is_now[i]]

            check("账本回到原样：股数不变，只有那一行的成本因手续费抬了一点",
                  idx is not None and len(was) == len(is_now) and not others
                  and was[idx][0] == is_now[idx][0]
                  and abs(is_now[idx][1] - want_cost) < 0.01,
                  "%d 行 → %d 行；超图 %s → %s（手续费算出来 %s）"
                  % (len(before), len(after), was[idx] if idx is not None else "?",
                     is_now[idx] if idx is not None else "?",
                     "%.4f" % want_cost if want_cost else "?"))

            if again is None or refetched is None:
                check("导入之后再取一次数", False,
                      "时间戳没换" if refetched is None else "读不到收益那句话")
            else:
                money = again.group(3)
                now = float(money.replace("¥", "").replace(",", "").replace("+", ""))

                # **抵平的是股数与现金进出，不是手续费。** 同一分钟、同价同量的一买一卖，
                # 现金进出一进一出相抵，但两笔的佣金与（卖出的）印花税是实打实付出的 ——
                # 所以收益要正好少这么一笔，而不是一分不差。原先判「回到原值」是费率还没
                # 进收益时的语义，加上费用之后它必然红，而红的是判据不是页面。
                two = fee_of({"Side": 0, "Price": 10.0}, 100) + fee_of({"Side": 1, "Price": 10.0}, 100)

                check("收益只少了那两笔的手续费（一买一卖抵平，费用如实扣掉）",
                      abs((guess["profit"] - now) - two) < 0.5,
                      "导入前 %+.2f / 导入后 %+.2f / 手续费 %.2f"
                      % (guess["profit"], now, two))

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

                # 等第二次导入自带的再取数完成再读列表 —— 与上一条同样的时序。
                wait_for_new(win, UPDATED, refetched, 180)

                # 与**第一趟导入之后**的那一版比，不是与导入之前：手续费已经落在成本里了。
                check("重复导入之后账本一字不变", sorted(book_rows(win)) == sorted(after))
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
