# AShare Motion Studio

This app turns A-share market indicators into vertical videos for phones. You pick a period, look at the preview until it reads well, and export an MP4. Nothing else has to be installed.

## Market Turnover

The whole market's daily turnover: the Shanghai and Shenzhen composite amounts added together, one bar per trading day.

- Only days on which every included market traded are kept, so a single market's holiday cannot make the total appear to collapse.
- A session still in progress is left out. An unfinished day holds only its opening auction, which would draw as a bar flat against the axis.
- The Beijing option adds the BSE 50 index, which covers its constituents and not the whole exchange. It is a different measure, and a smaller one.

## Stock Volume

One stock's volume against its turnover rate, as two stacked panels.

- Across trading days, volume and turnover rate are proportional, so the two panels have nearly the same shape. Within one day, per-minute volume and cumulative turnover look genuinely different, which is the more interesting picture.
- The intraday source only keeps the last few trading days, so that mode offers those rather than an arbitrary date.

## Video

The frame is always 9:16. Everything else is yours to set.

- Duration changes the pacing rather than trimming the animation: the opening, the growth of the bars and the closing statistics are re-apportioned across whatever length you choose.
- Margins are written against a 1080×1920 frame and scaled to the resolution you export at, so a layout tuned once holds at every size. The left margin also decides where the axis labels land — set it too small and the numbers leave the frame.
- The safe-area guides outline what a phone app covers with its own interface. They are drawn in the preview and never in a file.

## Where videos go

Exports are written to a folder you choose through a picker. Until one is chosen the first export asks, then remembers; Settings can change it or forget it.

## Data, and what it will not tell you

Quotes come from Tencent Finance's public endpoints, and the frame always says so. These videos describe what has already traded. They are for reference only and are not investment advice.

- Turnover is converted to hundreds of millions of yuan, and volume switches to a larger unit once the numbers warrant it, so the axis stays readable.
- A range longer than about 640 calendar days is refused rather than quietly truncated, because that is as much as one request to the source returns.

## Something wrong?

Write to gaqo@outlook.com and say what you were doing and what you expected instead. The version number is on the Settings page.
