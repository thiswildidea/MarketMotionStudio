using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One coin's daily bars, shaped into the series the gain-loss calendar draws.
///
/// The same shape the stock calendar builds (<see cref="InstrumentCalendar"/>), because
/// the renderer is metric-driven and knows nothing about what it is colouring: give it
/// a day and a change and it draws a cell. That is the whole of the difference between
/// this and the stock page — same grid, same ramp, a different walk behind it.
///
/// **What the coin market does to a calendar.** Every day is a trading day. A stock
/// calendar is mostly holes — weekends, holidays, suspensions — and reads the way a
/// market looks: five cells a week with gaps where the year stopped. A coin's fills
/// every square, which makes the picture denser rather than longer and is the one thing
/// worth saying about this page in the manual: a full grid is not missing data here, it
/// is the market never closing.
/// </summary>
public static class CryptoCalendar
{
    /// <summary>
    /// The smallest series worth a calendar. Matches the stock page's floor: fewer than
    /// three days is a grid with nothing to say.
    /// </summary>
    private const int FewestDays = 3;

    public static async Task<TurnoverSeries> LoadAsync(
        CryptoQuotes quotes,
        CryptoAsset asset,
        DateOnly start,
        DateOnly end,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (start >= end)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        // No ceiling here, unlike the stock page's 640-day guard: the caller clips the
        // range to what the source carries before it asks, which is what the other three
        // crypto pages do, and a second ceiling here would be one more place to keep in
        // step with that.
        progress?.Report(Strings.Format("GainCalendarFetching", asset.Display));

        var bars = await quotes.BarsAsync(asset, start, end, progress, cancellation);

        if (bars.Count < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverTooFewDays"));
        }

        // Day zero is 0%, as on the stock page: there is no prior close inside the range,
        // and reaching outside it for one would make the first cell depend on a day the
        // calendar does not show.
        var returns = bars
            .Select((bar, i) => i == 0 || bars[i - 1].Close <= 0
                ? 0
                : ((bar.Close / bars[i - 1].Close) - 1) * 100)
            .ToList();

        // The traded amount fills the Totals column the record asks for. The return
        // calendar never draws it — the animation plan's axis maths wants a non-zero
        // peak and this is the figure the record was built around. A coin's volume is a
        // count of coins, so the amount is the count times the day's price.
        //
        // The fallback is for the fallback source, which serves a price and no volume at
        // all. A constant rather than a zero: an axis scaled against zero is an axis that
        // has nothing to be scaled against, and no column on this page shows the figure.
        var totals = bars.Select(b => b.Volume > 0 ? b.Volume * b.Close : 1.0).ToList();

        if (totals.All(t => t <= 0))
        {
            totals = [.. Enumerable.Repeat(1.0, bars.Count)];
        }

        return new TurnoverSeries(
            [.. bars.Select(b => b.Date)],
            totals,
            returns,
            [asset.Display],
            asset.Display);
    }
}
