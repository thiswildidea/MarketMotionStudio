# -*- coding: utf-8 -*-
"""Render the Microsoft Store desktop screenshots.

The gallery cannot come out of a live capture run on this machine, so this
script draws the app window instead: the real layout (title bar, navigation
pane, the 9:16 dark preview canvas, the playback row and the parameter panel)
with the real interface strings read from the package's own resources, and a
synthetic but faithful chart inside the preview for each of the nine pages the
listing showcases.

Output: screenshots/<lang>/<stem>.png, 1920x1020 PNG, one set per language
(en-us, zh-hans, zh-hant); other regions fall back to en-us in Partner Center.

Run from the repo root:  python tools/render-store-screenshots.py
"""

import os
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESW = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")
OUT = os.path.join(ROOT, "screenshots")

W, H = 1920, 1020
NAV_W = 228
PANEL_X = 1490
CANVAS_W, CANVAS_H = 400, 711          # the 9:16 preview, as the window shows it
CX = (NAV_W + PANEL_X) // 2 - CANVAS_W // 2
CY = 150

# ---- palette ------------------------------------------------------------------

INK = "#161616"
GREY = "#616161"
LINE = "#e5e5e5"
NAV_BG = "#f6f6f6"
SEL_BG = "#e6e6e6"
ACCENT = "#0067c0"
OK_BG = "#eef7ee"
OK_TX = "#1a7f37"
DARK = "#0e1222"
UP = "#ef5350"      # Chinese convention: red is up
DOWN = "#26a269"    # green is down
GOLD = "#f2b544"
PURPLE = "#7c5cff"
BLUE = "#4f8cff"

# ---- fonts --------------------------------------------------------------------

FONTS = {
    "en-us":   ("segoeui.ttf", "segoeuib.ttf"),
    "zh-hans": ("msyh.ttc", "msyhbd.ttc"),
    "zh-hant": ("msjh.ttc", "msjhbd.ttc"),
}
_fcache = {}


def F(lang, size, bold=False):
    key = (lang, size, bold)
    if key not in _fcache:
        name = FONTS[lang][1 if bold else 0]
        _fcache[key] = ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", name),
                                          size)
    return _fcache[key]

# ---- strings ------------------------------------------------------------------

NAV_ITEMS = ["NavCandle", "NavStockVolume", "NavSectorRace", "NavMarketCap",
             "NavCapHistory", "NavAhPremium", "NavExtremeDays", "NavFxCorridor",
             "NavIndexRace", "NavAssetRace", "NavBondRace", "NavDrawdown",
             "NavHoldOdds", "NavMatrix", "NavGainCalendar", "NavDcaPlan"]


def resw(lang, key, default=""):
    """One value out of a language's Resources.resw, key with its suffix."""
    import re
    text = open(os.path.join(RESW, lang, "Resources.resw"),
                encoding="utf-8").read()
    m = re.search(r'<data name="%s"[^>]*>\s*<value>(.*?)</value>' % re.escape(key),
                  text, re.S)
    return m.group(1) if m else default


def strings(lang):
    s = {
        "app": resw(lang, "AppDisplayName", "Market Motion Studio"),
        "help": resw(lang, "NavHelp.Content", "Help"),
        "settings": resw(lang, "NavSettingsLabel.Text", "Settings"),
        "update": resw(lang, "UpdatePill.Content", "Update"),
        "data": resw(lang, "StudioDataSection.Text", "Data"),
        "range": resw(lang, "StudioRange.Header", "Date range"),
        "fetch": resw(lang, "StudioFetch.Content", "Get data"),
        "title_section": resw(lang, "StudioTitleSection.Text", "Title"),
        "title_text": resw(lang, "StudioTitleText.Header", "Title text"),
        "hide_title": resw(lang, "StudioHideTitle.Header", "Hide the title"),
        "nav": [resw(lang, k + ".Content", k) for k in NAV_ITEMS],
    }
    for page in PAGES:
        s[page + ".title"] = resw(lang, page + "PageTitle.Text", page)
        s[page + ".sub"] = resw(lang, page + "PageSubtitle.Text", "")
    return s

# ---- the nine pages -----------------------------------------------------------
# stem = screenshot file name; sel = which nav row is highlighted.

PAGES = ["MarketTurnover", "SectorRace", "GainCalendar", "Matrix", "DcaPlan",
         "Position", "Candle", "MarketCap", "BondRace"]

SHOTS = [
    ("01-market-turnover", "MarketTurnover", 15),
    ("02-sector-race", "SectorRace", 2),
    ("03-gain-calendar", "GainCalendar", 14),
    ("04-monthly-matrix", "Matrix", 13),
    ("05-dca-plan", "DcaPlan", 15),
    ("06-position", "Position", 16),
    ("07-candle", "Candle", 0),
    ("08-market-cap", "MarketCap", 3),
    ("09-bond-race", "BondRace", 10),
]

# Chart-internal copy, per page, per language. Values in the combos and the
# status line are authored (the real ones carry live numbers).
CHART = {
    "MarketTurnover": {
        "title": {"en-us": "A-share market turnover", "zh-hans": "A股市場成交額", "zh-hant": "A股市場成交額"},
        "value": {"en-us": "¥ 1,784.2 bn", "zh-hans": "¥ 17,842 億", "zh-hant": "¥ 17,842 億"},
        "status": {"en-us": "9,532 trading days (1990-12-19 to 2026-10-23) · record ¥ 3,421 bn on 2024-10-08",
                   "zh-hans": "9,532 个交易日（1990-12-19 至 2026-10-23）· 峰值 2024-10-08 ¥ 34,210 億",
                   "zh-hant": "9,532 個交易日（1990-12-19 至 2026-10-23）· 峰值 2024-10-08 ¥ 34,210 億"},
        "combo": {"en-us": "Whole market", "zh-hans": "全市场", "zh-hant": "全市場"},
    },
    "SectorRace": {
        "title": {"en-us": "US sector ETFs return race", "zh-hans": "美股行业 ETF 涨跌竞速", "zh-hant": "美股行業 ETF 漲跌競速"},
        "status": {"en-us": "10 sectors · 64 trading days · leading Energy +19.14% · last Utilities -8.90%",
                   "zh-hans": "10 个行业 · 64 个交易日 · 领先 能源 +19.14% · 垫底 公用事业 -8.90%",
                   "zh-hant": "10 個行業 · 64 個交易日 · 領先 能源 +19.14% · 墊底 公用事業 -8.90%"},
        "combo": {"en-us": "US sector ETFs", "zh-hans": "美股行业 ETF", "zh-hant": "美股行業 ETF"},
    },
    "GainCalendar": {
        "title": {"en-us": "SSE Composite gain calendar", "zh-hans": "上證指數漲跌日曆", "zh-hant": "上證指數漲跌日曆"},
        "status": {"en-us": "263 trading days in 2026 · 142 up, 116 down, 5 flat · best +4.81%",
                   "zh-hans": "2026 年 263 个交易日 · 142 涨 116 跌 5 平 · 最大 +4.81%",
                   "zh-hant": "2026 年 263 個交易日 · 142 漲 116 跌 5 平 · 最大 +4.81%"},
        "combo": {"en-us": "SSE Composite", "zh-hans": "上证指数", "zh-hant": "上證指數"},
    },
    "Matrix": {
        "title": {"en-us": "SSE Composite monthly returns", "zh-hans": "上證指數月度收益", "zh-hant": "上證指數月度收益"},
        "status": {"en-us": "10 years × 12 months · 2026 year to date +11.2% · best month +14.3%",
                   "zh-hans": "10 年 × 12 月 · 2026 年内 +11.2% · 最好月份 +14.3%",
                   "zh-hant": "10 年 × 12 月 · 2026 年內 +11.2% · 最好月份 +14.3%"},
        "combo": {"en-us": "SSE Composite", "zh-hans": "上证指数", "zh-hant": "上證指數"},
    },
    "DcaPlan": {
        "title": {"en-us": "DCA plan: Nasdaq-100 ETF", "zh-hans": "定投計劃：納指100 ETF", "zh-hant": "定投計劃：納指100 ETF"},
        "status": {"en-us": "1254 trading days (2021-10-11 to 2026-10-08), 1254 buys",
                   "zh-hans": "1254 个交易日（2021-10-11 至 2026-10-08），1254 次买入",
                   "zh-hant": "1254 個交易日（2021-10-11 至 2026-10-08），1254 次買入"},
        "combo": {"en-us": "Nasdaq-100 ETF", "zh-hans": "纳指100 ETF", "zh-hant": "納指100 ETF"},
    },
    "Position": {
        "title": {"en-us": "Position: 中国平安 2015", "zh-hans": "持倉收益：中國平安 2015", "zh-hant": "持倉收益：中國平安 2015"},
        "status": {"en-us": "Bought 2015-06-09 at ¥ 82.00 · mark-to-market ¥ 61.34 · worst drawdown -47.9%",
                   "zh-hans": "2015-06-09 以 ¥ 82.00 买入 · 现价 ¥ 61.34 · 最大回撤 -47.9%",
                   "zh-hant": "2015-06-09 以 ¥ 82.00 買入 · 現價 ¥ 61.34 · 最大回撤 -47.9%"},
        "combo": {"en-us": "601318 中国平安", "zh-hans": "601318 中国平安", "zh-hant": "601318 中國平安"},
    },
    "Candle": {
        "title": {"en-us": "贵州茅台 600519 — daily", "zh-hans": "贵州茅台 600519 — 日線", "zh-hant": "貴州茅台 600519 — 日線"},
        "status": {"en-us": "480 daily bars · last close ¥ 1,412.00 · 20-day MA ¥ 1,388.40",
                   "zh-hans": "480 根日K · 最新收盘 ¥ 1,412.00 · 20 日均线 ¥ 1,388.40",
                   "zh-hant": "480 根日K · 最新收盤 ¥ 1,412.00 · 20 日均線 ¥ 1,388.40"},
        "combo": {"en-us": "600519 贵州茅台", "zh-hans": "600519 贵州茅台", "zh-hant": "600519 貴州茅台"},
    },
    "MarketCap": {
        "title": {"en-us": "A-share market cap race", "zh-hans": "A股市場市值榜競速", "zh-hant": "A股市場市值榜競速"},
        "status": {"en-us": "15 companies · 2026-10-23 · 贵州茅台 leads at ¥ 1.77 tn",
                   "zh-hans": "15 家公司 · 2026-10-23 · 贵州茅台以 ¥ 1.77 万亿领先",
                   "zh-hant": "15 家公司 · 2026-10-23 · 貴州茅台以 ¥ 1.77 萬億領先"},
        "combo": {"en-us": "A-share · top 15", "zh-hans": "A股 · 前十五", "zh-hant": "A股 · 前十五"},
    },
    "BondRace": {
        "title": {"en-us": "Bond indices, price change", "zh-hans": "債市固收：價格變動", "zh-hant": "債市固收：價格變動"},
        "status": {"en-us": "8 bond indices · 1 year · aggregate price change +2.41%",
                   "zh-hans": "8 条债券指数 · 1 年 · 价格变动合计 +2.41%",
                   "zh-hant": "8 條債券指數 · 1 年 · 價格變動合計 +2.41%"},
        "combo": {"en-us": "China bond indices", "zh-hans": "中国债券指数", "zh-hant": "中國債券指數"},
    },
}

# ---- chrome -------------------------------------------------------------------


def rounded(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def draw_window(img, d, lang, s, sel_nav):
    d.rectangle([0, 0, W, H], fill="#ffffff")
    # title bar
    d.rectangle([0, 0, W, 42], fill="#ffffff")
    d.line([0, 42, W, 42], fill=LINE, width=1)
    for i, x in enumerate((16, 48)):
        d.line([x, 21, x + 10, 11], fill="#8a8a8a", width=2)
        d.line([x, 11, x + 10, 21], fill="#8a8a8a", width=2)
    rounded(d, [86, 11, 108, 33], 5, "#d94f43")
    d.text((120, 12), s["app"], font=F(lang, 12), fill=INK)
    for i, (x, g) in enumerate(((1782, "—"), (1828, "☐"), (1874, "✕"))):
        d.text((x, 10), g, font=F("en-us", 13), fill="#5a5a5a")

    # navigation pane
    d.rectangle([0, 42, NAV_W, H], fill=NAV_BG)
    d.line([NAV_W, 42, NAV_W, H], fill=LINE, width=1)
    for y in (74, 80, 86):
        d.line([24, y, 44, y], fill="#5a5a5a", width=2)
    y = 118
    row_h = 38
    for i, label in enumerate(s["nav"]):
        if i == sel_nav:
            rounded(d, [6, y - 5, NAV_W - 6, y + row_h - 9], 6, SEL_BG)
            rounded(d, [6, y - 5, 10, y + row_h - 9], 2, ACCENT)
        d.ellipse([28, y + 8, 40, y + 20], outline="#7a7a7a", width=2)
        d.text((56, y + 2), label, font=F(lang, 13), fill=INK)
        y += row_h
    y += 14
    for label in (s["help"], s["settings"]):
        d.ellipse([28, y + 8, 40, y + 20], outline="#7a7a7a", width=2)
        d.text((56, y + 2), label, font=F(lang, 13), fill=INK)
        y += row_h
    rounded(d, [148, y - 2, 218, y + 26], 4, ACCENT)
    d.text((157, y + 4), s["update"], font=F(lang, 12), fill="#ffffff")

    # parameter panel
    d.line([PANEL_X, 42, PANEL_X, H], fill=LINE, width=1)
    x = PANEL_X + 30
    w = 360
    d.text((x, 78), s["data"], font=F(lang, 14, True), fill=INK)
    d.text((x, 112), CHART_PAGE["combo"][lang], font=F(lang, 11), fill=GREY)
    combo(d, x, 132, w)
    d.text((x, 186), s["range"], font=F(lang, 11), fill=GREY)
    combo(d, x, 206, w)
    rounded(d, [x, 258, x + w, 292], 4, "#ffffff", "#c9c9c9")
    d.text((x + w // 2 - d.textlength(s["fetch"], font=F(lang, 13)) // 2, 266),
           s["fetch"], font=F(lang, 13), fill=INK)
    d.text((x, 322), s["title_section"], font=F(lang, 14, True), fill=INK)
    d.text((x, 352), s["title_text"], font=F(lang, 11), fill=GREY)
    rounded(d, [x, 372, x + w, 446], 4, "#ffffff", "#c9c9c9")
    rounded(d, [x, 470, x + 40, 490], 10, "#cccccc")
    d.ellipse([x + 20, 470, x + 40, 490], fill="#ffffff")
    d.text((x + 52, 471), s["hide_title"], font=F(lang, 11), fill=GREY)


def combo(d, x, y, w):
    rounded(d, [x, y, x + w, y + 32], 4, "#ffffff", "#c9c9c9")
    d.line([x + w - 20, y + 14, x + w - 14, y + 20], fill="#5a5a5a", width=2)
    d.line([x + w - 14, y + 20, x + w - 8, y + 14], fill="#5a5a5a", width=2)


def draw_bottom(img, d, lang, s, page):
    # playback row
    d.ellipse([NAV_W + 34, 868, NAV_W + 66, 900], outline="#5a5a5a", width=2)
    d.polygon([(NAV_W + 48, 876), (NAV_W + 48, 892), (NAV_W + 62, 884)], fill="#5a5a5a")
    d.rounded_rectangle([NAV_W + 82, 880, 1380, 888], 4, "#d9d9d9")
    d.rounded_rectangle([NAV_W + 82, 880, 1180, 888], 4, ACCENT)
    d.ellipse([1172, 872, 1188, 896], fill=ACCENT)
    d.text((1395, 876), "1:30 / 1:30", font=F("en-us", 12), fill=GREY)
    # status bar (the check is drawn, not typed — no glyph dependency)
    rounded(d, [NAV_W + 30, 916, 1480, 958], 6, OK_BG)
    d.line([NAV_W + 46, 937, NAV_W + 52, 944], fill=OK_TX, width=2)
    d.line([NAV_W + 52, 944, NAV_W + 63, 928], fill=OK_TX, width=2)
    d.text((NAV_W + 74, 928), CHART[page]["status"][lang], font=F(lang, 12), fill=OK_TX)
    d.text((1452, 926), "×", font=F("en-us", 14), fill="#8a8a8a")


# ---- the nine charts ----------------------------------------------------------


def canvas_base(d):
    rounded(d, [CX, CY, CX + CANVAS_W, CY + CANVAS_H], 6, DARK)


def chart_title(d, lang, page, sub=""):
    t = CHART[page]["title"][lang]
    f = F(lang, 17, True)
    d.text((CX + (CANVAS_W - d.textlength(t, font=f)) // 2, CY + 22), t,
           font=f, fill="#ffffff")
    if sub:
        f2 = F(lang, 9)
        d.text((CX + (CANVAS_W - d.textlength(sub, font=f2)) // 2, CY + 52), sub,
               font=f2, fill="#9aa3c0")


def date_chip(d, lang, text, y):
    f = F(lang, 15, True)
    d.text((CX + (CANVAS_W - d.textlength(text, font=f)) // 2, y), text,
           font=f, fill=GOLD)


def chart_turnover(d, lang):
    chart_title(d, lang, "MarketTurnover", "whole market · daily")
    date_chip(d, lang, "2026-10-08", CY + 92)
    rnd = random.Random(7)
    base = CY + 640
    x = CX + 26
    for i in range(80):
        h = 60 + 300 * (i / 79.0) ** 1.6 + rnd.randint(-40, 60)
        h = max(24, min(h, 500))
        up = rnd.random() < 0.54
        d.rectangle([x, base - h, x + 3, base], fill=UP if up else DOWN)
        x += 4.4
    d.line([CX + 22, base + 1, CX + CANVAS_W - 22, base + 1], fill="#2a3152", width=1)
    d.text((CX + 24, base + 12), "1990", font=F("en-us", 9), fill="#9aa3c0")
    t = "2026"
    d.text((CX + CANVAS_W - 22 - d.textlength(t, font=F("en-us", 9)), base + 12),
           t, font=F("en-us", 9), fill="#9aa3c0")


SECTORS_EN = ["Energy", "Technology", "Health Care", "Consumer Staples",
              "Financials", "Materials", "Industrials", "Real Estate", "Utilities"]
SECTORS_ZH = ["能源", "科技", "医疗保健", "必需消费", "金融", "原材料", "工业", "房地产", "公用事业"]
SECTOR_VALS = [19.14, 6.58, 4.95, -0.18, 2.32, -2.74, 4.51, 7.18, 2.33, -4.80]


def chart_sector(d, lang):
    chart_title(d, lang, "SectorRace", "10 ETFs · cumulative return")
    date_chip(d, lang, "2026-10-08", CY + 92)
    labels = SECTORS_ZH if lang.startswith("zh") else SECTORS_EN
    x0, x1 = CX + 112, CX + CANVAS_W - 20
    track = x1 - x0 - 58            # room for the value label at the bar's end
    top = max(abs(v) for v in SECTOR_VALS)
    y = CY + 150
    for i, v in enumerate(SECTOR_VALS):
        w = max(abs(v) / top * track, 4)
        color = PURPLE if i == 0 else (UP if v >= 0 else DOWN)
        rounded(d, [x0, y, x0 + w, y + 20], 3, color)
        d.text((x0 + w + 6, y + 3), "%+.2f%%" % v, font=F("en-us", 10, True), fill=color)
        lbl = labels[i] if i < len(labels) else ""
        d.text((x0 - 10 - d.textlength(lbl, font=F(lang, 9)), y + 4), lbl,
               font=F(lang, 9), fill="#c7cde4")
        y += 47


def chart_calendar(d, lang):
    chart_title(d, lang, "GainCalendar", "2026 · one cell a day")
    rnd = random.Random(3)
    cols, rows = 14, 18
    cw, chh, gap = 22, 22, 3
    x0 = CX + (CANVAS_W - (cols * (cw + gap) - gap)) // 2
    y0 = CY + 112
    for r in range(rows):
        for c in range(cols):
            if rnd.random() < 0.08:
                continue
            col = UP if rnd.random() < 0.55 else DOWN
            shade = 0.35 + 0.65 * rnd.random()
            d.rectangle([x0 + c * (cw + gap), y0 + r * (chh + gap),
                         x0 + c * (cw + gap) + cw, y0 + r * (chh + gap) + chh],
                        fill=_mix(col, shade))


def _mix(hexcolor, k):
    r = int(hexcolor[1:3], 16) * k
    g = int(hexcolor[3:5], 16) * k
    b = int(hexcolor[5:7], 16) * k
    return "#%02x%02x%02x" % (int(r), int(g), int(b))


MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def chart_matrix(d, lang):
    chart_title(d, lang, "Matrix", "year × month")
    rnd = random.Random(11)
    years = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
    x0 = CX + 46
    y0 = CY + 116
    cw, chh = 26, 34
    for c, m in enumerate(MONTHS):
        d.text((x0 + c * (cw + 3) + 9, y0 - 16), m, font=F("en-us", 9), fill="#9aa3c0")
    for r, yr in enumerate(years):
        d.text((x0 - 34, y0 + r * (chh + 3) + 9), yr, font=F("en-us", 9), fill="#9aa3c0")
        for c in range(12):
            v = rnd.uniform(-1, 1)
            col = UP if v > 0 else DOWN
            shade = 0.25 + 0.75 * abs(v)
            d.rectangle([x0 + c * (cw + 3), y0 + r * (chh + 3),
                         x0 + c * (cw + 3) + cw, y0 + r * (chh + 3) + chh],
                        fill=_mix(col, shade))


def _poly(d, pts, color, width=3):
    d.line(pts, fill=color, width=width, joint="curve")


def chart_dca(d, lang):
    chart_title(d, lang, "DcaPlan", "100/day · every trading day")
    date_chip(d, lang, "2026-10-08", CY + 84)
    big = "+81.3%"
    f = F(lang, 34, True)
    d.text((CX + (CANVAS_W - d.textlength(big, font=f)) // 2, CY + 122), big,
           font=f, fill=UP)
    d.text((CX + (CANVAS_W - d.textlength("Return", font=F("en-us", 9))) // 2, CY + 168),
           "Return", font=F("en-us", 9), fill="#9aa3c0")
    rnd = random.Random(5)
    x0, x1 = CX + 36, CX + CANVAS_W - 30
    yb, yt = CY + 420, CY + 220
    pts_v, pts_i = [], []
    v = 0.0
    for i in range(60):
        v += rnd.uniform(-0.8, 1.15) + i * 0.012
        x = x0 + i * (x1 - x0) / 59
        pts_v.append((x, yb - (v + 6) * (yb - yt) / 22))
        pts_i.append((x, yb - i * (yb - yt) / 59 * 0.55))
    _poly(d, pts_i, "#8a91ad", 2)
    _poly(d, pts_v, UP)
    badge = "+81.3%"
    d.text((x1 - 58, yt - 16), badge, font=F("en-us", 9, True), fill=GOLD)
    chips = {"en-us": ["Final value 227.4K", "Total in 125.4K", "Total P&L +102K", "Buys 1,254"],
             "zh-hans": ["期末价值 227.4K", "总投入 125.4K", "总损益 +102K", "买入 1,254"],
             "zh-hant": ["期末價值 227.4K", "總投入 125.4K", "總損益 +102K", "買入 1,254"]}[lang]
    cw = (CANVAS_W - 60 - 18) // 4
    for i, t in enumerate(chips):
        x = CX + 30 + i * (cw + 6)
        rounded(d, [x, CY + 590, x + cw, CY + 640], 4, "#1a2138")
        d.text((x + 8, CY + 596), t.split()[0], font=F(lang, 8), fill="#9aa3c0")
        d.text((x + 8, CY + 612), " ".join(t.split()[1:]), font=F(lang, 11, True),
               fill="#ffffff" if i < 2 else (UP if "+" in t else "#ffffff"))


def chart_position(d, lang):
    chart_title(d, lang, "Position", "¥1,000,000 · 2015-06-09")
    rnd = random.Random(9)
    x0, x1 = CX + 36, CX + CANVAS_W - 30
    yb, yt = CY + 620, CY + 240
    vals, v = [], 0.0
    for i in range(90):
        v += rnd.uniform(-1.1, 1.05) - (2.2 if 18 < i < 40 else 0)
        vals.append(v)
    lo, hi = min(vals), max(vals)
    span = max(hi - lo, 1.0)
    pts = [(x0 + i * (x1 - x0) / 89, yb - (vals[i] - lo) / span * (yb - yt))
           for i in range(90)]
    d.polygon(pts + [(x1, yb), (x0, yb)], fill=_mix(PURPLE, 0.25))
    _poly(d, pts, PURPLE)
    lab = "¥ 613.4K  -38.7%"
    lx, ly = pts[-1]
    rounded(d, [int(lx) - 124, int(ly) - 26, int(lx) - 6, int(ly) - 4], 3, "#1a2138")
    d.text((int(lx) - 116, int(ly) - 23), lab, font=F("en-us", 9, True), fill=GOLD)
    dd = "-47.9%"
    rounded(d, [CX + 46, CY + 110, CX + 130, CY + 134], 4, "#2a1420")
    d.text((CX + 56, CY + 113), dd, font=F("en-us", 11, True), fill=UP)


def chart_candle(d, lang):
    chart_title(d, lang, "Candle", "daily · MA20 · volume")
    date_chip(d, lang, "2026-10-23", CY + 84)
    rnd = random.Random(13)
    x0, x1 = CX + 30, CX + CANVAS_W - 30
    yb, yt = CY + 430, CY + 130
    n = 44
    step = (x1 - x0) / n
    v, bars = 0.0, []
    for i in range(n):
        o = v
        v += rnd.uniform(-1.4, 1.5)
        c = v
        bars.append((o, c, max(o, c) + rnd.uniform(0, 0.5),
                     min(o, c) - rnd.uniform(0, 0.5)))
    lo = min(b[3] for b in bars)
    hi = max(b[2] for b in bars)
    span = max(hi - lo, 1.0)

    def y(p):
        return yb - (p - lo) / span * (yb - yt)

    for i, (o, c, h, l) in enumerate(bars):
        x = x0 + i * step
        col = UP if c >= o else DOWN
        d.line([x + step / 2, y(h), x + step / 2, y(l)], fill=col, width=1)
        top, bot = sorted((y(o), y(c)))
        d.rectangle([x + 1, top, x + step - 2, max(bot, top + 2)], fill=col)
    closes = [b[1] for b in bars]
    pts = [(x0 + i * step + step / 2, y(sum(closes[max(0, i - 7):i + 1]) /
                                         len(closes[max(0, i - 7):i + 1])))
           for i in range(n)]
    _poly(d, pts, GOLD, 2)
    vy = CY + 580
    x = x0
    for i in range(n):
        h = rnd.randint(10, 78)
        d.rectangle([x, vy - h, x + step - 2, vy],
                    fill=_mix(UP if closes[i] >= bars[i][0] else DOWN, 0.6))
        x += step


CAPS_EN = [("Kweichow Moutai", 1.77), ("ICBC", 1.62), ("Agricultural Bank", 1.48),
           ("China Mobile", 1.31), ("PetroChina", 1.24), ("CNOOC", 1.02),
           ("China Merchants Bank", 0.96), ("Sinopec", 0.71)]
CAPS_ZH = [("贵州茅台", 1.77), ("工商银行", 1.62), ("农业银行", 1.48), ("中国移动", 1.31),
           ("中国石油", 1.24), ("中国海油", 1.02), ("招商银行", 0.96), ("中国石化", 0.71)]


def chart_marketcap(d, lang):
    chart_title(d, lang, "MarketCap", "top 15 · total market value")
    date_chip(d, lang, "2026-10-23", CY + 92)
    rows = CAPS_ZH if lang.startswith("zh") else CAPS_EN
    x0 = CX + 118
    x1 = CX + CANVAS_W - 60
    y = CY + 150
    for name, cap in rows:
        w = cap / 1.77 * (x1 - x0)
        color = GOLD if cap == 1.77 else BLUE
        rounded(d, [x0, y, x0 + w, y + 20], 3, color)
        d.text((x0 - 8 - d.textlength(name, font=F(lang, 9)), y + 4), name,
               font=F(lang, 9), fill="#c7cde4")
        d.text((x0 + w + 6, y + 4), "¥%.2f tn" % cap, font=F("en-us", 9), fill="#c7cde4")
        y += 44


BONDS_EN = [("CGB 1Y", 1.02), ("CGB 3Y", 1.84), ("CGB 5Y", 2.10), ("CGB 10Y", 2.41),
            ("CDB 5Y", 1.96), ("CDB 10Y", 2.28), ("IRS 1Y", 0.88), ("Local 5Y", 1.72)]
BONDS_ZH = [("国债 1年", 1.02), ("国债 3年", 1.84), ("国债 5年", 2.10), ("国债 10年", 2.41),
            ("国开 5年", 1.96), ("国开 10年", 2.28), ("互换 1年", 0.88), ("地方债 5年", 1.72)]


def chart_bond(d, lang):
    chart_title(d, lang, "BondRace", "price change · 1 year")
    date_chip(d, lang, "2026-10-23", CY + 92)
    rows = BONDS_ZH if lang.startswith("zh") else BONDS_EN
    x0 = CX + 108
    x1 = CX + CANVAS_W - 66
    y = CY + 150
    for name, v in rows:
        w = v / 2.41 * (x1 - x0)
        rounded(d, [x0, y, x0 + max(w, 4), y + 16], 3, DOWN)
        d.text((x0 - 8 - d.textlength(name, font=F(lang, 9)), y + 2), name,
               font=F(lang, 9), fill="#c7cde4")
        d.text((x0 + max(w, 4) + 6, y + 2), "+%.2f%%" % v, font=F("en-us", 9),
               fill=DOWN)
        y += 46


CHART_FN = {
    "MarketTurnover": chart_turnover,
    "SectorRace": chart_sector,
    "GainCalendar": chart_calendar,
    "Matrix": chart_matrix,
    "DcaPlan": chart_dca,
    "Position": chart_position,
    "Candle": chart_candle,
    "MarketCap": chart_marketcap,
    "BondRace": chart_bond,
}

# ---- one frame ----------------------------------------------------------------


def render(lang, stem, page, sel_nav):
    s = strings(lang)
    global CHART_PAGE
    CHART_PAGE = CHART[page]
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)
    draw_window(img, d, lang, s, sel_nav)
    d.text((NAV_W + 28, 62), s[page + ".title"], font=F(lang, 26, True), fill=INK)
    d.text((NAV_W + 28, 108), s[page + ".sub"], font=F(lang, 12), fill=GREY)
    canvas_base(d)
    CHART_FN[page](d, lang)
    draw_bottom(img, d, lang, s, page)
    out_dir = os.path.join(OUT, lang)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, stem + ".png")
    img.save(path)
    return path


def main():
    made = []
    for lang in ("en-us", "zh-hans", "zh-hant"):
        for stem, page, sel in SHOTS:
            made.append(render(lang, stem, page, sel))
    for p in made:
        print(p)


if __name__ == "__main__":
    main()
