# Market Motion Studio

This app turns A-share market indicators into vertical videos for phones. You pick a period, look at the preview until it reads well, and export an MP4. Nothing else has to be installed.

## Choosing a market

Settings picks which market the app takes its quotes from; A-shares by default. A change takes effect after the app is restarted.

- **A-shares**: all seven pages are available.
- **Hong Kong**: the return matrix and the gain-loss calendar work; the sector race runs on the four Hang Seng sub-indices; **there is no whole-market turnover figure, so that page is hidden**.
- **United States**: the return matrix and the gain-loss calendar work; the sector race runs on ten SPDR sector ETFs; the volume page keeps its daily mode only, because the minute endpoint serves no US data; **amounts are quoted in dollars, and the whole-market turnover page is hidden**.

## Market Turnover

The whole market's daily turnover: the Shanghai and Shenzhen composite amounts added together, one bar per trading day.

- Only days on which every included market traded are kept, so a single market's holiday cannot make the total appear to collapse.
- A session still in progress is left out. An unfinished day holds only its opening auction, which would draw as a bar flat against the axis.
- Or look at one slice alone: either exchange, either main board, STAR, ChiNext. Main boards are derived as the exchange total less its growth board; the BSE 50 remains a constituent measure.
- Only the A-share market yields a whole-market total. On Hong Kong or the United States the page is taken out of the navigation.

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

## Holdings Return

![The page in full: preview on the left, scrubber below, settings on the right.](media/position.png)

One purchase, held for years — a million into 中国平安 in 2015, say — animated as what the value and the return did.

- The one-tap names follow the market: the A-share list is the stocks people actually say they have held (Ping An, Moutai, CMB...), Hong Kong gets Tencent, HSBC and the Tracker Fund, the United States gets Apple, Berkshire and SPY.
- The initial capital and the holding span are yours to set; the span is three, five or ten years, or as far back as the data goes (about thirteen years).
- Returns are computed on backward-adjusted closes — dividends reinvested, no fees. The backward adjustment anchors at the listing and accumulates dividends forward, so a heavy payer's early years never turn negative the way the forward-adjusted series can.

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
