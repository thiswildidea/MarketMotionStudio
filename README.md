# Market Motion Studio

**行情指标动画工作室** — a Windows desktop tool that turns stock-market indicators into
vertical data-visualisation videos and exports them as H.264 MP4. It points at one market at
a time, chosen in Settings: A-shares by default, or Hong Kong, or the United States.

The product has two display names on purpose. Chinese markets get 「行情指标动画工作室」; everywhere
else, and in the Store listing, it is Market Motion Studio. The package identity MarketMotionStudio
stays fixed in every market and is never shown to users. See "Languages" below.

**Version history is `CHANGELOG.md`** — one entry per Store submission, newest first: the number,
the date, what is new, and what is still known to be limited. Releasing is three actions that
belong together: bump `Version` in the manifest, add the entry, and update the fourteen
"What's new in this version" lines in `docs/store-listing.md`. That last file is the Store
listing copy for all fourteen languages, and it lives in the repository — it used to sit in the
ignored `artifacts/`, where a cleared directory would have taken it for good.

Status: **seventeen pages working, and export working on all of them, across three markets.** Market Turnover fetches
live quotes and animates them as a bar race or a turnover calendar; its parameters are remembered
between runs; a cover PNG and an MP4 both export at full resolution.
Stock Volume does the same for one instrument — search by code, name or pinyin, two modes (daily
bars and per-minute intraday), favourites, covers and exports all verified against live data for
贵州茅台. Sector Race is the third: a dozen sectors' or stocks' bars overtaking one another,
their order interpolated smoothly to the last frame, on four rosters and two metrics. Monthly
Matrix is the fourth — a decade of monthly bars per request, cells lighting up in time order, as
a year × month seasonality table or a targets × months rotation, both verified live (上证指数
ten years; CSI Level-1 twelve months). Gain-loss Calendar is the fifth: the whole-market page's
return calendar freed from its fixed series, run on any stock or index. **DCA Plan** is the sixth
and the one that is not about a series: it buys one instrument on a fixed amount and a fixed
cadence — daily, weekly or monthly — over years of closes, and animates what went in against what
the shares became worth, in whichever currency that market quotes. **Position Return** is the
seventh and the mirror image of the plan: one purchase, once — 2015, a million, 中国平安 —
and nothing but the mark-to-market after that, with the drawdown promoted to a headline figure
because a holding's worst moment is the price of its whole story. **Candles** is the eighth: one
instrument's prices as candles — daily, weekly or monthly — drawn four ways (candles, OHLC bars, a
closing line, a closing area) with MA5/10/20 and a volume panel, arriving one candle at a time
across the whole range or walking forward inside a window of it.

**Nine more pages followed**, and the navigation now numbers seventeen: **Market Cap Race** (a
market's fifteen largest by total value, the field asked for at fetch time so members really come
and go), **AH premium** (one company's two listings priced against each other), **Extreme Days**
(one instrument's biggest moves ranked — the only board whose rows are days, not companies),
**Currency Corridors** (a pair per row, and the row *is* the corridor), **Index Race** (how far each
index has come since its own first month, never its level), **Asset Classes** (eight
mainland-listed funds — what holding them earned), **Bond Market** (nine bond indices, measured on
the quote because an index pays no coupon), **Drawdowns** (how far below its own high each
sits, and how long the way back took), and **Hold Odds** (of every entry that finished, the share
that gained). The last three share one watchlist that mixes all three markets.

**The seventeen icons are drawn, not borrowed.** Three pairs of pages had been sharing one Segoe
Fluent glyph — Candles with Sector Race, Volume & Turnover with Hold Odds, Market Turnover with
Position Replay — and one shape cannot mean two pages; the menu was quietly saying those pairs were
the same thing. Each is now a stroke skeleton on a shared 20×20 grid (lines, rings, polylines,
arrowheads) that `tools/make-icons.py` expands into the filled geometry a `PathIcon` needs, written
to `Themes/Icons.xaml` and taking its colour from the theme. Every drawing carries two registration
marks pinning its bounding box to `[2,18]²`, because `PathIcon` scales by bounding box and, without
them, a wide icon comes back stretched and a tall one squashed. Help and Settings keep their glyphs.

**Export is now measured rather than designed.** Three consecutive 90-second 1080p30 exports, driven
through the live app against 65 trading days of fetched data:

| | measured |
|---|---|
| wall time to encode 2,700 frames | 28 s, 35 s, 28 s — about a third of the video's own length |
| container | `ftyp` + `uuid` + `mdat` + `moov`, **no `moof`** — a plain, non-fragmented MP4 |
| duration in `mvhd` | 90.00 s, exactly as asked |
| samples in `stsz` | 2,700, one per frame drawn |
| size | 18.9–21.0 MB (High quality, 10 Mbps) |
| **the picture** | the last decoded frame matches a cover export of the same frame at a mean difference of **2.23** — the residue is H.264. Unflipped it was 26.99, which is how the vertical flip was found |

**Every format the settings offer has now been through the encoder**, each verified upright by
the same cover comparison, in a fresh session with both files exported back to back:

| format | frames | wall time | result |
|---|---|---|---|
| 1080×1920 · 30 fps | 2,700 | 28–35 s | complete, non-fragmented, MAD 2.25 |
| 1080×1920 · 60 fps | 5,400 | 58 s | complete, non-fragmented |
| 1440×2560 · 30 fps | 2,700 | 53 s | complete, non-fragmented, MAD 1.87 |
| 1440×2560 · 60 fps | 3,900 | 85 s | complete, non-fragmented, MAD 1.87 |

One 1440p60 run of 5,400 frames stalled at sample 3,200 with the app alive and the file left
truncated. It has not reproduced and no cause is established — see NOTES before assuming the
format is at fault.

That turned on one line: `MediaTranscoder.HardwareAccelerationEnabled` has to be **false**. See
"Things learned the hard way" — with it true, `PrepareMediaStreamSourceTranscodeAsync` never returns,
and nothing anywhere reports an error.

## What it is for

The two tools this replaces (`ashare-turnover-studio` and `stock-dual-studio`) were single
HTML files that drew on a canvas and recorded it with `MediaRecorder`. They worked, and they
carried three limitations that came from the browser rather than from the problem:

- **Export took as long as the video.** `MediaRecorder` timestamps frames by the wall clock,
  so a ninety-second video took ninety seconds to write, and feeding frames faster produced a
  video that played fast.
- **The output was fragmented MP4** (`ftyp` + `moov` + many `moof`/`mdat`). Platforms
  re-encode on upload so posting was fine, but editors read the timeline unreliably.
- **Edge or Chrome had to be installed**, because the H.264 encoder was the browser's.

Drawing with Win2D and encoding through Media Foundation removes all three: the encoder owns
the clock, the container is an ordinary MP4, and nothing outside the package is required.
Fetching over `HttpClient` also disposes of CORS and the JSONP workaround entirely.

## Markets

Settings picks which market the app reads: **A-shares** (the default, and the market the app
is named for), **Hong Kong**, or **the United States**. The choice is stored like the language
and the theme, and for the same reason it takes effect at the next start: the pages build their
rosters and preset lists as they are constructed, and the shell keeps the page instances alive
afterwards, so rebuilding one list on the spot would leave the rest pointing at the old market.

What each market can actually supply was measured against the endpoint, page by page, rather
than assumed from the market's existence:

| page | Hong Kong | United States |
|---|---|---|
| **Market Turnover** | no whole-market figure — the source's HK codes carry the turnover of an index's own constituents | the index "amount" is volume × index level, a number nobody paid |
| **Stock Volume** | daily and intraday, as the A-shares | daily only — the minute endpoint answers a US code with an empty body |
| **Sector Race** | the four Hang Seng sub-indices (finance, property, utilities, commerce & industry) | ten SPDR sector ETFs |
| **Return Matrix** | monthly bars for indices and listings | monthly bars for indices and listings |
| **Gain-loss Calendar** | daily bars for indices and listings | daily bars for indices and listings |
| **DCA Plan** | the Tracker Fund, the Hang Seng China Enterprises and tech trackers, and the two indices themselves | SPY, QQQ, DIA, IWM and the gold trust |
| **Position Return** | same preset families as the plan, plus the blue-chip singles | same, plus the broad singles |
| **Candles** | daily, weekly and monthly bars for indices and listings | same, with the venue tried in turn (`.OQ`, `.N`, `.AM`) |
| **Market Cap Race** | today's top 200 by market value, plus an archive of companies that used to be up there | thirty-five, and forty-two — a fixed field, because neither venue has a ranking this app can reach |
| **AH premium** | the Hong Kong leg of each pair — and the mainland leg, always both | not applicable: the page compares the two listings of one company, so it is the one page the market switch does not govern |

**A page the market cannot feed is not offered.** Market Turnover is taken *out of the
navigation* on Hong Kong and the United States rather than left to draw nothing, because what
it would draw is not a smaller answer but a different one — the turnover of an index's
constituents sits on the same axis as the turnover of a whole market and is not the figure the
page is about. Stock Volume keeps its daily mode and loses the mode radio entirely on the US,
so there is no control that leads to an empty fetch.

Everything that differs between the markets is data, not branches through the pages:
`MarketProfile` carries the amount's divisor, how the volume field is read, whether the minute
endpoint serves the market, the rosters on offer and the one-tap instruments. A page asks the
profile instead of knowing any of it.

Three facts about the source that a market switch would otherwise hide:

- **A US bar's amount is in dollars, not 万元.** Everywhere else ten thousand of the field is
  one 亿; in New York a hundred million of it is. One divisor for all three markets is a figure
  out by ten thousand — and an axis label would not make the difference visible.
- **The search endpoint answers in lower case** (`usaapl.oq`) while the chart endpoint refuses
  anything but `usAAPL.OQ`, and answers with *no bars* rather than with an error, so a code
  taken from search and passed straight through reads as an instrument with no history.
- **A US ticker typed without its exchange suffix is worse than refused**: `usAAPL` comes back
  as one bar from 2011, which looks like a listing that barely trades. The venues are tried in
  turn (`.OQ`, `.N`, `.AM`) and the first that answers with a real history wins.

## The seventeen pages

**Market Turnover** — the whole market's daily turnover: the Shanghai and Shenzhen composite
amounts added together. Only days on which every included market traded are kept, so one market's
holiday cannot make the total appear to collapse. A session still in progress is dropped, because
an unfinished day holds only its opening auction. The Beijing option adds the BSE 50 index, which
covers its constituents rather than the whole exchange — a different measure, and a smaller one,
so it is off by default.

The last entry on that menu is **your own list** — the one the four roster boards share, indices
and shares side by side. Two rules change when it is the basket, and both because a share is not an
index. Only mainland codes can be added up: turnover is reported in each market's own currency, so a
Hong Kong or New York name is left out and the status line says how many. And a day stays on the axis
if *any* member traded, with a member that has no row for it contributing nothing — the boards above
keep only the days every code has, which never bit while every code was an index, and which under a
halted share would remove the day from the chart entirely while the picture carried on looking
exactly like a day on which nothing traded anywhere.

It draws in **three forms**. The **bar race** and the **turnover calendar** are switchable at any
time without re-fetching, because they answer different questions about one fetch: the race puts time
on the horizontal axis, so a run of heavy days reads as a run, and closes with the mean line and the
two extremes boxed; the calendar gives one block per month with cells lighting up day by day, so a
busy fortnight is a patch of colour you can point at — which a time axis spreads out. The gain/loss
calendar that once completed this trio is its own page now (below): two places producing the same
video is a choice nobody needs, and the whole-market copy could only ever name one index.

The third, **intraday**, is a fetch of its own: one session's turnover accumulating from the opening
bell to the close, drawn as a curve that can only rise. The source keeps five sessions and no more,
so no range is offered and the frame names the day it drew. It stops at 15:00, because the half hour
the endpoint adds after that is after-hours trading, which the daily figure leaves out too — measured
on 贵州茅台 2026-09-30, ¥47.97 亿 at 15:00 against ¥48.02 亿 at 15:30, while the daily row says
¥47.97 亿. Its four closing cards are the day's total and what share of it fell in the morning, the
afternoon and the last half hour, because a chart of *when* money moved should answer with shares and
not restate the same total four times.

**Turnover and daily change are not summed the same way, and that asymmetry decides the design.**
Turnover is a quantity, so Shanghai plus Shenzhen is a whole-market figure. A percentage change is a
ratio, and adding two of them means nothing — so the return series is the *leading venue's alone*,
which is why the return calendar's subtitle names the index rather than the combination. One fetch
carries both measures; a `Metric` object says which one a frame is drawing and supplies everything
that follows from the choice: the values, their colours, how a figure reads, the closing cards, and
which two days get boxed.

**The series covers whichever slice of the market was picked.** Eight scopes: both exchanges,
either exchange, either main board, STAR, ChiNext, and both-exchanges-plus-BSE-50. Every board is
measured by a *composite* index — on this source the Shenzhen component and composite carry the
same amount while the STAR 50 carries a third of its board, so composites are the one rule that
keeps every number the same kind of number. The main boards have no composite of their own, so they
are derived per day as the exchange total less its growth board; both sides come from the same
source and the same口径, so the subtraction is exact. The whole-market figure is unchanged by the
rescope: the Shenzhen composite's amount is what the component index always carried.

The calendar has two layout decisions that exist because the frame is portrait. It draws
**Monday to Friday only**: A-shares do not trade at weekends, so two of seven columns would always
be empty while costing every cell nearly a third of its width. And the number of month-blocks per
row is **searched rather than ruled** — every count from one to four is tried and whichever yields
the largest cell wins. On a tall frame height is the binding constraint, so the best arrangement
depends on how many months there are in a way no fixed rule captures; four months land on two
columns of two, a year on four columns of four, and nobody has to choose.

**Stock Volume** — one stock's volume against its turnover rate, as two stacked panels, in
either of two modes. Across trading days the two series are proportional and the panels have
nearly the same shape; within one day, per-minute volume and cumulative turnover look
genuinely different, which is the better picture. The intraday source only keeps the last few
trading days, so that mode offers those rather than an arbitrary date. The stock is found by
code, Chinese name or pinyin through the same quote vendor's suggestion box, and a favourites
row keeps the codes worth coming back to — both stored locally, nothing sent anywhere.

**Sector Race** — a dozen horizontal bars overtaking one another, their order changing to the
last frame: the form where the suspense survives to the end, which a single growing series
cannot hold. Four rosters — the ten CSI Level-1 industries (mutually exclusive, collectively
exhaustive), fifteen hot themes, a custom pick from their union, or a watchlist of stocks — on
two metrics: cumulative return (zero axis centred, red up green down) or cumulative turnover
(monotonic — the story of where the money went). The smoothness is the ranking itself being
interpolated: each day's standings are precomputed, a row's position eases between its two
neighbouring days' ranks, and the axis range interpolates with them, so two racers trading
places cross instead of swapping. Rosters and metrics are bounded — three to sixteen racers,
or a vertical frame is a barcode — and the bounds are stated where the choice is made.

**Return Matrix** — months as cells lighting up in time order, on a clock the daily pages
cannot share: one request of monthly bars holds about eleven years, so a range selector built
for daily bars would say things the matrix cannot honour, which is why this is its own page
rather than a fourth form. Two kinds from one renderer — the kinds differ in what the rows and
columns *are*, resolved when the spec is built. Year × month reads one instrument's
seasonality, with every calendar month averaged across the years for the closing cards;
targets × months reads rotation, folding into horizontal bands of twelve when the months
exceed one row's width, each band carrying its own heads and a sub-total, so cells stay big
enough to read. Both compound the range by multiplying — a +20% month and a −20% month are
−4% together, and adding them to zero overstates exactly the volatile ranges a matrix is read
for. Cell colour is red up green down with depth as the square root of magnitude over the
frame's largest: linear puts nearly every month at the same dark tone, because most months
are far smaller than the extreme.

**Gain-loss Calendar** — the whole-market page's return calendar as its own page, on **any
A-share stock or index** rather than one fixed composite — which is why that copy was removed
from the whole-market page: its only instrument was one preset here. No renderer of its own: the calendar
grid is metric-driven, so this page is a different *loader* — one instrument's daily bars
shaped into the series record the whole-market page builds from three indices' — behind the
same grid, colour ramp and closing cards. The stock is found the way the per-stock page finds
one (code, Chinese name or pinyin, filtered to the market in force, whose codes are the ones
the bars endpoint speaks), with one-tap presets for that market's broad indices and **the same
watchlist** as the per-stock page — a favourite is a fact about the instrument, not about the
page it was added on. A favourite saved under another market is not carried over: the page
says which market the code belongs to instead of fetching from a venue it no longer names. Cell colour depth goes as the **square root** of the move, not linearly: most days are
small against a period's largest one, and a linear ramp leaves nearly every cell at the same
near-black while the picture says only "there was one big day". Verified live both ways:
上证指数 by preset, 贵州茅台 by typed code, each fetched, covered and encoded to MP4 with the
last frame matching its cover.

**DCA Plan** — the only page where the interesting number is a *difference* rather than a
level. A fixed amount goes into one instrument on every trading day, or every week, or
every month; what accumulates is shares, and the frame draws two lines on one axis — what
has been paid in, in amber, and what those shares are worth, in red — with the space
between them filled warm while the plan is ahead and cool while it is behind. The headline
reading is the ratio between them, which is the thing a plan is for: how the discipline
did, not how the price did.

Two decisions worth stating, because a naïve version gets both wrong silently:

- **The cadence is read off the trading calendar, not off a date grid.** A weekly plan buys
  on the first *trading* day of an ISO week and a monthly one on the first trading day of a
  month, so a Monday holiday moves that week's buy to Tuesday — which is what a person
  putting money in would have done, and which a "every seven rows" rule would not have.
  Whether a bar is a buy has to be decided bar by bar for this reason, not by index.
- **Years are walked backwards one request at a time.** One request carries about 640 bars,
  roughly two and a half years, so a ten-year plan is four or five requests stitched
  together, each asked for the window ending the day before the last one's earliest bar,
  deduplicated by date. It stops when a request brings nothing earlier than what it already
  has — which is both "the range is covered" and "this instrument's history starts here",
  two states the source does not distinguish.

The simulation is deliberately plain — `amount / close` shares at that day's close, no fees,
no slippage, no timing beyond the calendar — and says so on the frame. It is a description
of a price series, not a record of something anyone could have executed. Both pages that buy
at a price read the **backward-adjusted** series, and that choice is not cosmetic: the
forward-adjusted one rebases itself to today, and for a heavy payer like 中国平安 the rebase
goes through zero — years of closes arrive negative, which a ratio chart survives but a
purchase does not. The backward-adjusted series anchors at the listing, so every close is
positive and the ratio between any two days is the holding's real total return, dividends
reinvested.

The preset lists are per market, because a plan is something people start on particular
things: the A-shares get the broad ETFs (300, 500, ChiNext), the gold ETF that is the
non-equity arm of the same habit, a Nasdaq tracker, and the two indices for asking what the
market itself would have returned; Hong Kong gets the Tracker Fund and its H-share and tech
siblings; the US gets SPY, QQQ, DIA, IWM and GLD. Every code was fetched and read back
before being written down. The currency the amounts are named in comes from the market too —
CNY, HKD or USD — because an amount invested is an amount *of something*, and three venues
do not agree on what.

**Position Return** — the plan's mirror image, and the page where the interesting number is
a *ratio with a past*. One purchase, once: a capital, a day, one instrument. The capital line
is flat because nothing was ever added; the value line does whatever the price did; the space
between them fills warm while the holding is ahead and cool while it is behind, and the
headline reading is the ratio between the two, coloured by its own sign so a holding crossing
from loss to gain changes the colour of its number. The closing cards add what a return alone
hides — the **maximum drawdown**, the deepest fall from the holding's own running peak, which
is the price a holder paid for the whole story. Like the plan, the sim is deliberately plain:
adjusted closes, no fees, and the frame says what it is not.

Its range selector defaults to **as far back as the source goes**, because a holding's story
starts where the holder says it did, and "since 2015" is a span no fixed choice covers.

**Candles** — one instrument's prices as candles, and the only page where the period is a choice
of its own: **daily, weekly or monthly**, each served by the endpoint rather than aggregated from
the finer one, because a weekly bar the source did not compute is a bar nobody quoted. Four ways
to draw the same series — candles, OHLC bars, a closing line, a closing area — since the series is
one thing and what a viewer reads off it is another: bodies answer "where did it open and close",
a closing line answers "where has it been". MA5/10/20 ride over the plot and a volume panel sits
under it, and the range's return with its high and low is marked on the frame.

It is also the first page with **two animations**, because a candle series raises a question the
others do not. **Growing** draws one more candle per step until the whole range is on screen —
right for a range whose end is the point. **Scrolling** holds a fixed-width window and walks it
forward — right for a long range, where growing would end with several hundred candles squeezed
into one frame width. Both are drawn from the same progress fraction, so the choice is about what
the frame shows at a given moment and not about how the picture is produced.

A US code typed in the wrong case fetches **nothing**, because the search endpoint answers
`usaapl.oq` while the chart endpoint will only read `usAAPL.OQ` and returns no bars rather than an
error — which reads as an instrument with no history. A code is canonicalised for its market the
moment it is known, and the frame's name is the one the endpoint returns with the series rather
than the code the user typed.

**Market Cap Race** — the sector race's twin: fifteen horizontal bars, ranked by total market
value, their order changing to the last frame. Same renderer, same interpolated ranking, same two
gutters — a different question. The race asks how a sector performed; this asks which company *is*,
which the last decade of this market answers with a clear upset in it.

**The field is asked for, not remembered.** A hand-written field is wrong the moment somebody
lists, and it was: 长鑫科技 listed, became the largest company on the mainland at 3.7 trillion, and
the board did not know it existed — a defect no amount of care in writing the list could have
prevented, because the list was written before the company listed. So the field is **today's top two
hundred by market value**, asked of a ranking endpoint at fetch time, plus an archive of companies
that used to be up there and are not any more (万科, 中国重工, 上汽) — the archive is what a ten-year
board needs and a ranking cannot supply. The board is then whichever fifteen of those were largest at
each moment. Watching it run, December 2016 is ICBC, CCB, PetroChina, Bank of China, ABC, China Life,
Sinopec, Merchants Bank — and September 2026 has added 长鑫科技, 茅台, 宁德时代, 工业富联 and
紫金矿业 in their places.

**This page is the one place the app reads a second source, and the reason is in the first
sentence.** Tencent serves quotes and bars and no ranking at all: three candidate paths
(`stock.gtimg.cn`'s `rank`, `cgi-bin/rank/pt`, `cgi-bin/rank/hs`) answer with an empty list or a
400. Sina's `Market_Center.getHQNodeData` answers with the whole market sorted by market value, in
pages of a hundred, in the same code shape this app already speaks — `sh688825`, not a vendor
identifier — so nothing is translated and one request per fetch is the whole of the traffic. The
snapshot endpoint is still Tencent's, the bars are still Tencent's, and a failure of the ranking
falls back to the archive rather than to nothing: a board with a stale field is still a board.

**The month is the resolution, and it is where the subject lives.** A market-cap ranking is a slow
variable; what a daily series would buy is three hundred and seventy requests for a board that
moves a few times a year. The renderer interpolates between the periods it is given, so the motion
is continuous even though the data is monthly.

**Which means the frame's header line counts months, and it did not always say so.** That renderer
is shared with the sector race, which is daily, and the word after the count was read off the string
table inside the renderer — so a monthly board announced "12 个交易日" for twelve months, in every
frame of every export, and it took a reader asking why twelve months were being called trading days.
The count word and the span word are both supplied by the page now (`UnitWord`, `SpanWord`): the page
is the thing that knows what interval it asked the source for, and the renderer only knows how many
rows came back.

**One entry per calendar month, dated on the month's last bar.** Not the plain union of every date
in the field: a monthly row is dated on the month's last *trading* day, and a listing suspended for
a fortnight has its last trading day mid-month, so the union of two hundred listings' dates came to
**139 dates for 120 months** — nineteen "periods" in which one listing advanced and sixty-one
carried a stale value, which the frame showed as a stutter. Grouped by year and month, it is 120.

**A past market value is derived, and the derivation is worth stating.** The source serves today's
total market value and nothing else: a share count's own history is not served at all, so each past
value is `today's value × the adjusted price ratio`. That is exact as far as the adjusted series is
exact — a bonus issue or a split moves the price and the share count by the same factor and the
adjusted series cancels it, so a ten-for-ten does not read as the company halving. **A dividend is
not cancelled**, because the adjusted series reinvests it, so a heavy payer's past value reads low
and it looks like it grew faster than it did. The manual says so, the settings panel says so, and
the last frame's figure is the only one that came straight from the source.

**AH premium** — the tenth page, and the one page that needs two markets at once: the same company
listed on the mainland and in Hong Kong, ranked by how much dearer the mainland share is.

**Nothing here is derived, which is the whole design.** A market-cap board multiplies today's value
by an adjusted ratio because a share count's history is not served; a premium is two prices that
were really paid, and the rate between their currencies. So this is the one page that must **not**
use the adjusted series — and the reason `TencentKline.RawBarsAsync` exists. Backward adjustment
anchors a listing's earliest price and inflates every later one: ICBC's A share sells at 8.28 and the
adjusted series reports 13.34, which turns a +26% premium into +245%. **Two markets adjusted
separately cannot be compared**, so both legs and the rate take the same raw call.

**The same gap is quoted both ways round, which was the first thing a reader doubted.** This page
gives A against H — the direction the industry's own premium index uses — so 新华制药 reads +194%.
雪球 prints the same company on the same close as `溢价(H/A) −65.97%`: the same fact with the legs
swapped, since 1 ÷ (1 − 0.66) − 1 = 1.94. The card's method note and all fourteen manuals say so,
because the report that prompted them was "this value is wrong", and the value was right — it was
being read in the other direction.

**The frame draws the dearest fifteen, and on this market all fifteen are dear.** Across the field
the premium ran from +194% (新华制药) down to −9% (药明康德) on 2026-09-30, and only two of the
sixty-nine — 招商银行 and 药明康德 — have their Hong Kong line above their mainland one. At −6% and
−9% those two sit at the bottom of the list, where a top-fifteen board never reaches, so every bar
grows right from a zero axis at the left edge. The bars answer "how much dearer", not "which side",
and the manual and the card say so rather than leaving the frame to imply otherwise.

**The span decides how many companies are on it.** Sixty-nine pairs are candidates; a pair is drawn
only if both legs cover the whole span, so one whose Hong Kong listing is younger than the span drops
out — sixty-eight over three years, fifty-two over the longest. The count the page reports is the
count it drew, and the card explains the trade rather than promising a number.

**The longest span is about nine years, and the exchange rate is why.** `whHKDCNY` reaches back to
2016 and the two legs reach much further. Monthly, because a spread that moves a few points a year
does not need days, and because one request returns fifteen years of it. The three legs close their
months on different days — the A share on its last trading day, the rate on its last banking day —
so the axis is grouped by calendar month and dated on the month's own last day rather than
intersected on the date: the same defect that once reported 139 periods for 120 months.

**The pairs are written down, and the list is checkable.** Neither source answers "which mainland
listings also have a Hong Kong listing", so the field is a literal — which is a liability the market
cap board already paid for once. What keeps it honest is that every code was read back from the quote
endpoint on 2026-10-02, and one did not answer: 海通证券, whose H shares were delisted after the
merger into 国泰海通. A field of seventy less one, where the minus one would have been a lane that
stayed empty for the whole video.

**The axis is a union, not an intersection.** A listing that listed three years ago has no rows
before that, and intersecting would quietly start the whole video on the day the youngest entrant
listed — a ten-year board turned into a three-year one. With a union, and no value before the first
bar, it grows out of nothing on the day it joined, which is what a bar chart can say and a silent
truncation cannot.

**The name column now holds company names**, and that is why the renderer's left gutter sizes its
text before drawing: `Agricultural Bank of China` at the row's own size runs off the left edge of
the frame, and nothing complains — the first frame that names a company is the first frame that is
visibly wrong. One shared size for the whole column, computed once rather than per frame.

**Extreme days** — the eleventh page, and the one whose rows are days rather than companies: one
instrument's largest single-day moves, ranked by size.

**A row's value never changes, which is the whole inversion.** Every other board gives a racer a
value that moves day by day; here the racer *is* a day, and its value is how far the instrument
moved on it — fixed the moment that day closed. What moves instead is membership: a day is worth
nothing until it happens, so the board fills in as the years pass, and a day larger than the
fifteenth takes its place and pushes someone off the bottom. Twenty-four candidate days race for
fifteen places.

**Ranked by magnitude, not by sign.** A board of moves is a board of *moves*: −7.7% belongs beside
+8.1%. Ranking the signed values would file every fall below every rise, however small the rise,
and the page would be a list of good days with the crashes filed underneath. Bars therefore grow
both ways from the zero axis — **a rise to the right in red, a fall to the left in green** — which
is also the one board here whose bars are coloured by what the row says rather than by a hash of
its code: a company is something a viewer follows up a board, and a day is not.

**Days that have not happened yet are not on it.** Before its own date a row is worth zero, and
ranked by magnitude it sits at the bottom of the field — which is not far enough, because
twenty-four candidates of which five have happened still fill a fifteen-row frame, ten of them
reading 0.00%. The renderer skips a row whose value is zero *at that day*, which is also what makes
the board visibly fill up rather than start full.

**The move is the change in the adjusted close**, because an ex-dividend day is not a crash: the
price drops by the dividend that morning, and an unadjusted series would put that day at the top of
a board of the largest falls in history, when nobody holding the stock lost anything. On an index the
distinction is invisible, which is exactly why it is stated rather than left to be discovered on a
stock — and a stock can be on this board. Any instrument the market quotes goes in through the same
search box the candle and calendar pages carry; the market's broad indices sit underneath it as one
tap each — still a shortcut and not the boundary of the page — and the watchlist beside them is the
same list every other per-instrument page reads, because a favourite is a fact about the instrument
and not about the page it was added on.

**The longest span is about thirty-five years**, and that is the walk's limit rather than a choice:
one request carries about 640 daily bars and the walk makes twenty. A span with fewer than sixty
trading days is refused — the largest single day inside a quiet month is not a fact a board should
be built on.

**Currency corridors** — the twelfth page, and the one whose row is a *place* rather than a
quantity: six currency pairs, each drawn against the range it has actually traded in.

**The row is the corridor.** One end is the cheapest the pair has been in the chosen span, the
other the dearest, and the marker is where the rate is now. So the row is drawn full width in every
frame — a corridor is a place, not an amount — and what moves is the marker, together with the
walls, which are the lowest low and the highest high **so far**: a month that goes further than any
month before it pushes one of them outwards, and the corridor visibly widens as the years pass. A
fixed ruler with a dot on it would be a gauge; an expanding corridor is a record, and a pair
sitting at 100% is at the dearest it has ever been in the span, not at a limit.

**Every pair is measured against itself.** 157.92 on USD/JPY and 1.1245 on EUR/USD are not two
points on one scale, and normalising each corridor is what lets six pairs share one board. The cost
is that a narrow corridor and a wide one look alike, so the floor and the ceiling are printed under
every row — the only place on the frame that tells them apart.

**Two lists, offered separately, because the source's coverage differs.** USD/CNY reaches back to
2005 and carries 316 months; the other five renminbi pairs begin in 2016; the major crosses all
begin in 2005-07 and carry 325 months each. On one board together, what a viewer would be reading
is when the source started quoting each pair. A pair with no rate in a month is not a pair at 0% —
it is a pair with no position, so it is left off the board and out of the ranking rather than
pinned to the floor.

**Monthly, and one request per pair.** The endpoint answers a whole monthly history in one reply —
325 months against a 430-month ceiling — so "as far back as there is" costs six requests rather
than a hundred and twenty. Unadjusted, like the A+H page: a currency has no dividend and no split,
and an adjustment on one side of a comparison compares two different things.

**The market setting does not apply here.** A currency pair belongs to no stock market, so the
board is the same whichever one is in force — the second page, after A+H, that sits outside the
market switch's reach.

**Index race** — the thirteenth page, and the first one that is not about a single market: twelve
indices from Shanghai, Shenzhen, Hong Kong and New York, measured against one another.

**The row is the change, never the level.** 3,800 on the Shanghai Composite and 5,700 on the
S&P 500 are not two points on one scale, so each row is the cumulative change since *its own* first
month inside the range, in per cent. Drawing levels would be a board about where each index
happened to start counting.

**An index that arrives late is not on the board until it arrives.** The S&P reaches back to 1950,
the Dow only to 2009, the Hang Seng Tech index to 2020 — and on a shared axis that begins with the
oldest of them, the honest picture is a board that fills in. Which means the rows cannot start
together, and a row with no history yet is *absent* rather than zero: parked at 0.00% it would rank
above every index that was ever down and read as a market in which nothing happened. Every other
board here has every row from the first frame, so this is the first page that has to carry when
each row joined — one number per racer, from the loader, out to the renderer, which both leaves
the row out of the ranking and skips it when drawing. A row merely ranked last still holds its
place, and twelve places with seven of them empty is a board full of holes.

**Monthly, and adjusted since this board learned to race a reader's own list.** One request per
index carries 430 months — the source's ceiling — so "longest" costs twelve requests and about
thirty-five years. Daily would be worse than slower: the three markets' holidays are not each
other's, and a day any one of them lacked would either drop out of every row or be carried forward
into a claim that nothing moved.

Adjustment was the one open question, and it is settled by measurement rather than by argument.
**The source ignores the adjustment parameter for an index**: asked either way, all twelve come back
identical — the first month's close, the last month's close and the ten-year change differ by
0.0000 across every one of them. What an adjustment costs an index is nothing, and what it buys a
share is everything: over the same decade Apple reads +193% unadjusted against **+1183%** adjusted,
because of a four-for-one split in 2020; CATL reads 305% against 684%, Gree 71% against 138%. So
the board now takes the adjusted path, every figure already published from it is unchanged, and a
share sitting alongside those twelve is no longer short-changed by its own calendar. The one thing
it does cost is a difference of kind, and the page states it rather than hiding it: an index row is
a **price** return, because an index is not something you can hold, while a share row is a **total**
one, with the dividends and the splits put back.

**The market setting does not apply here either.** This page reads three markets at once, so there
is no single market it could be about; the group is chosen on the page — all twelve, the mainland's
six, Hong Kong's three, New York's three, or **a list of your own**. It is the third page, after
A+H and the currency corridors, that sits outside the market switch's reach.

**Asset classes** — the fourteenth page, and the index race's other half: eight asset classes you
could actually have held, one fund each, measured against one another. That board races published
numbers; this one races money.

**Adjusted, where the index race is unadjusted — and that is the reason the two do not share a
loader despite having the same arithmetic.** An index pays no dividend, so leaving its series alone
costs nothing there. A fund does pay, and most of what it pays is invisible in its price:

* the money-market fund's price goes from 100.161 to 100.901 across thirteen years. Unadjusted that
  is +0.0%, which draws cash — the one row here that has never fallen — as the bottom of the board,
  and tells the reader that holding cash was the worst available choice. Adjusted, it is +18.76%
  over the last ten years;
* a Nasdaq fund quoted at 0.998 in 2013 and 2.352 today looks, unadjusted, like +136% over thirteen
  years. The index it tracks rose sixfold over the last decade alone; the difference is a share
  split, which multiplied the holder's units by exactly what it divided their price by.

Both are wrong in the same direction and by a lot, so this is not a matter of taste. It is also why
the two boards cannot share a loader: the reason has to be readable where the call is made.

**The row is the change, never the level, and a row that has not joined yet is absent** — the same
two rules the index race established, for the same two reasons. The commodity fund only starts in
2019, so a ten-year board opens with seven rows and fills in as the years pass.

**All eight are quoted on a mainland exchange**, so every row is bought with the same money, and the
two overseas rows carry the exchange rate inside them — which is what a mainland holder's return
actually was. That is also why the market setting does not apply here: the board is chosen on the
page — all eight, the four share funds, the four that are not shares, or **a list of your own**.

Measured 2026-10-03 over ten years: 119 months, the Nasdaq fund ahead at +556.98%, the gold fund at
+225.67%, and the money-market fund behind at +18.55%.

**Bond market** — the seventeenth page, and the bond world the asset race left as a single row: nine
exchange bond indices, each measured from its own first month in the range. The asset race keeps the
bond market down to one government-bond fund among eight; this page is the bond market itself.

**Deliberately the opposite of the asset race, and the two cannot be read against each other.** Every
row here is an index, and the source ignores the adjustment parameter for an index, so what is drawn
is the quote. A bond pays most of its return as coupon and a coupon never appears in a quote: a
holder earned more than this board shows, by a different amount on every row. That board is drawn on
the adjusted series because a fund does pay out; this one is left alone because an index does not.

**The roster is built in, not a list you keep.** A CSI total-bond index was wanted and does not exist
on this source: the code that looks like it is the Shanghai detachable-bond index, whose monthly
series stops in August 2015, and a sweep of the whole index code space — `sh000001`–`sh000999` and
`sz399001`–`sz399999`, every code the source answers a name for — found no total-bond index at all.
It is a CSI Index Company code (`H11001`) and sits outside the exchange code space entirely. Those
seats went to the deepest credit indices the source does answer, and two bond ETFs were considered
and rejected: dividends and unit splits put a cliff or a collapse into their price series
(`sh511220` reads −89.6% over ten years, `sh511030` +949% over five), so a fund and an index cannot
share a board.

**The range is snapped to whole months at both ends.** The source answers this period only in whole
months and labels each row with that month's *last day*. Asked for a window opening on the 3rd, it
still answers the month containing the 3rd — a month that began before the window did — and measuring
from it would start every row on a date nobody chose. So the board begins on the first month lying
wholly inside the range, which is why "past 10 years" draws 119 months rather than 120. The two
dates in the header are the dates it really begins and ends on. Snapping the start single-handedly
moved every row, and by most on the volatile convertible indices at the top: the Shenzhen
convertible index reads +62.26% where the un-snapped arithmetic said +63.04%.

Measured 2026-10-03 over ten years: 119 months, the Shenzhen convertible index ahead at +62.26%, the
CSI convertible index at +56.15%, and the Shanghai enterprise bond 30 behind at +28.78%.

**Drawdowns** — the fifteenth page, and the asset race's other half: the same eight holdings, on the
same loader, over the same months, measured against their own highs instead of against each other.
That page says what a holding earned; this one says what it cost to earn it. A row is a filled
curve hanging below its own high-water line, deepest at its worst month, and the board's rows still
trade places — closest to its high on top — so the two halves read as a pair.

**Neither number implies the other, which is the whole reason the page exists.** Over the last ten
years the CSI 300 fund fell 33.04% and took twenty-nine months to regain its high, while the CSI 500
fund fell further — 36.10% — and was level again in nineteen. The Hang Seng fund went deepest of all
at 43.90% and healed in thirty-five. A board printing only the depth would rank those rows and say
nothing about which fall a holder could have sat through; the pair is the point, and the right
gutter carries three lines per row — where it is now, how deep it got, how long the climb took.

**The board keeps one depth scale, and that is the honest choice.** Scaling every row to its own
worst would draw the money-market fund's 0.23% as a chasm the size of the CSI 500's, on a board whose
whole claim is that those two are not comparable. So that row is a flat line pinned to its
high-water line, and the flatness is what it says. Gold and the commodity fund were still under
water when this was measured, and the board reports that kind of fall as open rather than healed.

**The depth and the climb are measured in that order**, and that is a bug this page's own probe had
first: written as one pass, a shallow dip early in the range sets the clock and the real fall is
never timed at all. Every holding came back healed in "one or two months" — on a board where one of
them took seven years. The deepest month has to be final before the months back mean anything, and
the picture cannot show the difference: the curves are drawn either way.

Adjusted, monthly and measured from each holding's own first month, all three for the reasons the
asset race gives — and unadjusted this board would be worse than wrong, because the one row that has
never fallen would be the only row with a hole in it. The roster is chosen on the page — all eight,
the four share funds, the four that are not shares, or **a list of your own** — and a share put on
that list is measured the same way, from its own first month, with the same two numbers.

**Hold odds** — the sixteenth page, and the third board on that same roster. The first two are drawn
on the range's own two ends: one way in, one way out, which answers "was this decade good". The
question a holder actually faces is a different one — walk in on a month you did not pick, hold for
the same length of time, how often does that work. So this board runs **every entry there was**: one
per month in the range, each held for the same length of time, counted once it has finished.

**One entry is luck; eighty-four of them are a rate.** A three-year hold sampled monthly across ten
years is eighty-four entries per row. They share months, and nothing here thins them out to make
them independent: that would leave three observations in a rate, and a rate built on three
observations is the luck the board exists to measure.

**An entry counts from the month it finishes.** Nothing bought in the last three years of the range
has finished, and counting an unfinished entry as a loss would bend every row downwards at the end
for no reason but the calendar. The board therefore opens on the first month an entry could have
finished on, and a row joins on the month its sixth one did — one entry is 0% or 100%, and either
number at an end of the ranking is an end it has not earned.

Measured 2026-10-02 over ten years with a three-year hold: the Nasdaq fund was ahead on all
eighty-four of its entries and the Hong Kong fund on forty per cent of them. Those are two rows the
asset race separates by ten years of total return; this board separates them by whether walking in
worked at all. Held for one year instead of three, the same decade is a different question with a
different answer — the CSI 300 fund goes from 69.0% to 59.3% and the Hong Kong fund from 40.5% to
49.1%, because a short hold catches different falls.

**One list of your own, shared by four boards.** The last group in each of those menus is a roster
you fill in yourself: type a code, a Chinese name or pinyin, and it joins. It is **one list, not
four** — a stock added on the index race is offered on the asset race, the drawdown board and the
hold-odds board, and it survives a restart, because a pick is a fact about the instrument and not
about the page it was typed on. It is also **cross-market**: none of those four boards is governed
by the market setting, so a mainland share, a Hong Kong one and a New York one sit on it together
and are fetched from the three endpoints the code asks for, which is why the search box looks in all
three markets rather than in the one in force. Under three picks the fetch is refused — a race needs
a field — and sixteen is the ceiling. A pick's name is re-resolved through the app's own instrument
table after a fetch rather than frozen at whatever the search box returned, so the same code reads
the same on this board as it does everywhere else in the app.

**A short fall's label moves out of the way.** The race renderer puts a value label outside the
bar's end when the bar is too short to hold it. For a fall that means to the left — and the axis's
proportional headroom puts the *most* negative value only about a sixth of the way into the plot,
so the label ran back over the name column and the row read as one string, "恒生科技−40.55%".
Where that would happen the label is drawn beyond the zero axis instead. It is not a rare frame:
it is the bottom row of every frame of any board with a fall on it, which includes the A+H page.

**The title is yours on every page.** Type one, or leave the box empty to get the default —
a fixed label on the whole-market chart, the fetched instrument's name on the per-stock one.
A title too long for the frame is scaled down to fit rather than clipped or wrapped, to half
size at most: clipping loses words silently and wrapping pushes the layout down into the chart,
while type that is legibly too small reads as "shorten this". The preview redraws as you type,
which is what makes that legible.

**Both pages can hide the title altogether.** It started per-stock only — the whole-market
title names a market rather than an instrument, so there was nothing to keep out of frame —
but a frame holding just the number is a legitimate look, and the switch was already free:
the panel, the persistence and the stage renderer all implemented it. Hiding gives the title's
row back to the chart: everything below shifts up into the freed row while the bottom margin
holds the lower edge still, so the chart area grows by one title row, and unchecking the box
restores the previous layout exactly rather than approximately. That exactness is why the shift
is expressed as "the title row is present or absent" (`FrameContext.ContentTop` on the per-stock
stage, `TurnoverRenderer.Row` on the whole-market indicators) rather than as an offset applied
to everything underneath.

## Design rules

**The preview and the encoder run the same renderer.** `IFrameRenderer.Draw` is handed a
`FrameContext` and draws in the video's own pixels. The preview differs by one transform
applied before the call; the encoder applies none. A renderer therefore cannot behave
differently in a preview than in a file, and "what you see is what is exported" is a property
of the structure rather than a claim to re-test whenever a renderer changes.

**A renderer is a pure function of progress, not of time.** `Draw` receives the fraction of
the way through and must not depend on having been called for earlier frames. That is what
lets the encoder decide the clock — the thing the browser version could not do — and what
makes the same fraction produce the same picture at 30 and at 60 fps.

**Every measurement is in baseline pixels against 1080×1920**, multiplied by
`FrameContext.Scale` at draw time. No drawing code contains a resolution, so a margin tuned
at 1080p is the same margin at 1440p. A font size assigned directly is the one bug this rule
exists to prevent, and its symptom — correct at 1080p, wrong at 1440p — reads as a layout
fault rather than a missing multiplication.

**All four margins mean the same thing: how far the nearest content is from that edge.**
The bottom margin measures to the *lowest thing drawn* — the data-source credit — not to the
chart's baseline. The credit, the statistic cards and the baseline above it are spaced by fixed
amounts, so the margin moves that whole stack as a unit without changing the gaps inside it.

This is worth stating as a rule because the obvious alternative was tried first and cost the
design something: while the bottom margin measured to the baseline, "250" meant a different
thing on the bottom than on the left, the two indicators needed *different* bottom margins to
look alike, and the credit's distance from the frame edge moved with the margin — so the one
element that guarantees a video says where its numbers came from could be pushed off the bottom.
With the unified meaning, `ChartMargins.Default` is a single 150/150/250 plus the top's
safe-area floor of 230 for both pages.
`FrameContext` follows suit: `CreditLine` is the anchor, and the baseline is derived from it by
`BaselineAbove(gap)` — a method, not a property, because the gap is a property of the indicator
and not of the margins.

**The top margin is the same idea, and its safe-area figure is the default rather than the
floor.** It measures from the top of the frame to the title block, and 230 baseline pixels is
where a phone's own interface stops covering the frame. That is what the margin *defaults* to,
because it reproduces the pre-margin layout exactly — but it was also the minimum, which made
the slider one-directional: a frame wanting less air could only ever get more. The range now
runs 40 to 450, crossing the safe-area line on the way down rather than starting on it.
Every top-anchored row moves through `FrameContext.TopRow(fraction)`, so the header block and
the plot shift together as one unit and the spacing inside the stack cannot change.

**The safe-area guides are drawn by the preview, not by the renderer.** The encoder does not
own a `PreviewSurface`, so the guides structurally cannot reach a file. The browser version
guaranteed the same thing twice — the guides were DOM elements outside the canvas *and* were
hidden during recording — and either mechanism could have been forgotten.

**The video's palette does not follow the app's theme.** A file is watched somewhere else. If
its colours followed the machine that made it, two people exporting the same data would get
different videos and neither preview would predict the result.

**Say what the data is, and what it is not.** The frame always carries its source, and the
reference-only disclaimer is in the Store description, on both indicator pages, in Settings
and at the end of the help document. That is four places on purpose: they are the four places
someone arrives from.

## Things learned the hard way

Facts that cost time here, kept so they do not have to be found twice. The parent shell's
own list is in `D:\code\AgolAdminKit\README.md` and still applies; these are new.

**A page's XAML root element must be the base class, not `Page`.** The XAML compiler
generates the other half of the partial class deriving from whatever the root tag names, so a
`<Page>` root with a `: StudioPage` code-behind is two declarations with different base types.
The error is `CS0263`, which names the code-behind file and says nothing about the XAML that
actually decided it.

**`Colors` is `Microsoft.UI.Colors` in WinUI 3, but the struct it yields is
`Windows.UI.Color`.** A file with `using Windows.UI;` resolves `Color` and fails on `Colors`,
which reads as a missing using rather than as two namespaces splitting one concept.

**MakePri logs `PRI249: Invalid qualifier` for every language folder whose tag contains a
hyphen** — `en-US`, `pt-BR`, `zh-Hans`, `zh-Hant` — because it tries the hyphenated name as a
`qualifier-value` pair before falling back. It is **cosmetic**: the built index holds all
fourteen `Language-*` qualifiers and all fourteen candidates for every key, which is how this
was settled rather than assumed. Renaming the help documents does not silence it; they were
never the cause.

**The help documents are named `help-<tag>.md`, with one dot.** Not because of the warning
above, but because MakePri genuinely does read dot-separated filename segments as qualifiers —
that is how `Square44x44Logo.targetsize-16.png` works. A name like `help.en-US.md` puts a
language tag in qualifier position and survives only on the fallback; `help-en-US.md` puts
nothing there.

**A `x:Uid` resource key has to carry the property it sets.** `x:Uid="SettingsMarketLabel"`
on a `TextBlock` resolves nothing — the loader looks for `SettingsMarketLabel/Text`, the
dotted key being a subtree and the property a value inside it. A bare key is only ever right
for a string read in code through `Strings.Get`. The symptom is a blank label where the
surrounding controls, written with the `.Text` suffix, are fine — which reads as a missing
translation rather than as a wrong key.

**Hiding a `NavigationViewItem` with `Visibility.Collapsed` is not the same as removing it.**
The framework keeps a place for it: keyboard navigation still reaches it and
`MenuItems[0]` — which is what this shell selects at startup — is still the hidden one. Where
a page must be unreachable, `MenuItems.Remove(item)` is the only thing that is; the market
never changes while the window is open, so nothing has to put it back.

**A WinUI 3 package carries a machine-learning runtime whether or not the app uses one.**
`onnxruntime.dll` and `DirectML.dll` account for roughly 80 MB across the architectures in
the bundle, against a 65 MB per-architecture package. Nothing here calls them. See NOTES.

**Win2D's native component is `Microsoft.Graphics.Canvas.dll`, under `runtimes/<rid>/native/`.**
Searching a package for "Win2D" or "Direct2D" finds nothing and looks like a dependency that
failed to travel.

**Measuring text in Win2D needs a `CanvasTextLayout`, and the drawing session is the resource
creator it wants.** `new CanvasTextLayout(session, text, format, 0, 0)` with `NoWrap` gives the
natural width in `LayoutBounds`, which is what shrink-to-fit needs; there is no "measure" call on
the session itself. Passing 0 for the maximum width does not mean zero — it means unconstrained.

**Win2D positions text by its layout box; a canvas positions it by the alphabetic baseline.**
`ctx.fillText(s, x, y)` puts the baseline at `y`; `DrawText` puts the *top* there. Porting
coordinates across without correcting drops every line by its ascent, roughly a fifth of the
font size, which on a five-line title block crowds the lines together and reads as spacing that
was never tuned. `CanvasTextLayout.LineMetrics[0].Baseline` is the ascent, so the conversion is
exact — it lives in `Render/Ink.cs` and nothing else is allowed to place text.

**A glow has to blur the shape, not approximate its bounding box.** Win2D has no
`shadowBlur`, and the cheap substitute — concentric translucent rectangles — is fine behind a
two-pixel bar and visibly a *box* behind a 128-pixel number. The real thing is short: record
into a `CanvasCommandList`, wrap it in a `GaussianBlurEffect` with `BorderMode.Soft`, and
composite. Its `BlurAmount` is a Gaussian sigma, about half a canvas `shadowBlur`, so a source
value of 24 comes across as 12.

**The Tencent kline endpoint ignores the start date in its `param`.** It returns the last
`count` bars ending at the end date, so `count` is what decides how far back it reaches and the
range has to be trimmed client-side. Counting calendar days over-fetches, which is what you
want; trusting the server to honour the start silently returns a different range than asked for.

**Each bar in that response is a heterogeneous array — field 6 is an empty JSON object.**
Deserializing a bar as `string[]` therefore fails on *every* response rather than on an unusual
one. Read by index with `JsonElement` and touch only the fields you need: 0 is the date, 8 is
turnover in 万元.

**It serves JSON under `Content-Type: text/html`.** The content type is no use as a check; the
envelope's own `code` field is.

**A verification script has to follow the same routing table the app does.** An outside script that
recomputes a board's numbers is the only check on them, and the easiest way to write it wrong is to
hard-code the generic endpoint: `hk` codes are answered by `hkfqkline`, `us` codes by `usfqkline`,
and asking the generic one for a Hong Kong share returns a *different series* rather than an error.
The board came out at −66.86% for one pick and the script at −69.83%, which is close enough to look
like rounding and was enough to flip "healed in thirty-five months" into "not healed yet". Both
sides were confidently reporting and neither was failing.

**`CultureInfo.CurrentCulture` does not follow the language the app is showing.** A language
pinned in Settings goes through `PrimaryLanguageOverride`, which redirects *resource* lookup; the
thread's culture still follows the operating system. On an English Windows showing a Chinese
interface, `CurrentCulture` is `en-US` — which rendered a calendar's month as "Jun" and its
weekday row as "M T W T F" inside an otherwise Chinese frame, in a video meant for a Chinese
audience. The fix is the trick this shell already uses to pick the help document: let the
resources name the answer. `CultureName` is a per-language string, so whichever language MRT
resolved — including through its own fallback rules — is the one that answers, and there is one
resolution instead of two free to disagree. `Strings.Culture` is the only culture user-visible
words may be formatted with.

Numbers are the exception and deliberately use `InvariantCulture`: comma-grouped thousands are
what this audience reads on a financial chart, and following the interface language would print
"23.807" in German and "23 807" in Russian for the same series. Words follow the interface,
magnitudes do not.

**`Measure` is an inherited method on every `UIElement`, so it is a poor name for a type.** A class
called `Measure` compiles everywhere except inside a `Page`, where `Measure.Turnover` resolves the
layout method and fails with `CS0119: 'UIElement.Measure(Size)' is a method, which is not valid in
the given context` — an error that names layout and says nothing about the type that caused it. The
same trap waits for `Arrange`, `Content` and `Resources`. It is now `Metric`.

**Win2D hands back pixels top-down; Media Foundation's uncompressed RGB samples are bottom-up.** Feed one to the other and every frame comes out mirrored about the horizontal axis. Nothing else notices: the container is a valid MP4, `mvhd` carries the right duration, `stsz` holds exactly the frames that were drawn, and the export takes the time it should. **A video can be upside down while every property you can read out of its container is correct**, which is why this survived a verification pass that checked all of them. What found it was decoding the last frame and comparing it against a cover export of the same frame. Flipping the decoded frame vertically took the mean absolute difference against the cover from 26.99 to **2.29** — the residue is H.264 — against 29.21 for a horizontal flip and 12.85 for 180°. One axis, unambiguously. The fix is in `VideoExporter.FlipRows`, on the pixel buffer — not a transform on the drawing session, which would have made the file differ from the preview in a way nobody could see.

**`MediaTranscoder.HardwareAccelerationEnabled = true` hangs `PrepareMediaStreamSourceTranscodeAsync` on this machine, silently.** This cost the better part of a day, because every observable symptom points somewhere else: the process stays alive and responsive, no exception is thrown, no `MediaStreamSource.Starting` is ever raised, no sample is ever requested, and the `.mp4` the code created just before the call is deleted by its own `catch`. From outside it is indistinguishable from a folder picker waiting for input — which is what it was taken for, twice. What found it was a `CrashLog.Note` before and after each `await` in the method: the trace stopped dead on the line between them. Setting the flag false, the same 2,700 frames encode in about 28 seconds. The lesson is not "do not use hardware acceleration" — it is that **a hung `await` reports nothing at all, and a trace is the only instrument that can see it**.

**Reading an MP4 while it is still being written produces a confident wrong answer.** A container check run a few seconds after `TranscodeAsync` returned found `ftyp`, `uuid` and `mdat` and no `moov`, which reads as a corrupt or fragmented file. The `moov` was simply not flushed yet; the same file checked a minute later is complete and correct. Stat the file's size twice, or wait, before concluding anything about a container.

**`System.Drawing` is enough to generate a complete MSIX logo set, including the `.ico`.**
Writing PNG-compressed entries (the Vista `.ico` form) rather than BMP entries is what keeps
the alpha correct; the 256-pixel entry records its size as `0`, because the field is one byte.

## Layout

```
src/MarketMotionStudio/
  Market/          TencentKline (the only HTTP to a quote source), RankingSource (the one
                   ranking call, to a second source, and why it is a second source), TurnoverSeries,
                   InstrumentCalendar (one instrument's bars as that record),
                   HistoryWalk (years of closes, walked backwards a page at a time),
                   DcaPlanner (the walk, then the plan) and PositionLoader (the walk, then the holding),
                   CandleSeries (daily/weekly/monthly bars, and the two animations' shapes),
                   MarketCaps (the fifteen-per-market field, and today's value turned into a history),
                   AhPremium (the A+H pairs, and the one page that must not use adjusted prices),
                   ExtremeDays (one instrument's largest single-day moves, rows that are days),
                   FxRates (the pairs, their monthly bars, and the corridor's arithmetic),
                   IndexRace (twelve indices from three markets, each measured from its own first month),
                   AssetRace (eight asset classes as funds, and the one page that must use adjusted prices),
                   BondRace (nine bond indices, the opposite ruling on adjustment, and the whole-month snap),
                   Drawdown (the same eight funds measured against their own highs: depth and the climb back),
                   HoldOdds (every entry in the range, each held the same length of time, and the share that gained)
  Render/          VideoFormat, ChartMargins, SafeArea, FrameContext, IFrameRenderer,
                   Palette, Ink (text and effects), AnimationPlan and Easing,
                   Metric (turnover vs daily change), TurnoverRenderer (shared chrome)
                   with BarRaceRenderer, CalendarHeatmapRenderer and IntradayRenderer
                   (one session's cumulative curve — a clock, so it advances linearly),
                   StageRenderer,
                   DcaRenderer, PositionRenderer, CandleRenderer, Backdrop (the frame's ground),
                   SectorRaceRenderer (ranked bars, shared by the race, the market-cap board,
                   the extreme-day board, the index race, the asset-class board, the bond board
                   and the hold-odds board),
                   UnderwaterRenderer (ranked curves, one depth scale for the whole board),
                   FxCorridorRenderer (a row that is a range, with the rate as a marker on it),
                   FrameExporter (one frame to PNG)
  Views/           PreviewSurface (the letterboxed 9:16 canvas), VideoSettingsPanel, Dialogs
  Pages/           StudioPage base, the indicator pages, the two buy-at-a-price pages,
                   Settings, Help, Playback
  Localization/    Strings lookup and the language override
  Strings/<bcp47>/ Fourteen Resources.resw
  Assets/Help/     Fourteen help-<tag>.md and media/<tag>/, their pictures
  Diagnostics/     Crash log
tools/
  new-icons.ps1          Generates every image the manifest declares
  store-screenshots.py   Drives the running app; captures the Store screenshots, one set per language
  help-media.py          Crops those captures into the help document's page pictures
  port-help-images.py    Inserts the pictures into all fourteen help documents, by chapter number
  localize-instruments.py, localize-appname.py
                         Add one key to all fourteen resw at once — idempotent, key-order checked
  port-*-resw.py, port-*-help.py
                         Port one feature's strings and help section from the sibling project
  port-store-listing.py  Rewrites the three paragraphs the Store listing repeats in fourteen
                         languages — the page list, what's new, the feature bullets
  port-ahpremium-*.py    The same, for the A+H page — including the 40 A-leg names it needed
  port-extremedays-*.py  The same, for the extreme-day board
  port-fxcorridor-*.py   The same, for the currency corridor
  port-indexrace-*.py    The same, for the index race
  port-marketcap-*.py    One page's strings, instrument names and help chapter, into all fourteen
                         (the pool script carries the 93 candidates that only need zh + en)
  verify-*.py            Drive the UI and assert the feature behaves as documented
  drive-*.py             Drive the app end to end for a smoke run
```

`Render/` has no dependency on XAML and `Views/PreviewSurface` is the only thing that knows a
preview exists. That split is what the first design rule above rests on.

`Render/Ink.cs` is the only place text is positioned or blurred, for the reason in "Things
learned the hard way": both operations differ from the canvas originals in ways that are easy to
get subtly wrong and hard to spot afterwards.

`TurnoverRenderer` is the abstract base holding everything the two whole-market forms share — the
background, the title block with its running total, the closing statistic cards, the credit and
the progress bar — with one abstract member for the plot area. That mirrors the source, which has
a shared `drawHeader`/`drawStats`/`drawProgress` and branches only on the chosen view.

`StageRenderer` draws an empty frame — the background, a gridline, the credit — and is what the
Stock Volume page shows *before* anything is fetched. It is *not* a shared base across indicators —
the two source tools are separate implementations with different layout anchors, and an earlier
assumption here that they could share a stage was wrong: the whole-market forms put their plot top
at a fixed fraction of frame height, while the per-stock one stacks two panels whose tops and
bottoms hang from different anchors entirely.

## Building

Requires Visual Studio 2026 (18.x), the Windows SDK 26100, and the .NET 10 SDK.

```powershell
$msb = "C:\Program Files\Microsoft Visual Studio\18\Professional\MSBuild\Current\Bin\MSBuild.exe"

# Debug build
& $msb src\MarketMotionStudio\MarketMotionStudio.csproj /restore /p:Platform=x64 /p:Configuration=Debug

# Store submission package, x64 and ARM64 in one bundle
& $msb src\MarketMotionStudio\MarketMotionStudio.csproj /restore `
  /p:Configuration=Release /p:Platform=x64 `
  /p:AppxBundlePlatforms="x64|arm64" /p:AppxBundle=Always `
  /p:UapAppxPackageBuildMode=StoreUpload /p:AppxPackageSigningEnabled=false `
  /p:GenerateAppxPackageOnBuild=true /p:AppxPackageDir="$PWD\artifacts\\"
```

The second command produces `artifacts\MarketMotionStudio_<version>_x64_arm64_bundle.msixupload`,
which is the file Partner Center takes.

Use `Build`, not `Rebuild`, when the app may be running: `Rebuild` cleans first, the clean
succeeds, the copy back fails on the locked exe, and the output folder is left without
`runtimeconfig.json` and `deps.json` — at which point the apphost claims .NET is not
installed, which is false.

To run a local build, enable Developer Mode and register the loose files:

```powershell
cd src\MarketMotionStudio\bin\x64\Debug\net10.0-windows10.0.26100.0
Add-AppxPackage -Register .\AppxManifest.xml
```

Re-run `tools\new-icons.ps1` only after changing the palette; the generated files are
committed, so a fresh clone packages without it.

## Languages

The interface ships in fourteen: English, German, Spanish, French, Italian, Polish,
Portuguese (Brazil), Czech, Turkish, Russian, Japanese, Korean, Simplified Chinese and
Traditional Chinese. It follows Windows by default and can be pinned in Settings; the change
takes effect at the next start, offered there as a button, because `x:Uid` is resolved when
XAML loads and never re-read.

Translations live in `Strings\<bcp47>\Resources.resw` and the SDK picks them up from the
folder name, so a language is added by adding a folder. The manifest declares `x-generate`
rather than a list, so it cannot disagree with what is there. The help page carries the manual
in the same fourteen, and which document it opens is named by a resource key rather than
worked out from the current culture — one answer to the question instead of two that can
disagree.

**The product name is translated, in exactly two markets.** This departs from the parent
shell's rule that a product name is never translated, and it is deliberate: the product was
commissioned with a Chinese name and an English one, so `AppTitle.Text` carries
「行情指标动画工作室」 in `zh-Hans` and 「行情指標動畫工作室」 in `zh-Hant`, and the English
name `Market Motion Studio` everywhere else. The package identity stays `MarketMotionStudio`
in every market and is never shown to users.

The same name is published a second time as `AppDisplayName`, because the two are read by
different machinery. `AppTitle.Text` is a *property* identifier — `x:Uid` owns it, the window
title uses it — and a file cannot hold both `X` and `X.Text`, so the manifest cannot point at
it. `AppDisplayName` is a plain identifier, and the manifest reads it as
`ms-resource:AppDisplayName` for the Start menu, the Apps list and Settings, which is what
makes the shell name follow the OS display language. Before that, all three carried the
literal `MarketMotionStudio` — the identity, which is not a product name and reads the same
everywhere. A display language the app does not ship falls back to English: `DefaultLanguage`
in the csproj is pinned to `en-US` for exactly that, and the resource index records
`Language-EN-US` as the default candidate.

Every language carries the same keys in the same order. All fourteen currently report 732 keys
with no encoding damage, and all fourteen help documents carry the same twenty-five sections in
the same order — the equality the cross-language check rests on.

## Appearance

Light, dark, or whatever Windows is set to, from Settings. It changes as you pick it — a theme
is re-read by elements already on screen, which the language is not. The window uses Mica; the
preview draws an opaque frame of its own inside it, because what the video will look like must
not depend on the colour of the wallpaper behind the app.

## The frame's backdrop

What every frame is drawn on is a setting: the page's own gradient, a two-colour gradient of the
user's, or a picture — from the computer or from Windows' own wallpapers, the last six kept. One
setting for all seventeen pages, and it reaches the preview, the cover PNG and the MP4 alike, which
is the single-render-path rule restated: one renderer draws all three.

**It travels in `FrameContext`, not through a global the renderers read.** Each draw is handed
the backdrop it is to fill with, and an export takes one snapshot at the start, so changing the
setting while an encode is running cannot produce a video that changes face partway through. A
renderer reading a global would have made that possible, and it would have looked like a corrupt
file.

**The two sliders run in opposite directions, on purpose.** A picture is faded *towards* the
page's own gradient, so a higher number is more of the default: a picture arrives carrying its
own colouring and has to be pushed back. A colour is drawn *over* that gradient at an opacity,
so 100 is the two colours as chosen and lower lets the page through. Each appears only under its
own kind, so only one is ever on screen.

Two details a second implementation would get wrong. A picture is cached **per device**, because
a `CanvasBitmap` belongs to the device that created it and the preview and the encoder do not
share one — a single cache would hand each the other's bitmap. And a picture that fails to load
has its path remembered anyway, or a 2,700-frame export retries it 2,700 times.

## Settings are remembered, results are not

Range, duration, resolution, frame rate, quality, margins, the typed title, the chosen form, the
guides — and on the plan page, the instrument, the cadence and the amount per buy — all
persisted, because re-entering them every session is the friction that makes a feature
go unused. A fetched series is deliberately not: it belongs to one moment, so keeping it would mean
deciding how long it stays true, and a stale chart is worse than an empty one.

The market is persisted too, and like the language it needs a restart — see "Markets" above.
A code saved under one market is not silently fetched under another: the per-stock page, the
calendar and the plan page all refuse it and name the market they are on — the plan's saved
instrument falls back to that market's first preset rather than requesting a code the current
venue never quoted.

Two details that are not incidental. Keys are **prefixed per page**, because the video and layout
controls are one shared control used by both indicators — without the prefix, tuning the margins for
one chart would silently retune the other. And writes are **coalesced over 400 ms**, because
dragging a slider raises a change per step and a settings write per step is a hundred writes for one
gesture.

## Covers, and why they matter more than they look

**Save cover PNG** writes whichever frame the preview is parked on, at the full export resolution.
Useful on its own for a post thumbnail — and it is the first thing here to render **off-screen**,
which is the mechanism the video encoder needs: a `CanvasRenderTarget` at the real size, the
production renderer drawn into it with no transform, the result read back. If a cover comes out
matching the preview, the encoder's drawing half is already proved and only its muxing half is new.

It also tests the single-render-path rule from the other side: the preview draws through a scaling
transform, a cover draws at 1:1, and a cover that does not match the preview means that rule has been
broken somewhere.

## Where videos go

Exports are written to a folder chosen through a picker and remembered as a future-access
token rather than as a path. This is not incidental: **MSIX silently redirects
`%LOCALAPPDATA%` writes** into the package container while the path string the app holds still
points at the original location, so the browser tools' habit of writing to
`桌面\A股成交额视频\` would produce a file the app reports having written where the user
cannot find it. A folder the user picked is not redirected. Nothing is chosen up front; the
first export asks and then remembers.

## Not done yet

- **The per-stock export at 1440p60 has run once** (a 90-second 242-minute intraday file and a
  daily one, both verified upright against their covers) — but not the full format matrix the
  whole-market page has been through, nor the Beijing venue, nor a cancel mid-export. See NOTES.
- **The DCA plan page has had one of everything, once**: one fetch (沪深300ETF, daily ¥100,
  past three years — 726 buys; a ten-year plan of 2,429 buys fetched by hand the same day),
  one cover, one 1080p30 export with its boxes verified. Not the Hong Kong or US preset
  lists, not the weekly or monthly cadences, not another format. See NOTES.
- **The extreme-day board has been fetched and read at one span, on two instruments** (A-shares, ten
  years, 32 checks: 24 candidate days over 2,427 trading days, the largest move recomputed from the
  source's own bars and matching to two decimals), and its preferences survive a restart. It has not
  been exported at any format, its custom span has not been exercised, and Hong Kong and New York
  have not been driven through it. See NOTES.
- **The index race has been fetched and read on two groups, at one span** (all twelve and New York's
  three, ten years, 37 checks: 120 months, and the leader and the loser of all twelve recomputed from
  the source's own bars and matching to 0.01 of a percentage point). It has not been exported at any
  format, its custom span has not been exercised, and no span long enough for a row to *join* late
  has been driven through it — every group is complete inside a ten-year window, so the absence rule
  is verified in the source and in the ranking, not yet on a frame. See NOTES.
- **The asset-class board has been fetched and read on two groups, at one span** (all eight and the
  four share funds, ten years, 41 checks: 120 months, and the leader and the loser of all eight
  recomputed from the source's own **adjusted** bars and matching to 0.01 of a percentage point —
  which is what proves the adjustment, since unadjusted the loser would read 0.00% and the leader
  would read one fifth of what it earned). It has not been exported at any format, its custom span
  has not been exercised, and the English interface has not been driven. See NOTES.
- **The Store screenshots show seven pages, not fourteen.** `tools/store-screenshots.py` predates
  the candle page, the market-cap board, the A+H page, the extreme-day board, the currency corridor,
  the index race and the asset-class board, so the gallery has none of the seven. The listing copy
  says ten charts in all fourteen languages — it predates the last three pages, and the listing is
  written at release time — so the copy and the
  gallery disagree until all five captures are taken. The copy deliberately runs ahead of the package: it is
  written for the version being prepared, and it must not be uploaded before that package is.
- **The A+H page has been fetched and read at two spans** (three years and the longest, twenty-two
  checks), and its headline number was recomputed independently from the source — the dearest premium
  matched the page to 0.04 of a percentage point, which is what proves the unadjusted prices, the
  exchange rate and the month grouping all three. Its English interface has not been driven, no export
  has been run at any format, and the custom span has not been exercised. See NOTES.
- **The market-cap board has been fetched and read on one market, at two spans** (A-shares, one
  year and ten years, seventeen checks), and three moments of the ten-year run were captured to
  confirm membership changes. Hong Kong and New York have not been driven through the page; neither
  has the custom span, nor an export at any format. The English interface was checked for the name
  column's width, which is the thing a company name could break.
- **The console shows a log line per request and the walk logs one per page**, which for a
  ten-year fifteen-listing board is about ninety lines. It is not a problem, but it is the
  loudest thing this app does and worth knowing before reading a log.
- **Only the A-share and US candle pages have been fetched end to end**, each 18 checks. The
  Hong Kong one has not; neither has weekly or monthly through the page, nor an export at any
  format other than the default.
