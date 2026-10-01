namespace MarketMotionStudio.Market;

/// <summary>
/// Walks the kline endpoint backwards, one request at a time, to gather years of
/// daily closes for one instrument.
///
/// The pages that need years — the plan page and the position page — share this
/// walk because it is the same negotiation with the source whichever question is
/// being asked of the history: one request carries only
/// <see cref="TencentKline.MostBarsPerRequest"/> bars (about two and a half
/// years), and the endpoint ignores the start date in its param, so the only way
/// further back is to ask again for the window ending the day before the earliest
/// bar the last request returned. It stops when a request brings nothing earlier
/// than what is already held — which is both "the range is covered" and "this
/// instrument's history starts here", two states the source does not distinguish.
///
/// Because the source clips what it returns to the window it was asked for, the
/// last step of a walk backwards from <c>end</c> asks for the stretch between the
/// range's own start and the earliest bar held — a stretch that can hold no bars
/// at all, since a start date landing on a weekend or inside a holiday week has no
/// trading days after it before the first bar. That reply arrives as an empty list,
/// and the stop condition below is what reads it as "the range is covered"; see
/// <see cref="TencentKline.StockBarsAsync"/>, which must answer it rather than
/// refuse it.
///
/// The walk asks for <c>hfq</c>, the backward-adjusted series, and that choice is
/// not cosmetic. The forward-adjusted one rebases itself to *today*: every past
/// dividend and split pushes earlier prices further down, and for a heavy payer
/// like 中国平安 the rebase goes through zero — years of closes arrive negative,
/// which a ratio-based chart survives but anything that buys at a price does not.
/// The backward-adjusted series anchors itself at the listing instead, so every
/// close is positive and the ratio between any two days is the holding's real
/// total return, dividends reinvested.
///
/// What <c>hfq</c> asks for here is that total return, not literally a block with
/// that name: <see cref="TencentKline"/> sends it to whichever endpoint carries the
/// venue's adjusted rows, which for the United States is the forward-adjusted
/// series, since no backward-adjusted one exists there. The two answer the same
/// question up to one constant factor over the whole series, and that factor
/// cancels in everything these two pages derive — a buy is <c>amount / price</c>
/// and a marking is <c>shares × price</c>.
/// </summary>
internal static class HistoryWalk
{
    /// <summary>
    /// Requests beyond this are not made. Twenty pages is about twelve years of
    /// trading days, which is past where the source's adjusted history thins out
    /// anyway — the walk stops on its own when a page returns nothing earlier, and
    /// this is the backstop that keeps a pathological response from looping.
    /// </summary>
    private const int MostRequests = 20;

    /// <summary>
    /// The furthest back one walk can reach, in calendar days.
    ///
    /// One request carries <see cref="TencentKline.MostBarsPerRequest"/> days at most,
    /// and the walk makes <see cref="MostRequests"/> of them. A page offering two dates
    /// to type in bounds its pickers by this rather than by a number picked for how it
    /// sounds: past it the walk runs out of requests before it runs out of range, and
    /// the series quietly starts later than the date that was asked for — which is the
    /// one answer a custom span must not give, because the whole point of typing two
    /// dates is that they are the dates.
    /// </summary>
    public const int MostDays = MostRequests * TencentKline.MostBarsPerRequest;

    /// <summary>
    /// The closes from <paramref name="start"/> to <paramref name="end"/>, or as
    /// many as the source has, keyed by trading day. Duplicates are collapsed by
    /// date, so overlapping requests cost nothing.
    /// </summary>
    public static async Task<SortedList<DateOnly, double>> ClosesAsync(
        TencentKline kline,
        string code,
        string display,
        DateOnly start,
        DateOnly end,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var closes = new SortedList<DateOnly, double>();

        var cursor = end;
        var earliestSeen = end;

        for (var request = 0; request < MostRequests; request++)
        {
            progress.Report($"{display}: {closes.Count} …");

            // The walk stops when the earliest bar held is at or before the range's
            // own start, so the cursor never precedes it — but a start landing one
            // day before the first bar leaves a window of exactly one day, and that
            // is a window like any other: it holds that day or it holds nothing.
            if (cursor < start)
            {
                break;
            }

            var bars = await kline.StockBarsAsync(code, start, cursor, cancellation, adjustment: "hfq");

            if (bars.Count == 0)
            {
                break;
            }

            foreach (var bar in bars)
            {
                // A defence, not a fix: the backward-adjusted series does not go
                // negative, but a source that once did could again, and a buy at a
                // non-positive price is not a holding, it is a gift.
                if (bar.Close > 0)
                {
                    closes.TryAdd(bar.Date, bar.Close);
                }
            }

            var earliest = bars[0].Date;

            // The page ends where the last one began, so nothing earlier arrived:
            // either the range is covered or the source has no more. Either way, done.
            if (earliest >= earliestSeen || earliest <= start)
            {
                break;
            }

            earliestSeen = earliest;
            cursor = earliest.AddDays(-1);
        }

        return closes;
    }
}
