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
/// The walk asks for <c>hfq</c>, the backward-adjusted series, and that choice is
/// not cosmetic. The forward-adjusted one rebases itself to *today*: every past
/// dividend and split pushes earlier prices further down, and for a heavy payer
/// like 中国平安 the rebase goes through zero — years of closes arrive negative,
/// which a ratio-based chart survives but anything that buys at a price does not.
/// The backward-adjusted series anchors itself at the listing instead, so every
/// close is positive and the ratio between any two days is the holding's real
/// total return, dividends reinvested. Hong Kong and US rows come back unadjusted
/// whatever is asked, which for those venues is the same question anyway.
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
