# Market Motion Studio

This app turns A-share market indicators into vertical videos for phones. You pick a period, look at the preview until it reads well, and export an MP4. Nothing else has to be installed.

## Choosing a market

Settings picks which market the app takes its quotes from; A-shares by default. A change takes effect after the app is restarted.

- **A-shares**: all eight pages are available.
- **Hong Kong**: the return matrix and the gain-loss calendar work; the sector race runs on the four Hang Seng sub-indices; **there is no whole-market turnover figure, so that page is hidden**.
- **United States**: the return matrix and the gain-loss calendar work; the sector race runs on ten SPDR sector ETFs; the volume page keeps its daily mode only, because the minute endpoint serves no US data; **amounts are quoted in dollars, and the whole-market turnover page is hidden**.



## Moving between pages

The two buttons at the left of the title bar step back and forward through the pages you have visited, as a browser does — **Alt+Left** and **Alt+Right**, or the side buttons on a mouse.

- A page is kept as you left it, so going back to one returns to the period and the preview as they stood, not to a page opened afresh.
- Picking a new page clears what lay ahead, as a browser does.
- They work with the navigation pane collapsed as well, which is when the preview needs the width most.

## Market Turnover

The whole market's daily turnover: the Shanghai and Shenzhen composite amounts added together, one bar per trading day.

- Only days on which every included market traded are kept, so a single market's holiday cannot make the total appear to collapse.
- A session still in progress is left out. An unfinished day holds only its opening auction, which would draw as a bar flat against the axis.
- Or look at one slice alone: either exchange, either main board, STAR, ChiNext. Main boards are derived as the exchange total less its growth board; the BSE 50 remains a constituent measure.
- Only the A-share market yields a whole-market total. On Hong Kong or the United States the page is taken out of the navigation.

## Candles

One instrument's prices as candles: daily, weekly or monthly, drawn four ways, with its averages and its volume underneath.

- **Period** decides how much market time one candle covers — a day, a week or a month. Changing it fetches again, because the three are separate series on the source.
- **Style** decides how the same four prices are drawn: candles, OHLC bars, a closing line, or a closing area. Switching between them re-fetches nothing.
- **Motion** is either candles arriving one after another until the whole range is laid out, or a fixed window of them walking forward. The second is what keeps a candle wide enough to read on a long range, and how wide is the **window** setting.
- Moving averages MA5, MA10 and MA20 can be laid over the candles; the volume panel underneath can be turned off, and the price panel takes the room back.
- A week or a month still in progress is left out. A candle made of three days is not a week.
- Every market is read on its adjusted series, so a split day is not drawn as a fall, and neither is a dividend.

## Volume and Turnover

One stock's volume against its turnover rate, as two stacked panels.

- Across trading days, volume and turnover rate are proportional, so the two panels have nearly the same shape. Within one day, per-minute volume and cumulative turnover look genuinely different, which is the more interesting picture.
- The intraday source only keeps the last few trading days, so that mode offers those rather than an arbitrary date.
- Minute data is served for A-shares and Hong Kong only; on the United States that mode is not offered.

## Sector Race

![The page in full: preview on the left, scrubber below, settings on the right.](media/sector-race.png)

A set of sectors or stocks, drawn as horizontal bars that overtake one another, the order changing right up to the last frame.

- Two measures: the interval's gain/loss percentage, and its turnover in hundreds of millions of yuan. Switching is just a re-colour of the same data; it does not fetch again.
- Four rosters: SW Level-1 industries, hot themes, custom (tick the boxes), and individual stocks (search to add). The custom roster starts filled with the SW Level-1 set.
- The built-in rosters follow the market: SW Level-1 industries and hot themes for A-shares, the four Hang Seng sub-indices for Hong Kong, ten SPDR sector ETFs for the US. The custom and stock rosters exist on every market.
- The interval can be 1, 3, 6 or 12 months, or a custom start and end date.
- A roster has a minimum and a maximum size — too few bars is no race, too many crowd into a blur.




## Market Cap Race

One market's fifteen largest companies as horizontal bars ranked by total market value, the
order changing to the last frame. Sampled monthly.

- **The board is re-ranked every period.** A fetch first asks the source for the current ranking
  by market value, takes the top two hundred as its field, and adds the large caps that used to be
  on the board and have dropped out of that ranking; each period then shows the fifteen largest in
  that field. So members really do come and go — 2016 was oil and banks, 2026 has added 茅台,
  宁德时代 and 工业富联. A field written into the program missed a company that listed and went
  straight to the top, so the field is asked for rather than remembered.
- **A past market value is derived**: today's total market value times the adjusted price ratio
  over the range. A bonus issue or a split cancels in the adjusted series, so a ten-for-ten does
  not read as the company halving; a dividend does not cancel — it is reinvested, so a heavy
  payer's past value reads low and it looks like it grew faster than it did. Only the last frame's
  figure comes straight from the source.
- **A company that had not listed yet grows out of nothing**: 宁德时代 and 工业富联 listed in 2018,
  and they rise from the baseline on the day they joined rather than holding a place in advance.
- **The interval is a month, not a day** — a hundred and twenty periods over ten years, twelve over
  one, and the frame's own header counts months. A market-cap ranking is a slow variable, and a
  monthly sample gets a whole history in one request.
- **Each market has its own fifteen.** The three are never mixed: their money is not one money,
  and a board of mixed currencies means nothing. Hong Kong and New York keep a fixed field, because
  no ranking this app can reach serves them.




## AH premium

How much more a company's mainland listing costs than its Hong Kong one, for the firms
listed on both sides — month by month, as bars that overtake one another.

- **Premium = A price ÷ (H price × HKD/CNY) − 1.** Nothing here is derived: both legs are prices
  actually paid at the same moment, which is why this is the one page that must fetch
  **unadjusted** prices. A backward-adjusted series inflates recent prices, and two markets
  adjusted separately cannot be compared — ICBC's A share sells at 8.28 on the screen and the
  adjusted series reports 13.34, which turns a +26% premium into +245%.
- **The frame draws the fifteen dearest**, so the bars grow to the right — even the fifteenth
  carried a premium above twenty per cent. Only two of the sixty-nine go the other way, their H
  shares above their A shares, and both sit at the bottom of the list, past where the frame looks.
- **The longer the span, the fewer companies qualify.** Sixty-nine well-known dual listings are
  candidates, but only a pair with both legs covering the whole span is drawn: one whose Hong Kong
  listing is under two years old drops out. So "past 3 years" carries more pairs than "longest",
  and the count in the status line is the count on the frame.
- **Sampled monthly, not daily.** "Longest" is about nine years, and the limit is the exchange
  rate series, which reaches back to 2016 only. The three legs close their months on different
  days, so they are grouped by calendar month and the month's last print is taken, rather than
  intersected on the date itself.
- **The list is built in.** Neither source answers "which mainland listings also have a Hong Kong
  listing", so the pairs are written down — and checkable: every one was read back from the quote
  endpoint on 2026-10-02, and 海通证券 is what that check removed, its H shares delisted after the
  merger into 国泰海通. Kept, it would have been a lane that stayed empty for the whole video.

## Return Matrix

![The page in full: preview on the left, scrubber below, settings on the right.](media/monthly-matrix.png)

Monthly bars laid into a grid: year mode shows one instrument's decade of seasonality, compare mode puts several side by side to show rotation.

- Year mode: pick one instrument (search, or a preset broad index); the span is 1-10 years or all. One request returns a decade of monthly bars.
- Compare mode: 2-14 instruments from a roster (Level-1 industries / themes / broad indices / custom / stocks) side by side, across 6 to 48 months.
- The grid lights cell by cell in time order; the close-out shows the strongest and weakest months in the span, among other stats.
- Monthly data covers a decade in one go, so there is no daily-style day cap here - but too many instruments run past the frame.

## Gain-loss calendar

![The page in full: preview on the left, scrubber below, settings on the right.](media/gain-calendar.png)

Any A-share stock or index, its daily rise or fall laid into calendar cells by month: red for up, green for down.

- Search by code, name or pinyin; presets are broad indices. Only instruments on the market you have selected.
- The watchlist is shared with this app's stock page - a favourite added in either place shows in both.
- The interval is 1, 3, 6 or 12 months, or custom; a single instrument is still bound by the ~640-calendar-day fetch limit.
- The close-out stats give the count of up and down trading days.

## DCA Plan

![The page in full: preview on the left, scrubber below, settings on the right.](media/dca-plan.png)

Buying one instrument for a fixed amount on a fixed cadence — every trading day, every week or every month — and watching what the discipline turned into.

- The one-tap instruments follow the market: broad and gold ETFs on the A-share market, the Hong Kong tracker funds, SPY, QQQ and GLD in the United States.
- The amount and the cadence are yours to set; the span is three, five or ten years, or as far back as the data goes (about thirteen years).
- Returns are computed on backward-adjusted closes, with no fees. The result describes the price series, not a bill anyone could have executed.
- Besides three, five and ten years and the longest span, the range can be **Custom**: give a start and an end date, then press Fetch. About 35 years is reachable — the source serves roughly 640 calendar days per request, and the walk makes at most twenty of them.

## Holdings Return

![The page in full: preview on the left, scrubber below, settings on the right.](media/position.png)

One purchase, held for years — a million into 中国平安 in 2015, say — animated as what the value and the return did.

- The one-tap names follow the market: the A-share list is the stocks people actually say they have held (Ping An, Moutai, CMB...), Hong Kong gets Tencent, HSBC and the Tracker Fund, the United States gets Apple, Berkshire and SPY.
- The initial capital and the holding span are yours to set; the span is three, five or ten years, or as far back as the data goes (about thirteen years).
- Returns are computed on backward-adjusted closes — dividends reinvested, no fees. The backward adjustment anchors at the listing and accumulates dividends forward, so a heavy payer's early years never turn negative the way the forward-adjusted series can.
- The same **Custom** span works for the holding: give two dates, then press Fetch. If the instrument listed later than the date you asked for, the holding starts on its first trading day.

## Video

The frame is always 9:16. Everything else is yours to set.

- Duration changes the pacing rather than trimming the animation: the opening, the growth of the bars and the closing statistics are re-apportioned across whatever length you choose.
- Margins are written against a 1080×1920 frame and scaled to the resolution you export at, so a layout tuned once holds at every size. The left margin also decides where the axis labels land — set it too small and the numbers leave the frame.
- The safe-area guides outline what a phone app covers with its own interface. They are drawn in the preview and never in a file.

## Where videos go

Exports are written to a folder you choose through a picker. Until one is chosen the first export asks, then remembers; Settings can change it or forget it.

## Background picture

The Settings page can put a picture behind the window, dimmed. Cards and panels stay opaque and the navigation pane lets only a little through, so the picture shows mainly around them; the video preview has its own solid backdrop and is unaffected.

- Pick one from your computer, or use one of the wallpapers and lock-screen pictures Windows already ships.
- A picture you pick is copied into the app's own folder, so moving or deleting the original does not affect the background.
- The dimming slider sets how far the picture is pushed back, from 30% to 95%.
- No picture is shown while high contrast is on.
## Animation background

The Settings page can change what the animation is drawn on: the built-in gradient, two colours of your own, or a picture. It applies to the preview, the exported video and the cover image alike — all three are drawn by the same renderer, so there is no "looks good in the preview, different in the file".

- Choosing colours gives you a top and a bottom stop, and the frame fades from one to the other. Dark suits these frames: every tone of text in them is light, and a light background makes the numbers hard to read.

- The opacity slider sets how much of the two colours is used: at 100% the frame is the pair as chosen, and lower lets the page's own dark gradient through from underneath. It is what keeps a light pair readable.

- Choosing a picture works the same way as the window's: pick one from your computer, or use a wallpaper Windows already ships. One you pick is copied into the app's own folder.

- The picture fills the frame and the surplus is cropped, so its proportions are never stretched.

- The dimming slider sets how far the picture is pushed back towards the frame's own backdrop, from 20% to 95%.

## Data, and what it will not tell you

Quotes come from Tencent Finance's public endpoints, and the frame always says so. These videos describe what has already traded. They are for reference only and are not investment advice.

- Turnover is converted to hundreds of millions of yuan, and volume switches to a larger unit once the numbers warrant it, so the axis stays readable.
- Turnover is converted to hundreds of millions — of yuan on the mainland and in Hong Kong, of dollars in the United States. Each market keeps its own currency.
- A range longer than about 640 calendar days is refused rather than quietly truncated, because that is as much as one request to the source returns.

## Updating

When the Microsoft Store has a newer version, an **Update** button appears beside Settings in the navigation pane; one click installs it.

- It only appears when the Store really has a newer version. A development or sideloaded build never sees it, and that is expected.
- The app closes while the update installs and starts again on the new version, and the button is gone. If an export is running, it asks first.
- If it cannot install, it says why — Wi-Fi only, battery too low — and the update can also be installed from the Microsoft Store.

## Something wrong?

Write to gaqo@outlook.com and say what you were doing and what you expected instead. The version number is on the Settings page.
