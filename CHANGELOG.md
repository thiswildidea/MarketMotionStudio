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

## 1.0.2.0 — 2026-10-01（更新版 / update）

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
