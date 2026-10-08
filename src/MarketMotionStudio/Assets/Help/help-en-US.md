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

- **Your own list.** The last entry on the board menu is the list you keep — indices and shares
  side by side, shared with the four roster boards. Only mainland codes can be added up: turnover
  is reported in each market's own currency, so a Hong Kong or New York name is left out, and the
  status line says how many. A day is on the axis if *any* member traded; a member with no row
  for that day — halted, or not yet listed — contributes nothing. That is deliberately the
  opposite of the rule the boards above use: an index never halts, a share does, and dropping the
  day would make a halt look like a day on which nothing traded anywhere. This board **adds its
  picks up**, so clicking a name includes it in the total or leaves it out — and it opens on the
  **first** pick alone. The list is usually the one kept for the ranking boards, where a dozen
  names is an ordinary list; a dozen names added together is a total about nobody in particular.
- **The change under a basket** is the equal-weighted average of the members' own daily changes,
  each measured against its own previous close. Equal-weighted because a list is not a portfolio:
  there is no holding size to weight by.
- **One session, minute by minute.** The third form is a separate fetch: the running total from
  the opening bell to the close on a single day. The source keeps the last five sessions and no
  more, so no range is offered — the frame names the day it drew. The curve stops at 15:00,
  because the half hour the endpoint adds after that is after-hours trading, which the daily
  figure leaves out too. The four closing cards are the day's total and what share of it fell in
  the morning, the afternoon, and the last half hour — a chart of *when* money moved, so three of
  the four are shares rather than amounts. The BSE 50 is the one board that reports minutes with
  no amount column at all, and it is refused rather than counted as nothing.

## Candles

One instrument's prices as candles: daily, weekly or monthly, or minute candles for one named trading day — drawn four ways, with its averages and its volume underneath.

- **Period** decides how much market time one candle covers — a day, a week or a month. Changing it fetches again, because the three are separate series on the source.
- **1, 5 and 15 minutes** draw one trading day: the session from the open to the close, laid out on an axis that runs by the clock and leaves the ninety minutes nobody traded off it, so the morning and the afternoon meet across a hairline where the break was. The source keeps minute candles for Shanghai and Shenzhen only, and only for the last few sessions — about four days at one minute, seventeen at five, fifty at fifteen — so **trading day** is a list of the days it still has rather than a calendar. Picking another of them only draws it again.
- **Style** decides how the same four prices are drawn: candles, OHLC bars, a closing line, or a closing area. Switching between them re-fetches nothing.
- **Motion** is either candles arriving one after another until the whole range is laid out, or a fixed window of them walking forward. The second is what keeps a candle wide enough to read on a long range, and how wide is the **window** setting.
- **A scrolling window opens out at the end.** As the closing stretch begins the window widens back towards the first day of the range, so the frame the animation stops on is the whole span rather than the last few dozen days of it.
- Moving averages MA5, MA10 and MA20 can be laid over the candles; the volume panel underneath can be turned off, and the price panel takes the room back.
- A week or a month still in progress is left out. A candle made of three days is not a week.
- Every market is read on its adjusted series, so a split day is not drawn as a fall, and neither is a dividend.
- **Range** follows the period: daily offers 3, 6 or 12 months and 3, 5 or 10 years; weekly 1, 3, 5 or 10 years; monthly 3, 5 or 10 years, or as far back as the source goes (about 13). One request carries about 640 daily bars and this page walks backwards a page at a time, so ten years — around 2,500 bars — is inside it.

## Volume and Turnover

One stock's volume against its turnover rate, as two stacked panels.

- Across trading days, volume and turnover rate are proportional, so the two panels have nearly the same shape. Within one day, per-minute volume and cumulative turnover look genuinely different, which is the more interesting picture.
- The intraday source only keeps the last few trading days, so that mode offers those rather than an arbitrary date.
- Minute data is served for A-shares and Hong Kong only; on the United States that mode is not offered.
- On daily bars the range is 1, 3, 6, 12 or 24 months, or a start and end date of your own; a custom span stops at about 900 calendar days — what one request returns — and the date pickers stop there too. The intraday mode offers a choice among those few trading days.

## Sector Race

![The page in full: preview on the left, scrubber below, settings on the right.](media/sector-race.png)

A set of sectors or stocks, drawn as horizontal bars that overtake one another, the order changing right up to the last frame.

- Two measures: the interval's gain/loss percentage, and its turnover in hundreds of millions of yuan. Switching is just a re-colour of the same data; it does not fetch again.
- Four rosters: SW Level-1 industries, hot themes, custom (tick the boxes), and individual stocks (search to add). The custom roster starts filled with the SW Level-1 set.
- The built-in rosters follow the market: SW Level-1 industries and hot themes for A-shares, the four Hang Seng sub-indices for Hong Kong, ten SPDR sector ETFs for the US. The custom and stock rosters exist on every market.
- The interval can be 1, 3, 6, 12 or 24 months, or a custom start and end date. A custom span reaches about 900 days — one request's worth — and the date pickers stop there.
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
- The range is the last 12 months, 3, 5 or 10 years, or **Longest** — one request returns all 180 monthly periods, about fifteen years, and that is where the longest entry ends. A start and an end date of your own is offered too.
  and a board of mixed currencies means nothing. Hong Kong and New York keep a fixed field, because
  no ranking this app can reach serves them.





## Market Value History

One stock's circulating market value day by day, with its share price beneath it on the same time axis. Or several companies at once — one line each, named at its end.

- **The value is recovered, not quoted.** The source has no historical share count for any day. The count comes from the turnover rate, which is the volume as a fraction of the shares in circulation — so `volume ÷ turnover rate` *is* the circulating count, and the value is the day's price times it.
- **The band down the right-hand side can be given up, if you want the width.** It is off by default: the platform draws its avatar and its like and comment buttons down that side of a vertical video, and a figure underneath them is hidden on the phone even though it is perfectly readable here. Turned on, the panels draw to the frame's own edge and the plot is as wide as the frame.

- **The count is a twenty-day median.** The rate arrives with two decimals, so one day's count carries about a percent of noise, while a share count is a staircase — it moves on a placement or a buyback and is flat between. The median keeps the step on the day it happened and drops the rest.

- **Only the shares traded in this market are counted.** Shares the company lists somewhere else are left out, so a company listed in two places sits below the “total market value” a quote app shows — that figure prices the other market's shares at this market's price too. ICBC's gap is entirely H-shares. Stock still under lock-up in this market is out as well.

- **In Hong Kong the price is a traded average.** That market serves no unadjusted close, so the price is the amount over the volume, and the lower panel is labelled “average trade price” rather than “share price”.

- **New York divides by every share, not by the ones that trade.** Its rate is a fraction of all the shares the company has, insiders' included, so the line there is a total value rather than a circulating one: the count runs above a quote app's circulating figure by exactly the insider stake — nothing at Apple, 4% at NVIDIA, 12% at Tesla. It reaches back to 2009, the same depth the mainland gets.

- **A ten-year curve reads as if it once went to zero, and does not.** The axis has to hold the peak, so an early stretch worth a tenth of it sits within a few pixels of the baseline — 五粮液's 853 亿 against a 13,097 亿 peak is under seven per cent of it. That is why the low and high marks print their own figures: a bare dot down there is read as zero.

- **The figure rides the line.** A label at each line's leading end names the company and gives the value it has reached at that moment, and it moves with the animation — scrub the bar and it goes with the line. With one company both panels carry one, value and price, and the big figure over the panel says the same number; with several the labels are also what tells the lines apart.

- Span: one, two, five or ten years, or two dates of your own.

Compare several companies at once. Tick more than one chip and each gets a line, named at its own leading end. Several companies' share prices do not share a price axis honestly — put 贵州茅台 beside 京东方A and one of them is a flat line along the bottom — so the lower price panel steps aside and the whole frame goes to market value. Up to six; a seventh is refused rather than quietly dropped, because a frame drawn from six of the seven companies somebody ticked answers about a list nobody chose.

The value axis has two readings. Absolute answers which company is worth more; rebased to 100 at each line's own first day answers whose value grew faster, and is the only readable one once one is several times the other. Either way the date axis is the union of their days rather than the overlap: the overlap would cut a ten-year comparison down to the stretch of whichever listed last.



## AH premium

How much more a company's mainland listing costs than its Hong Kong one, for the firms
listed on both sides — month by month, as bars that overtake one another.

- **Premium = A price ÷ (H price × HKD/CNY) − 1.** Nothing here is derived: both legs are prices
  actually paid at the same moment, which is why this is the one page that must fetch
  **unadjusted** prices. A backward-adjusted series inflates recent prices, and two markets
  adjusted separately cannot be compared — ICBC's A share sells at 8.28 on the screen and the
  adjusted series reports 13.34, which turns a +26% premium into +245%.
- **The same gap is written two ways, and the direction is not a detail.** This page gives A
  against H, the form the industry uses: +194% means the mainland share costs nearly three times
  the Hong Kong one. Some quote services state the same number the other way round — 溢价(H/A),
  negative — where 新华制药 reads −66% on the same day. That is the same fact
  (1 ÷ (1 − 0.66) − 1 = 1.94), not another price and not an error.
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

## Extreme days

One instrument, and the days it moved the most — horizontal bars ranked by size. **The rows of
this board are days, not companies**, which no other page here does: a row's value is how far the
instrument moved on that day against the previous trading day's close, and once that day has
happened the value never changes again.

- **The move is the change in the adjusted close.** Adjusted, because an ex-dividend day is not a
  crash: a stock's price drops by the dividend on that morning, and an unadjusted series would put
  that day at the top of a board of the largest falls in history, when nobody holding it lost
  anything.
- **Ranked by size, not by sign.** −7.7% and +8.1% are the same size of move, so they stand next
  to each other; ranking the signed values would file every fall underneath every rise. The bars
  therefore grow both ways: **a rise to the right, in red; a fall to the left, in green**.
- **A day is ranked only once it has happened.** The twenty-four largest moves in the span are the
  candidates and the frame draws the fifteen largest of those; a day does not take part until its
  own date arrives, so the board fills in as the years pass rather than starting full.
- **Any instrument the market quotes, not only the broad indices.** Type a code, a name or
  pinyin into the search box: a single stock and an exchange-traded fund belong on this board as
  much as an index does, and the list underneath is only a shortcut to the usual ones. Changing the
  market swaps that list and leaves behind an instrument from another market; choosing an instrument
  or a span only saves a preference — nothing is fetched until 取数 is pressed.
- **The longest span is about thirty-five years**, which is the source's limit: one request carries
  about 640 daily bars and the walk makes at most twenty. A span with fewer than sixty trading days
  is refused — the largest single day inside a quiet month is not a fact worth a board.
- **The date at the top of the frame is the time axis**, and the bar underneath it is the progress.
  The header line carries the span, the trading-day count and the number of candidate days.

## Currency corridors

One row per pair, and **the row is the corridor itself**: one end is the cheapest the pair has
been in the chosen span, the other the dearest, and the marker is where the rate is now. So this
board is not like the others — elsewhere a bar's length is *how much*, and here the row is full
width in every frame; what moves is the marker, and the corridor around it.

- **The corridor widens.** Its walls are the lowest low and the highest high **so far**, not over
  the whole span. A month that goes further than any month before it pushes one of them outwards,
  and a pair sitting at 100% is at the dearest it has ever been — not at a limit.
- **Every pair is measured against its own range.** 157.92 on USD/JPY and 1.1245 on EUR/USD are not
  two points on one scale; normalising each corridor is what lets six pairs stand on one board. The
  cost is that a narrow corridor and a wide one look alike, which is why the floor and the ceiling
  are printed under every row.
- **Monthly bars, unadjusted.** A currency has no dividend and no split to adjust for, and the page
  takes the same raw path through the source that the A+H page takes.
- **Coverage differs, which is why the two lists are separate**: USD/CNY reaches back to 2005, the
  other five renminbi pairs to 2016; the major crosses all begin in 2005-07 and carry 325 months
  each. Put them on one board and what you are reading is when the source started quoting each pair.
- **The market setting does not apply here**: a currency pair belongs to no stock market, and the
  board is the same whichever one is in force.
- The longest span is about twenty years, which is the source's monthly coverage; a range shorter
  than twelve months is refused — that is a few weeks of movement, not a corridor.

## Index race

One row per index, and the row is **how far that index has come since its own first month in the
range** — not its level. 3,800 on the Shanghai Composite and 5,700 on the S&P 500 are not two points
on one scale, and drawing levels would be a board about where each index happened to start counting.

- **An index that arrives late is not on the board until it arrives.** The S&P reaches back to 1950,
  the Dow only to 2009, and the Hang Seng Tech index starts in 2020. It is absent, not parked at
  0.00% — parked there it would rank above every index that was ever down, and read as a market in
  which nothing happened.
- **Monthly, and adjusted now.** An index pays nothing out, but a stock pays dividends and splits
  its shares: Apple reads +193% across ten years unadjusted and +1183% adjusted, because the
  unadjusted line carries cliffs no holder ever fell off. The indices are untouched by it — asked
  for an adjustment, the source answers an index with the same rows it always did, and all twelve
  came back identical on both calls. What the board does carry is a difference worth stating rather
  than hiding: an index row is a **price** return, because an index is not a holding, while a stock
  row is a **total** one, dividends and splits put back.
- **The market setting does not govern this page**: it reads three markets at once, and switching the
  market does not change it. You can take the mainland's six, Hong Kong's three, New York's three, or
  all twelve.
- The longest span is held down by the source's monthly ceiling of 430 bars, about thirty-five years;
  a range shorter than twelve months is refused — that is a sprint, not a long run.
- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and a mainland share, a Hong Kong one and a New York one can sit on it together
  — this board never asks the market setting. One list, shared by four boards, so a stock added here
  is offered on the asset race, the drawdown board and the hold-odds board too. Fewer than three and
  the fetch is refused.

## Asset classes

One row per asset class, and the row is **what holding it earned** — not its quote. All eight are
funds listed on a mainland exchange, bought with the same money, so they can be compared directly.

- **Dividends are put back in, and share splits too.** A bond and a cash fund pay almost entirely in
  income: the money-market ETF's price went from 100.161 to 100.901 across thirteen years, which
  unadjusted is +0.0% — and would draw the one row here that never fell as the bottom of the board.
  A fund that split its units is starker still: the Nasdaq ETF is +136% unadjusted, while the index
  it tracks rose sixfold over the same decade.
- **Deliberately the opposite of the index race.** An index pays no dividend, so that page is left
  alone; a fund does pay, so this one has to be adjusted. The two paths do not mix.
- **The two overseas rows carry the exchange rate.** The Nasdaq and Hang Seng ETFs are quoted in
  yuan, so the currency's moves are already inside them — which is what a mainland holder actually
  got.
- **Start dates differ.** The earliest row begins in 2012 and the commodity fund only in 2019. A row
  that has not joined yet is absent, not 0.00%.
- **The market setting does not govern this page**: all eight are listed on the mainland. Fewer than
  twelve months is refused.
- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and the three markets can be mixed on it. One list shared by four boards, so a
  stock added here is offered on the other three as well; it is fetched adjusted, exactly like the
  eight funds, so dividends and share splits are in the number. Fewer than three and the fetch is
  refused.

## Bond market

One row per bond index, and the bar is a **price change** — which is not the same thing as what
holding it earned.

- **A coupon is not in the number.** All nine rows are indices, and the source ignores the
  adjustment parameter for an index, so what comes back is the quote. A bond pays most of its
  return as coupon, and a coupon never appears in a quote: a holder earned more than this board
  shows, and by different amounts on different rows.
- **Deliberately the opposite of the asset race.** That board is drawn on the adjusted series
  because a fund pays out; this one is left alone because an index does not. The two boards
  cannot be read against each other.
- **Nine rows, and the roster is built in** rather than a list you keep. A CSI total-bond index
  was wanted and does not exist on this source: the code that looks like it is the Shanghai
  detachable-bond index, whose monthly series stops in August 2015, and a sweep of the entire
  index code space found no total-bond index at all. Those seats went to the deepest credit
  indices the source does answer.
- **Start dates differ.** The earliest row begins in 2003-02 and the Shenzhen convertible index
  only in 2014-08, so on a ten-year board it joins five years in. A row that has not started is
  absent, not 0.00%.
- **Monthly**, one bar per month, and the market setting does not govern this page. Fewer than
  twelve months is refused.
- **Begins on the first whole month in the range.** The source answers only in whole months and a
  monthly bar *is* that whole month, so when a window opens in the middle of one that partial
  month does not count — the board starts on the next whole month after it. That is why "past 10
  years" draws 119 months rather than 120: the missing one lies outside the window. The two dates
  in the header are the dates it really begins and ends on.
- **Three groups**: all nine, the six straight bonds without convertibles, and the three
  convertibles.

## Drawdowns

A row is **how far below its own high a holding sits** — not what it earned, but what it cost to
earn it. The same eight holdings as the asset race, measured against themselves instead of each
other.

- **The curve is the point.** Everywhere else in this app a value is drawn as a length, which can
  only say how deep the water is at this instant. A depth is a shape over time: the low and the
  climb out of it are two places on the curve, and the distance between them across the frame is
  the months it took.
- **The two numbers do not rise together.** Over the last ten years the Nasdaq fund fell 25.52%
  and was level again in six months; the CSI 500 fund fell 56.07% and took eighty-six. Printed as
  one number, the second looks like more of the same thing as the first and is not.
- **One depth scale for the whole board.** Scaling each row to its own worst would draw the
  money-market fund's 0.2% as a chasm the size of the CSI 500's 56%, on a board whose whole claim
  is that those are not comparable. So that row is a flat line pinned to its high-water line — and
  **the flatness is what it says**.
- **Adjusted, monthly, and from each holding's own first month**, for the reasons the asset race
  gives: a fund's distributions never appear in its price, and a holding that joins in 2019 is not
  measured against a high it did not have.
- **The rows still race.** They are ordered by how far below their own high they are, closest to
  its high at the top, and they trade places as their months pass.
- **Gold and the commodity fund were still under water when this was measured** — the board reports
  that kind of fall as open, because the range ended before it was mended.
- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and the three markets can be mixed on it. One list shared by four boards, so a
  stock added here is offered on the other three as well; it is fetched adjusted, exactly like the
  eight funds, so dividends and share splits are in the number. Fewer than three and the fetch is
  refused.

Not governed by the market setting: all eight are quoted on a mainland exchange. Fewer than twelve
months in the range is refused.

## Hold odds

A row is **the share of finished entries that gained** — of all the months a holder could have
bought in and held for the same length of time, the share that ended up ahead. The same eight
holdings as the asset race and the drawdown board, scored on whether holding them worked rather
than on how much they made.

- **One entry is luck; eighty-four of them are a rate.** Every month in the range is an entry and
  each is held for the same length of time, so a three-year hold across ten years is eighty-four
  entries per row, not one. They share months, and that is the point: thinning them out to three
  independent ones would leave a rate with three observations in it.
- **An entry counts from the month it finishes.** Nothing bought in the last three years of the
  range has finished, and counting an unfinished entry as a loss would bend every row downwards at
  the end for no reason but the calendar. So the board opens on the first month an entry could have
  finished on.
- **A row joins on its sixth finished entry.** One entry is 0% or 100%, and either number sitting
  at an end of the ranking is an end it has not earned.
- **Adjusted, monthly, and from each holding's own first month**, for the reasons the asset race
  gives: a fund's distributions never appear in its price, and a fund launched in 2019 has no 2016
  entry to have won or lost.
- **The holding period is this board's one new choice.** One year and five years over the same ten
  years are different questions with different answers, and the eight rows reorder between them.
- **The rows still race.** They are ordered by their rate, most often ahead at the top, and they
  trade places as their months pass.
- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and the three markets can be mixed on it. One list shared by four boards, so a
  stock added here is offered on the other three as well; it is fetched adjusted, exactly like the
  eight funds, so dividends and share splits are in the number. Fewer than three and the fetch is
  refused.

Measured over the last ten years with a three-year hold: the Nasdaq fund was ahead on all
eighty-four of its entries and the Hong Kong fund on forty per cent of them — two rows the asset
race separates by ten years of total return and this board separates by whether walking in worked
at all.

Not governed by the market setting: all eight are quoted on a mainland exchange. Fewer than twelve
months in the range is refused.

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

Buying a fixed amount on a fixed cadence — every trading day, every week or every month — and watching what the discipline turned into. Several plans can share the one frame: a value line each, with its running profit riding the line's leading end.

- The instruments come from your **own list**, the one the other boards share: search a code or a name to add one, each chip's switch decides whether it is on this frame, and the × takes it off the shared list (and off those other boards with it). The one-tap row follows the market — broad and gold ETFs on the A-share market, the Hong Kong tracker funds, SPY, QQQ and GLD in the United States — and a press adds that name and draws it straight away.
- **2 to 6 plans on one frame.** Each puts in the same amount at the same cadence, buying from its own first trading day. Only the value lines are drawn: six fills stacked over each other are mud, and at one amount and one cadence the six invested lines land exactly on top of one another, so the invested line is drawn once — for the plan that put in the most, since drawing the least would flatter the rest. The date axis is the union of their days: a listing that starts later begins later, and is absent before that. Six is the ceiling — past it the fetch refuses rather than quietly drawing some of them — and an instrument from another market is left off. With several, the big figure in the middle becomes the **leader's** return in per cent rather than its money: a later listing has had less paid in, and earning less is not the same as being the worse plan.
- **The figure rides the line.** A label at each plan's leading end names it and gives the money it is up at that moment, and it moves with the animation — scrub the bar and it goes with the line. With one plan the big figure in the middle is still the return in per cent, and the label is there all the same.
- The amount and the cadence are yours to set; the span is three, five or ten years, or as far back as the data goes (about thirteen years).
- Returns are computed on backward-adjusted closes, with no fees. The result describes the price series, not a bill anyone could have executed.
- Besides three, five and ten years and the longest span, the range can be **Custom**: give a start and an end date, then press Fetch. About 35 years is reachable — the source serves roughly 640 calendar days per request, and the walk makes at most twenty of them.
- **Two motions.** *Grow across the span* lays the whole range down at once; *scroll a window* holds a window of a fixed number of trading days and walks it from the start of the range to its end — the only way a long daily series keeps its wobbles readable. The window only counts while scrolling, and both motions read **the same marks**: switching re-fetches nothing. **The vertical axis is not rescaled per window**: the gap between the two lines *is* the result of a plan, and rescaling would widen it along with the window.
- **A scrolling window opens out at the end.** As the closing stretch begins the window widens back towards the first day of the range, so the frame the animation stops on is the whole span rather than the last few dozen days of it.
- **The band down the right-hand side can be given up, if you want the width.** It is off by default: the platform draws its avatar and its like and comment buttons down that side of a vertical video, and a figure underneath them is hidden on the phone even though it is perfectly readable here. Turned on, a frame filling the whole span draws to the frame's own edge from its first frame on; a scrolling window still keeps clear while it is a window, and opens out into the full width along with the window — so the frame the video stops on is the whole span, edge to edge.

## Holdings Return

![The page in full: preview on the left, scrubber below, settings on the right.](media/position.png)

One purchase, held — a million of the same name since 2015 — animated to show what the years did to its value and its return. Several holdings can share the one frame: a line each, with its running profit riding the line's leading end.

- The holdings come from your **own list**, the one the other boards share: search a code or a name to add one, each chip's switch decides whether it is on this frame, and the × takes it off the shared list (and off those other boards with it). The one-tap row follows the market — 中国平安 and 贵州茅台 for the mainland, 腾讯, 汇丰 and 盈富基金 for Hong Kong, Apple, Berkshire and SPY for New York — and a press adds that name and draws it straight away.
- **2 to 6 of your holdings on one frame.** Each is bought once with the same amount, on its own first trading day, so the lines are directly comparable and the distance between two of them at any date is the answer to "which was the better place for it". The date axis is the union of their days: a listing that starts later simply begins later, and is absent before that rather than drawn flat along the capital. Six is the ceiling — past it the fetch refuses rather than quietly drawing some of them — and a holding from another market is left off, because the amounts here are the currency of the market in force.
- **The figure rides the line.** A label at each holding's leading end names it and gives the money it is up at that moment, and it moves with the animation — scrub the bar and it goes with the line. With one holding the big figure in the middle is still the return in per cent; with several it becomes the money the **leader** is up, with that holding's name underneath, and the closing cards become one per holding rather than the four figures describing one.
- The initial capital and the holding span are yours to set; the span is three, five or ten years, or as far back as the data goes (about thirteen years).
- Returns are computed on backward-adjusted closes — dividends reinvested, no fees. The backward adjustment anchors at the listing and accumulates dividends forward, so a heavy payer's early years never turn negative the way the forward-adjusted series can.
- The same **Custom** span works for the holding: give two dates, then press Fetch. If the instrument listed later than the date you asked for, the holding starts on its first trading day.
- **Two motions.** *Grow across the span* lays the whole range down at once, so the curve's shape on screen is its shape in time. *Scroll a window* holds a window of a fixed number of trading days and walks it from the start of the range to its end — the only way a long daily series keeps its wobbles readable, since spread over twelve years a three-month fall is two pixels. The window only counts while scrolling, and both motions read **the same marks**: switching re-fetches nothing.
- **A scrolling window opens out at the end.** As the closing stretch begins the window widens back towards the first day of the range, so the frame the animation stops on is the whole span rather than the last few dozen days of it.
- **The band down the right-hand side can be given up, if you want the width.** It is off by default: the platform draws its avatar and its like and comment buttons down that side of a vertical video, and a figure underneath them is hidden on the phone even though it is perfectly readable here. Turned on, a frame filling the whole span draws to the frame's own edge from its first frame on; a scrolling window still keeps clear while it is a window, and opens out into the full width along with the window — so the frame the video stops on is the whole span, edge to edge.

## Video

The frame is always 9:16. Everything else is yours to set.

- Duration changes the pacing rather than trimming the animation: the opening, the growth of the bars and the closing statistics are re-apportioned across whatever length you choose.
- Margins are written against a 1080×1920 frame and scaled to the resolution you export at, so a layout tuned once holds at every size. The left margin also decides where the axis labels land — set it too small and the numbers leave the frame.
- The safe-area guides outline what a phone app covers with its own interface. They are drawn in the preview and never in a file.
- The title can be more than one line: press Enter in the title box to break it where you want. A title too wide for one line wraps onto a second, two lines at most; only when two still will not hold it does the size give way. A second line pushes everything below it down by one row, so the chart is that much shorter.
- **The name and the figure at a line's end stop short of the platform's own interface.** A phone app draws its avatar and its like and comment buttons down the right-hand side of a vertical video, so the plotting area ends before the frame's right edge and the live point of a curve — with the name and the figure riding it — comes to rest to the left of that band. The chart is narrower than the frame, and that is why.

- Everything up to the last step is free: fetching data, playing the animation, saving a cover image. **Export** is the one place that asks for a monthly subscription, and pressing it says what that buys and what it costs. It renews until you cancel it in Microsoft Store.

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

- **Every frame also carries a name across its backdrop: the watermark.** It is on by default, reads “周期留白” until you change it, and the wording is yours to edit. It is repeated on a slant over the whole frame, drawn **under** the data, so it covers nothing; the preview, the exported video and the cover image all carry it. Left blank it falls back to the default name — to carry nothing at all, switch it off. The switch is on by default because a video is posted somewhere that shows nothing of where it was made.

- Taking the mark off is one of the two things a subscription buys. Until one exists the switch stays on and cannot be moved — which is also exactly what every frame will carry, so the preview and the file never disagree.


- **How the mark looks is yours too.** The font is any font installed on this machine — each entry in the list is drawn in the font it names —, the colour is whatever the picker gives, and the strength is how much of that colour is used: 10% by default, up to 40%, and even at its strongest it is drawn under the data. All three reach the preview, the exported video and the cover image alike.

- **Until there is a subscription, that slider stays at 40%.** Turning the mark down goes with taking it off: an unsubscribed app writes every frame at full strength and the slider cannot be moved off it. The 10% above is where it starts once there is one.
- The default wording does not follow the interface language: a watermark is a signature, and a signature that changed with the language would be a different one on every machine.

## Data, and what it will not tell you

Quotes come from Tencent Finance's public endpoints, and the frame always says so. These videos describe what has already traded. They are for reference only and are not investment advice.

- Turnover is converted to hundreds of millions of yuan, and volume switches to a larger unit once the numbers warrant it, so the axis stays readable.
- Turnover is converted to hundreds of millions — of yuan on the mainland and in Hong Kong, of dollars in the United States. Each market keeps its own currency.
- A range longer than one request can return is refused rather than quietly truncated: about 900 calendar days of daily bars, about fifteen years on the candle page, which pages backwards, and a full history of monthly bars. Truncating quietly is the worst outcome — what goes missing is the **beginning**, and a chart missing its first years is a shorter chart that looks entirely correct.

## Updating

When the Microsoft Store has a newer version, an **Update** button appears beside Settings in the navigation pane; one click installs it.

- It only appears when the Store really has a newer version. A development or sideloaded build never sees it, and that is expected.
- The app closes while the update installs and starts again on the new version, and the button is gone. If an export is running, it asks first.
- If it cannot install, it says why — Wi-Fi only, battery too low — and the update can also be installed from the Microsoft Store.

## Something wrong?

Write to gaqo@outlook.com and say what you were doing and what you expected instead. The version number is on the Settings page.
