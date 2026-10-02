# 版本记录 / Changelog

Each version sent to the Store gets one entry here: its number, its date, and what is new in it.
**Releasing is three actions that belong together** — bump `Version` in
`src/MarketMotionStudio/Package.appxmanifest`, add an entry below, and update the
"What's new in this version" line in the store listing. Skipping the middle one is how a
version ends up with no record of what it changed.

每个上架版本在这里留一条：版本号、日期、本版新增。**发版是三个绑定的动作**——改
`Package.appxmanifest` 的 `Version`、在这里加一条、同步商店文案的「此版本的新增功能」。
少做第二步，这个版本就再也说不清自己改了什么。

Two rules decide the number itself (full text in NOTES.md under "Version numbering"): the
fourth section stays 0, and the first cannot be 0. An update must also be higher than the
version already published, or nobody is offered it.
版本号怎么定（详见 NOTES.md 的 "Version numbering"）：第四段恒为 0，第一段不能为 0；
且必须高于已发布版本，否则用户根本收不到更新。

Entries run newest first. / 新版本在上。

---

## 1.0.4.0 — 2026-10-02（更新版 / update）

本版的文案已经写好、版本号已经升上，**包尚未构建上传**——等发版时再构建。
The copy for this version is written and the number is bumped; **the package has not been built
or uploaded yet** — that happens when it is released.

### 新增 / Added

- **十六个页面各有各的图标 / an icon drawn for each of the sixteen pages** — 导航里原先有
  **三对页面共用同一个系统字形**：K线与行业板块竞速（`E9E9`）、成交量换手率与持有胜率（`E9D2`）、
  市场成交额与持仓收益（`E9D9`）。一个形状说不了两个页面，而 Segoe Fluent Icons 里能用的字形
  就那么多，页面长大了装不下。现在十六幅都是画出来的：20×20 网格上的描边骨架（线、圆环、折线、
  箭头）由 shapely 外扩求并成填充几何，落在 `Themes/Icons.xaml`，跟随深浅主题变色，包里不加
  任何位图。每幅图都带两个定位点把包围盒钉成 `[2,18]²`——`PathIcon` 按包围盒等比缩放，没有它们
  宽扁的会被撑高、瘦高的会被压扁。帮助与设置保留系统字形：问号和齿轮是这套菜单里唯一从来没有
  歧义的两个。
  Three pairs of pages had been sharing one system glyph: Candles with Sector Race (`E9E9`),
  Volume & Turnover with Hold Odds (`E9D2`), Market Turnover with Position Replay (`E9D9`). One
  shape cannot mean two pages, and there are only so many usable glyphs in Segoe Fluent Icons.
  All sixteen are drawn instead: a stroke skeleton on a 20×20 grid — lines, rings, polylines,
  arrowheads — expanded and unioned by shapely into the filled geometry a `PathIcon` needs, kept in
  `Themes/Icons.xaml`, taking its colour from the light or dark theme and adding no bitmap to the
  package. Each drawing carries two registration marks that pin its bounding box to `[2,18]²`,
  because `PathIcon` scales by bounding box and, without them, a wide icon is stretched tall and a
  tall one squashed flat. Help and settings keep their glyphs: a question mark and a gear are the
  two shapes in this menu that were never ambiguous.
- **四页的区间按接口实测重定 / four range menus, re-cut against what the endpoints return** —
  实测发现 `count` 是**根数不是天数**，源端从结束日往回数、忽略起始日：要 365 天回 365 根、要 640
  回 640、要 1825 仍然只有 640 根。所以超长区间丢的是**头部**，回来的图短一截却完全正常——这正是
  区间最不该给出的答案。据此：K线日线加了 **5 年与 10 年**两档（日线走分页，6 × 640 = 3840 根，
  约 15 年；实测十年是 2462 根）；成交量换手率与行业板块竞速加了 **24 个月**一档，自定义区间的
  上限从 640 天改到 **900 天**（旧阈值会把源端答得出来的两年拦下），日期选择器同步收窄；市值榜
  加了「**最长**」与「**自定义**」，它的天花板是月线自己的 180 个月，而不是按日线算出来的三十五年。
  新增 `TencentKline.MostDaysPerRequest = 900`（天），与既有的 `MostBarsPerRequest = 640`（根）
  分开——拿根数去挡天数会拦下源端答得出来的区间。
  Measured: `count` is a number of **bars**, not of days, and the source counts backwards from the
  end date, ignoring the start — ask for 365 days and 365 bars come back, ask for 640 and 640 come
  back, ask for 1825 and it is still 640. So a span past the ceiling loses its **head**, and a
  chart with its first years missing is a shorter chart that looks entirely correct, which is the
  one answer a span must not give. Accordingly: daily candles gained **5 and 10 years** (daily
  pages backwards, 6 × 640 = 3840 bars, about fifteen years; ten years measured at 2,462 bars);
  Volume & Turnover and Sector Race gained **24 months**, and the ceiling on a custom span went
  from 640 to **900 days** — the old one refused two years the source answers happily — with the
  date pickers narrowed to match; Market Cap Race gained **Longest** and **Custom**, its ceiling
  being the monthly series' own 180 periods rather than the thirty-five years a daily walk would
  suggest. `TencentKline.MostDaysPerRequest = 900` (days) now sits beside `MostBarsPerRequest =
  640` (bars): using a bar count to police a number of days refuses spans the source will answer.

### 改进 / Changed

- **帮助手册 14 份补上了本版的口径 / the manual now says what the menus do** — K线、成交量换手率、
  市值榜三章各多一句本页的档位；「数据，以及它不会告诉你的事」里那条「超过约 640 个自然日会被
  拒绝」改成按页分档的说法，并写明为什么不能悄悄截断。改动由 `tools/port-help-ranges.py` 按
  **章节位置**注入（14 种语言里"第 N 章的最后一条 bullet"都是同一处，而按句子匹配要写 14 份正则）。
  The Candles, Volume and Market Cap chapters each gained a line about that page's entries, and the
  "longer than about 640 calendar days is refused" line in the data chapter now states the ceiling
  per page and why nothing is quietly truncated. `tools/port-help-ranges.py` injects them by
  **chapter position** — "the last bullet of chapter N" is the same place in all fourteen
  languages, where matching a sentence means fourteen patterns.
- **商店文案从十页补到十六页 / the store listing stopped saying ten pages** — 说明段还写着「十大
  图表页」，而后加的六页（极端交易日、汇率走廊、指数长跑、大类资产、回撤与修复、持有胜率）从来
  没进过商店文案。现在补上了，描述**取自各语言帮助手册那一章的首句**（那是项目自己翻的、与界面
  一致的说法），页面名取自 resw，破折号抄这一段自己已有的那一条（德语那段用的是短破折号）。
  十四条「此版本的新增功能」改写为本版内容——它们此前还在一页一页地数「新增第八个图表页」，与
  「十六大图表页」并排是自相矛盾的；历史留在 CHANGELOG 里。
  The description still said "Ten chart pages" while the six pages added since — extreme days,
  currency corridors, index race, asset classes, drawdowns, hold odds — had never made it into the
  copy. They are in now, each described by **the first sentence of that chapter in the same
  language's manual** (the project's own translation, the same words the UI uses), named from resw,
  and dashed with whatever that section already uses (the German one writes an en dash). The
  fourteen "What's new" lines were rewritten for this version: they were still counting "an eighth
  chart page", which contradicts "Sixteen chart pages" sitting above it. The history lives here.

### 已知限制 / Known limits（沿用 1.0.3.0 / unchanged from 1.0.3.0）

- 图标只换在导航里：设置与帮助仍是系统字形（问号与齿轮），工具条上的字形也没有重画。
  The new icons are in the navigation only; Settings and Help keep their glyphs, and the toolbar's
  glyphs were not redrawn.
- 成交量换手率与行业板块竞速的日线区间上限仍是约 900 个自然日，一次请求的天花板就到那里。
  The daily ceiling on Volume & Turnover and Sector Race is still about 900 calendar days, which is
  where one request stops.
- 美股没有日内模式（那个分时端点的 `data` 是 list 不是 object），日内只有最近几个交易日可选。
  There is no intraday mode on the United States (that endpoint returns a list, not an object), and
  intraday offers only the last few trading days.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份改写为本版
的两个改动（图标、区间）；同一份文件里「说明」的图表页数与「产品功能」的图表条数从十改成十六，
说明段补上六条。三处各由一个脚本按语言改（`tools/port-store-listing-pages.py`、
`tools/port-store-listing-whatsnew.py`），幂等，且按整行精确匹配——某语言的措辞与脚本里的不一致
时会报错而不是留下一个旧数字。这两个文件都是 CRLF，脚本读写都保持原样。
The fourteen "What's new" lines now describe this version's two changes — the icons and the ranges;
the description's page count and the features bullet went from ten to sixteen, with six entries
added to the list. A script per edit does it per language
(`tools/port-store-listing-pages.py`, `tools/port-store-listing-whatsnew.py`), idempotent and
matching whole lines, so a language whose wording differs fails loudly instead of keeping a stale
number. Both files are CRLF and the scripts keep them that way.

---

## 1.0.3.0 — 2026-10-01（更新版 / update）

**1.0.2.0 那一版只构建成包、从未上传商店**，所以它写下的内容（页面导航、三个市场的复权口径等）
是随本版一起到达用户的。下面只列本版在 1.0.2.0 之上新增的改动。应用的完整能力仍见下面的
0.0.0.0 条目。
Version 1.0.2.0 was built but never uploaded, so what its entry describes — page navigation, the
adjustment basis across the three markets — reaches users as part of this one. What follows is only
what this version adds on top of it. The full feature set is still in the 0.0.0.0 entry below.

### 新增 / Added

- **第八页：K线走势 / an eighth page: Candles** — 一只标的的价格画成 K 线，日线 / 周线 / 月线
  任选，四种画法（蜡烛、美国线、收盘线、面积），带 MA5/10/20 均线与成交量副图；区间的涨跌幅和
  最高、最低点标在画面上。动画有两种且可切换：**逐根生长**——从区间第一根长到最后一根；
  **固定窗口滚动**——窗口宽度固定，画面带着一段行情向前走。指数、个股、ETF 都能画，三个市场
  都支持。它在导航里排在「市场成交额」正下方，与帮助手册里的顺序一致。
  One instrument's prices as candles, daily, weekly or monthly, drawn four ways — candles, OHLC
  bars, a closing line, a closing area — with MA5/10/20 averages and a volume panel beneath, the
  range's return and its high and low marked on the frame. Two animations, switchable: **growing**,
  one candle at a time from the range's first to its last, and **scrolling**, a fixed-width window
  walking forward through the range. Indices, stocks and ETFs all draw, on all three markets. It
  sits directly under Market Turnover in the navigation, which is where the manual puts it.
- **自定义数据区间 / a custom span, on three pages** — K线走势、定投计划、持仓收益的区间下拉
  都多了一档「自定义」：选它就露出起始日期与结束日期两个框，取回来的就是这两个日期之间的行情。
  此前定投与持仓只能选区间长度（3 / 5 / 10 年 / 最长），K线页则完全没有这一档。两个日期的可选
  范围不是随手定的：这三个页面都要把日线一段一段往回翻，一页约 640 个自然日，能翻多少次是定
  死的，所以日期框的上限就钉在那条线上（K线页约 10 年，定投与持仓约 35 年）。超出上限会在发
  请求之前就拒绝——再往前，回溯会在走到你要的起点之前先用完请求次数，序列会悄悄从更晚的一天
  开始，而填两个日期的全部意义就是那天是那天。起始日期晚于结束日期同样在发请求前拒绝：否则源
  端只会含糊地说「天数太少」，而画面里上一次那条曲线还站在两个它从没走过的日期底下。
  Candles, the DCA plan and the position replay each gained a **Custom** entry in their range
  dropdown: pick it and two date boxes appear, a start and an end, and the fetch returns exactly
  what lies between them. The plan and the position could only take a length before — three, five
  or ten years, or as far back as there is — and the candle page had no such entry at all. The
  range the boxes offer is not arbitrary: all three pages walk daily bars backwards a page at a
  time, about 640 calendar days to a page, with a fixed ceiling on requests, so the boxes stop
  where the walk stops (roughly ten years on the candle page, thirty-five on the other two). Asking
  for more is refused before any request goes out — past that line the walk runs out of requests
  before it reaches the day you asked for, and the series quietly starts later, while the whole
  point of typing two dates is that the day is the day. A start later than the end is refused for
  the same reason: otherwise the source answers something vague about too few days, and the
  previous curve is left standing under two dates it never visited.

### 改进 / Changed

- **动画背景的颜色档有了不透明度 / an opacity for a colour backdrop** — 选「颜色」时两个色标
  下面多一条滑条（20–100，默认 100）：100% 就是所选的两个颜色本身，往低调会从底下透出这一页
  原本的深色渐变。方向故意与图片档那条相反：图片带着自己的配色来，需要被压回去（浓度越高越接近
  默认底）；颜色是你选的，要决定的是用多少。两条各自只在自己的类型下出现。
  A colour backdrop gained a slider under its two swatches, 20–100 with 100 the default: at 100 the
  frame is the two colours you picked, and turning it down lets the page's own dark gradient show
  through from beneath. Deliberately the opposite direction from the picture's slider — a picture
  arrives with its own colouring and has to be pushed back, while a colour is yours and the question
  is how much of it to use. Each appears only under its own kind.
- **颜色改动在设置页就有回应 / a colour change answers on the page it was made** — 两个取色器下面
  多了一条 40 像素的渐变条，画的就是这一页会被填成的样子（底＝默认渐变，上＝所选色按不透明度），
  改颜色或拖滑条时它跟着变。此前唯一的反馈是下拉里那个 18 像素的色块，而画面在另一个页面上，
  于是「刚才那一下有没有生效」在选颜色的那一页上没有答案。
  A forty-pixel bar under the two pickers draws what the frame will be filled with — the page's
  default gradient beneath, the chosen colours over it at their opacity — and follows both the
  colours and the slider. The only feedback before was an eighteen-pixel swatch in each dropdown,
  with the frame itself on another page, so "did that do anything" had no answer where the colour
  was chosen.
- **上边距的最小值从 230 放宽到 40 / the top margin's floor is 40 now** — 默认仍是 230（手机
  状态栏遮住的那 0.12 帧高就是 230 基线像素，低于它标题会被压到状态栏底下），但最小值此前也是
  230，等于这个滑块只能往上、不能往下。现在可以收到 40。
  The default is still 230 — the 0.12 of the frame a phone's own interface covers, below which a
  top margin can only slide the title under the status bar — but the minimum was 230 too, so the
  slider could only ever go up. It now goes down to 40.

### 修复 / Fixed

- **K线表头的四价行压住了日期行 / the candle header's quote row sat on its date** — 表头四行
  （标题、副标题、日期、开高低收）里，四价那一行还硬写着上一版留下来的一个裸数字，加上大数字的
  发光会向外糊约 25 像素，压到了下面一行。四行现在是命名常量，按发光半径重排。
  Of the header's four rows — title, subtitle, date, open/high/low/close — the quote row still
  carried a bare number left over from an earlier pass, and the glow behind the large figures
  blurs about twenty-five pixels outward, so it sat on the row beneath. The four rows are named
  constants now, spaced with the glow's radius in mind.
- **日期行没有落在两行中间 / the date was not centred between its neighbours** — 按基线取中点仍
  差 4 像素：中文副标题挂在基线下方 4 像素，四价行的中文标签又有 22 像素高。居中现在按**墨迹**
  算而不是按基线，实测上下间隙各 42.2 像素。成交额、定投、持仓三页的同一行同此改法。
  Taking the midpoint of the two baselines was still four pixels out: a CJK subtitle hangs four
  pixels below its baseline and the quote row's CJK labels are twenty-two tall. Centring is
  measured on the ink now rather than on the baseline — 42.2 pixels of clear space above and below.
  The same row on the turnover, plan and position pages was corrected the same way.
- **美股代码大小写导致取不到数据，标题还写错 / a US code in the wrong case fetched nothing, and
  the title was wrong** — 搜索端点返回小写 `usaapl.oq`，而 K 线端点只认 `usAAPL.OQ`，对小写返回
  **空数据而不是报错**，看起来像一只没有历史的标的；标题则直接把代码大写印成 `USAAPL`。代码现在
  在第一次拿到时就按市场规范化，画面上的名字用端点随行情一起返回的那个。
  The search endpoint answers in lower case (`usaapl.oq`) while the candle endpoint will only read
  `usAAPL.OQ` — and answers a lower-case code with *no data* rather than an error, which reads as an
  instrument with no history. The title printed the code upper-cased as `USAAPL`. A code is
  canonicalised for its market as soon as it is known, and the name the frame shows is the one the
  endpoint returns alongside the series.

### 已知限制 / Known limits（沿用 1.0.2.0，本版未变 / unchanged from 1.0.2.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.
- 商店截图仍是七个页面，K线走势页的截图尚未拍摄。
  The Store screenshots still show seven pages; the candle page has not been captured yet.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：K线走势页、三页的自定义区间、颜色档的不透明度、上边距放宽，以及两处修复。同一份文件
里「说明」的图表页数与「产品功能」的图表条数也跟着从七改成八。
之前这些改动是手写到 14 份里的，本版起由一个脚本（`tools/port-store-listing.py`）按语言改，
幂等，且每处都按整行精确匹配——某语言的措辞与脚本里的不一致时会报错而不是留下一个旧数字。
The fourteen "What's new in this version" lines now describe only this release: the candle page,
the custom span on three pages, opacity for a colour backdrop, the relaxed top margin, and two
fixes. The description's page count and the features bullet in the same file moved from seven to
eight. These edits used to be made by hand in fourteen places; from this version a script does it
(`tools/port-store-listing.py`), idempotent and matching whole lines, so a language whose wording
differs fails loudly instead of keeping a stale number.

---

## 1.0.2.0 — 2026-10-01（更新版 / update）

**本版只构建成包、未上传商店；内容随 1.0.3.0 一起发布。**
Built but never uploaded; its contents shipped with 1.0.3.0.

**1.0.1.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的 0.0.0.0 条目——
那一版已发布，这里不重复。
The first update after 1.0.1.0; only the changes are listed. See the 0.0.0.0 entry below for the
full feature set — that version is published and is not repeated here.

### 新增 / Added

- **页面导航：标题栏加了后退与前进 / Back and Forward in the title bar** — 两个按钮按浏览器
  的方式来走访问过的页面：一条后退栈、一条前进栈，打开新页面会清掉前进栈，最多记 50 条。
  Alt+← / Alt+→ 与鼠标侧键同样有效；后退时页面从左滑入，前进时从右。导航窗格收起时它们
  照样可用——9:16 的预览要和参数面板抢宽度，窗格折叠起来的时候，这是回到刚才那一页最快
  的路。
  Two buttons in the title bar walk the pages you have visited the way a browser does: a back
  stack and a forward stack, a new visit clearing the forward stack, fifty entries at most.
  Alt+Left, Alt+Right and the side buttons on a mouse do the same, and the transition knows the
  direction — a step back slides the page in from the left, a step forward from the right. They
  are there with the navigation pane collapsed too: the 9:16 preview competes with the parameter
  panel for width, and once the pane is folded away this is the quickest way back to the page
  you were on.

### 修复 / Fixed

- **港股与美股的价格没有复权 / Hong Kong and US prices were unadjusted** — 定投计划与持仓
  收益要的是「任意两天之比就是持有者真实赚到的」那种价格，也就是复权价，而行情源只在 A 股
  上直接给得出。港股与美股拿到的是不复权的收盘价，于是拆股那一天成了一次凭空的暴跌：腾讯
  控股 2014-05-15 一拆五，图上是从 514 跌到 108.8，一夜 −78.83%；苹果 2020-08-31 一拆四，
  −74.15%。分红同样没有算进去——除息那天的下跌留在了曲线上，而那份现金没有回到持有者手里。
  现在这两个市场各走自己的复权端点：港股用 `hkfqkline` 的后复权，美股用 `usfqkline` 的前
  复权（前复权与后复权只差一个贯穿全序列的常数因子，在「份额 = 金额 ÷ 价」「市值 = 份额 ×
  价」里正好抵消）。十三年的月度定投，苹果从 +99.7% 回到 +576.4%，特斯拉从 +24.2% 回到
  +1061.2%，腾讯从 +48.2% 回到 +82.3%。指数与从未分派过的信托仍然用不复权的行——它们本来
  就没有可复权的东西。
  The plan and the position need a price whose ratio between any two days is what a holder
  actually earned, which is to say an adjusted one — and the source only serves that directly for
  an A-share. Hong Kong and US codes came back unadjusted, so a split arrived as a collapse out of
  nowhere: 腾讯控股's one-for-five on 2014-05-15 read as a close of 514.0 falling to 108.8
  overnight, minus 78.83 per cent, and Apple's four-for-one on 2020-08-31 as minus 74.15.
  Dividends were missing too — the drop on the ex-date stayed on the curve while the cash it paid
  out never came back to the holder. Each venue now goes to the endpoint that carries its adjusted
  rows: `hkfqkline` for Hong Kong, `usfqkline` for the United States, whose only adjusted series
  is the forward-adjusted one. Forward and backward differ by a single constant factor over the
  whole series, and that factor cancels in everything these pages derive — a buy is
  `amount / price` and a marking is `shares × price`. Over thirteen years of monthly
  buying, Apple goes from +99.7% to +576.4%, Tesla from +24.2% to +1061.2%, Tencent from +48.2%
  to +82.3%. Indices and trusts that have never distributed still read their unadjusted rows,
  having nothing to adjust for.

- **其余页面的价格也没有复权 / every other page was unadjusted too** — 上一轮只把定投与
  持仓这两个「按价买入」的页面换到了各市场自己的复权端点，其余页面仍留在通用端点的前复权
  上。而通用端点对港股和美股根本不给复权序列，对 A 股的高分红股给的是**负数**收盘价——
  贵州茅台 2010-09 至 2015-12 的月线，1280 根里有 1280 根是负的。于是：
  - 收益矩阵：收盘价非正数被当作无效值丢掉，茅台静默少了 7 个月、五粮液少 6 个月，剩下的
    两个月被当成相邻月算收益；港股与美股则完全没有复权，腾讯 2014-05-15 一拆五在月线上是
    −78.83%，苹果 2020-08-31 一拆四是 −74.15%。
  - 行业板块竞速：美股十只行业 ETF 里 XLK / XLY / XLE / XLB / XLU 在 2025-12-05 各自凭空
    跌掉约一半；自选股里放进高分红股，读到的同样是负价。
  - 涨跌日历：自定义区间拉回几年前时，日涨幅由负价算出。
  现在凡是要画收益的页面一律走总回报序列：A 股 `newfqkline` 的后复权、港股 `hkfqkline`
  的后复权、美股 `usfqkline` 的前复权，月线同样按市场选端点。复权后最差月：茅台从
  −65.99% 回到 −26.23%，苹果从 −69.64% 回到 −18.11%，XLK 从 −49.70% 回到 −11.95%；
  丢月数全部归零。**成交量与换手率那一页刻意留在前复权**——它靠「量 × 价 ≈ 额」判成交量
  的单位是手还是股，换成后复权会把价乘上整个复权因子（伊利股份是 84.5），判成「股」就差
  一百倍。
  The last round moved only the two pages that buy at a price — the plan and the
  position — onto each venue's own adjusted endpoint. Every other page stayed on the
  general endpoint's forward-adjusted series, which for a Hong Kong or US code is not
  adjusted at all and for an A-share heavy payer is *negative*: every one of 贵州茅台's
  1280 monthly closes between 2010-09 and 2015-12 is below zero. So the gain matrix
  dropped those months as invalid — seven of them for 茅台, six for 五粮液 — and read
  the two months either side of the hole as adjacent; Hong Kong and US months were
  wholly unadjusted, 腾讯控股's one-for-five of 2014-05-15 arriving as minus 78.83 per
  cent and Apple's four-for-one as minus 74.15. The sector race showed five of the ten
  US sector ETFs losing roughly half their value on 2025-12-05, and a watchlist holding
  a heavy payer reading negative prices. The gain calendar's daily returns came from
  those same closes once a custom range reached back a few years. Every page that draws
  a return now reads the total-return series: `newfqkline` backward-adjusted for an
  A-share, `hkfqkline` backward-adjusted for Hong Kong, `usfqkline` forward-adjusted for
  the United States, and the monthly request choosing its endpoint the same way. The
  worst month after: 茅台 −65.99% to −26.23%, Apple −69.64% to −18.11%, XLK −49.70% to
  −11.95%; no month dropped anywhere. **The volume page stays forward-adjusted on
  purpose** — it tells a listing's volume unit, lots or shares, from "volume × price ≈
  amount", and the backward-adjusted price is that price times the listing's whole
  adjustment factor, which for 伊利股份 is eighty-four: reading "shares" would put every
  bar a hundredth of what it is.

- **美股复权序列里没有成交额 / the US adjusted series carries no turnover** — 美股的前复权
  每行只有六个字段，到成交量为止，没有成交额也没有换手率。竞速页的成交额榜和涨跌日历的
  合计列会因此全部变成零。这两页现在拿到复权价之后，再向通用端点要一次成交额按日期合并：
  拆股改变的是价格与股数，不改变当天换手的钱，所以未复权那一行里的成交额本来就是对的。
  A US row on the adjusted series carries six fields and stops at the volume: no amount
  and no change rate behind it, which left the race's turnover board and the calendar's
  totals column at zero. Those two pages now ask the general endpoint for the window's
  turnover as well and merge it in by date. A split divides the price and multiplies the
  share count; it does not change the money that changed hands, so the unadjusted row's
  figure was the right one all along.

- **一次网络抖动就把这只票永久降级成不复权 / one dropped request degraded a code for
  good** — 复权端点只要失败一次，这个代码在本轮会话里就改用通用端点的未复权行，而一次
  定投要翻二十页，中间抖一下的概率并不小。现在把两种失败分开：请求压根没到源端（超时、
  连接中断、网关返回一段 HTML 而不是 JSON）最多重试两次再降级；源端明确回答「没有这个
  代码」则立刻降级，问第二遍也不会变。
  One failure on the venue's own endpoint was enough to move a code onto the general
  endpoint's unadjusted rows for the rest of the session, and a plan walks twenty pages,
  so a single blip was not unlikely. Two kinds of failure are told apart now: a request
  that never reached the source — a timeout, a broken connection, a gateway answering
  with HTML instead of JSON — is worth two more attempts, while an answer that says the
  source does not serve this code here is not, and degrades at once.

- **定投计划与持仓收益取不到数 / the plan and position pages failed to fetch** — 这两个页面
  要把十几年的日线一段一段往回翻，最后一段是「区间起点到已拿到的最早一根之前」；区间起点
  如果落在周末或假期（例如「近 5 年」从 2021-10-01 起，紧跟着就是国庆长假），这一小段里
  一根 K 线也没有。行情源按请求的窗口裁剪，于是返回空——而代码把「窗口里没有 K 线」当成
  错误抛了出去，多年数据已经拿到手，整条回溯却倒在了最后一步，页面报出一句英文的
  `no daily bars in that range.`。现在空窗口照空处理，回溯按既定规则停下。任何起点落在
  休市日的区间都会碰到它，一年里大约三分之一的日子。
  Both pages walk years of daily bars back one page at a time, and the last step asks for the
  stretch between the range's start and the earliest bar already held. When the start lands on a
  weekend or a public holiday — "the last five years" from 2026-10-01 starts on 2021-10-01, the
  first day of the National Day week — that stretch holds no bars at all, and the source, which
  clips rows to the window it was asked for, answers with nothing. The code took "no bars in the
  window" for a failure and threw, so a walk that had already gathered years of data died on its
  last step and the page reported `no daily bars in that range.` An empty window is now read as an
  empty window and the walk stops as it was designed to. Any range whose start falls on a day the
  market is shut runs into this — roughly a third of the calendar.

- **画面上写着的是上一个标的的名字 / the frame named the previous instrument** — 在定投计划与
  持仓收益里换标的时，画面标题只在取数成功后才跟着变；取数失败（比如上面那条）就停在旧名字
  上，于是图上写着「沪深300ETF定投计划」而失败信息里的代码是另一个。现在换标的那一刻就重画：
  属于旧标的的曲线一并清掉，标题立刻是新标的的名字。恢复参数时若存的只有代码没有名字，也
  不再回落到本市场的第一个内置标的（那同样是给画面安了一个不存在的名字）。
  On both pages the frame's title only followed a new pick once the fetch succeeded, so a failed
  fetch left the old name standing over the new code — the chart said "沪深300ETF plan" while the
  error named another instrument. The frame is redrawn the moment a pick is made now: the previous
  instrument's series is dropped and the title is the new instrument's. And when a restored
  preference carries a code but no name, the fallback is the code rather than the market's first
  built-in — which was the same defect wearing a friendlier name.

- **行业板块竞速的板块名跟随界面语言 / the race's sector names follow the language** — 内置
  列表（中证一级行业、热门主题板块、恒生分类指数、美股行业 ETF）的板块名用的是行情源自己的
  中文，于是在其他 13 种语言下，一张英文标题、英文副标题的图上，每一行都是中文。这些名字
  现在按代码查界面语言，与自选股的名称走同一条路；查不到的仍回落到源端原名。
  A built-in roster carried the quote source's own Chinese, so in the other thirteen languages a
  chart with an English title and an English caption still had a Chinese word on every row. The
  names are looked up by code now, as watchlist names already were; a code with no entry still
  falls back to the name the source gave.

- **切换市场后竞速列表回来的还是同一份 / the roster comes back as the same list** — 竞速列表
  的选中项此前是按位置记的，而只有一个内置列表的市场菜单更短，同一个位置落到的是另一份列表：
  「自定义板块」重启后会变成「自选股」。现在按标识记，位置上没有对应项时回落到第一个内置
  列表——与取数时已有的回退一致。
  The chosen roster was remembered by position, and a market with one built-in list has a shorter
  menu — the same position pointed at a different list, turning "custom sectors" into "watchlist
  stocks" across a restart. It is remembered by identity now, falling back to the first built-in
  list where the position has no equivalent, as the fetch itself already did.

### 已知限制 / Known limits（沿用 1.0.1.0，本版未变 / unchanged from 1.0.1.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：页面导航、板块名跟随语言、取数失败与标题两处修复，以及复权口径（三个市场、全部
画收益的页面）。
The fourteen "What's new in this version" lines now describe only this release: page navigation,
sector names following the language, the fetch failure and the title, and the adjustment basis —
all three markets, every page that draws a return.

---

## 1.0.1.0 — 2026-09-29（更新版 / update）

**1.0.0.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的 0.0.0.0 条目——
那一版已发布，这里不重复。
The first update after 1.0.0.0; only the changes are listed. See the 0.0.0.0 entry below for the
full feature set — that version is published and is not repeated here.

### 新增 / Added

- **动画背景可自定义 / the animation's backdrop is yours to set** — 设置页新增「动画背景」：
  默认渐变、自选两色渐变、或一张图片（可从电脑选，也可直接用 Windows 自带壁纸，最近 6 张
  留档）。图片按「填满」铺开并裁掉多余部分，压暗浓度 20–95% 可调。它同时作用于预览、导出的
  视频和封面图——三者由同一个渲染器绘制，所以文件里看到的就是预览里看到的。
  A new Settings card decides what every frame is drawn on: the built-in gradient, a two-colour
  gradient of your own, or a picture — from your computer or Windows' own wallpapers, the last six
  kept. Pictures fill the frame and are cropped rather than stretched, dimmed 20–95%. It reaches the
  exported video and the cover image as well as the preview, because one renderer draws all three.

### 改进 / Changed

- **设置页内容居中 / the Settings page is centred** — 那列固定宽度的卡片改为在窗口里居中，
  宽窗口下不再贴着左侧导航栏。
  The column of cards now sits centred in the window instead of against the navigation pane.
- **帮助手册新增「动画背景」一节 / the manual documents the new backdrop** — 14 份手册各加
  一章（现为 15 章），讲清三种背景、图片的铺法与浓度范围。
  All fourteen manuals gained a chapter on it (now fifteen); the chapter count is checked by the
  injection script, the way the resource keys are.

### 已知限制 / Known limits（沿用，本版未变 / unchanged）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 美股日线未做拆股调整，长区间曲线在拆股处会出现断崖。
  US daily bars are not split-adjusted; a long range shows a cliff at a split.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：动画背景可自定义。
The fourteen "What's new in this version" lines now describe only this change: the custom
animation backdrop.

---

## 1.0.0.0 — 2026-09-28（更新版 / update）

**这是商店中 0.0.0.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的
0.0.0.0 条目——那一版已经发布，这里不重复。
The first update after 0.0.0.0 in the Store; only the changes are listed. See the 0.0.0.0 entry
below for the full feature set — that version is already published and is not repeated here.

### 新增 / Added

- **窗口背景图片 / window background image** — 可任选一张图片作为窗口背景，遮罩浓度
  30–95% 可调，最近 6 张留档；高对比度主题下自动不显示。
  Pick an image as the window background, dim it 30–95%, keep the last six. Suppressed
  automatically under a high-contrast theme.
- **商店更新检查 / Store update check** — 商店有新版本时，导航栏「设置」右侧出现
  「更新」按钮；静默安装或经商店弹窗安装，装完自动重启应用。
  When the Store has a newer version, an Update button appears beside Settings: silent where
  the Store allows it, otherwise through the Store's own prompt, then the app restarts.
- **帮助文档配图 / pictures in the help document** — 14 份手册各配 5 张本语言的页面截图，
  图文相间；截图按语言取，日文手册配日文窗口。
  Each of the fourteen manuals carries five pictures of its own language — a Japanese manual
  shows a Japanese window.
- **标的显示名本地化 / instrument names follow the interface language** — 80 个常用标的的
  显示名随界面语言走（请求仍用代码，不变）。
  Eighty common instruments are named in the interface language; requests still go by code.

### 改进 / Changed

- **应用名随系统显示语言 / the app name follows the OS display language** — 开始菜单、
  应用列表与系统设置里显示的是**产品名**：中文系统显示「行情指标动画工作室」，其余显示
  Market Motion Studio。此前这三处都写死为包标识 `MarketMotionStudio`——那是标识符，
  不是产品名，任何语言下都长这样。未提供的语言回退英文。
  Start menu, Apps list and Settings now show the **product name** in the OS display language;
  all three previously carried the package identity, which is an identifier rather than a
  product name and reads the same in every language. Unlisted languages fall back to English.

### 已知限制 / Known limits（沿用 0.0.0.0，本版未变 / unchanged from 0.0.0.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。六档都出过片，
  但 1440p60 长片（5,400 帧）有一次卡在第 3,200 帧、文件被截断，未复现也未定位原因。
  Export offers three sizes × 30/60 fps. All six have produced a file; one 1440p60 run of
  5,400 frames stalled at frame 3,200 and left a truncated file — not reproduced, cause unknown.
- 美股日线未做拆股调整，长区间曲线在拆股处会出现断崖。
  US daily bars are not split-adjusted; a long range shows a cliff at a split.
- 港美股没有全市场成交额口径，市场成交额页在这两个市场下不存在。
  Hong Kong and US have no whole-market turnover figure, so that page is absent there.
- 定投计划与持仓收益页只能选区间长度，不能指定精确起始日期。
  The DCA and position pages take a range length, not an exact start date.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为
**只写本次改动**（此前误写成「首个发布版本」+ 全部能力，那是已发布的 0.0.0.0 的内容）。
原缺的意大利语整节已补齐，法语功能列表被截成 `- c` 的那一条已修复。
这份文案原本放在 `artifacts/`，而该目录在 `.gitignore` 里——等于没有备份；现已挪到
`docs/store-listing.md` 纳入版本控制。

---

## 0.0.0.0 — 2026-09-27（首个上架版本，已发布 / first published version）

**已发布上线，用户现在装得到的就是这一版。**
Published and live — this is the version users have.

### 新增 / Added

- **七个图表页 / seven chart pages** — 市场成交额、成交量与换手率、行业板块竞速、
  收益矩阵、涨跌日历、定投计划、持仓收益。
  Market turnover, volume & turnover rate, sector race, return matrix, up/down calendar,
  DCA plan, position replay.
- **三个市场 / three markets** — A股、港股、美股；在设置里切换，重启后生效。
  A-share, Hong Kong and US, switched in Settings; the change takes effect after a restart.
- **14 种界面语言 / 14 interface languages** — en-US、de、es、fr、it、pl、pt-BR、cs、tr、
  ru、ja、ko、zh-Hans、zh-Hant。帮助手册同样 14 份。
- **导出 / export** — 9:16 竖屏 H.264 MP4，三种尺寸（720×1280 / 1080×1920 / 1440×2560）
  × 30 / 60 fps，外加同帧封面 PNG；预览与编码器共用同一渲染器，所以导出的每一帧都等于
  预览看到的那一帧。
  9:16 vertical H.264 MP4 in three sizes (720×1280 / 1080×1920 / 1440×2560) at 30 or 60 fps,
  plus a cover PNG of the same frame. Preview and encoder share one renderer, so every exported
  frame is the frame the preview showed.

### 关于这个版本号 / About this number

0.0.0.0 是 09-26 上传 `0.2.0.1` 被拒之后改出来的：那条报错的真实含义是**第四位必须为 0**，
当时被误读成「必须全零」。它侥幸通过了校验，但违反「第一段不能为 0」，而且没有上升空间——
更新必须高于已发布版本。所以下一版直接跳到 `1.0.0.0`（1.0.0.0 > 0.0.0.0，用户能收到更新）。
0.0.0.0 came from misreading the rejection of 0.2.0.1 on 09-26: the error meant *the fourth
section must be 0*, not *all four must be 0*. It passed validation by luck, breaks the
"first section cannot be 0" rule, and has nowhere to go — an update must be higher. Hence
1.0.0.0, which is higher and will reach users.

---

## 模板 / Template for the next version

```
## X.Y.Z.0 — 日期 / date

### 新增 / Added
- 功能名 / Feature name — 一句话说明 / one line.

### 改进 / Changed
- 改了什么、为什么 / what changed and why.

### 修复 / Fixed
- 修了什么、原来什么症状 / what was wrong and how it showed.

### 商店文案同步 / Store listing
- docs/store-listing.md：14 份「此版本的新增功能」已更新到本版。
```
