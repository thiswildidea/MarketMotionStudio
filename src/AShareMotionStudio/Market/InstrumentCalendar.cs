using AShareMotionStudio.Localization;

namespace AShareMotionStudio.Market;

/// <summary>
/// One fetch of a single instrument's daily bars, shaped into the series the gain-loss calendar
/// draws.
///
/// The calendar renderer is metric-driven and takes a <see cref="TurnoverSeries"/>, so "any stock
/// or index" needs no renderer of its own — only this loader, which turns one instrument's bars
/// into the same record the whole-market page builds from three indices'. That is the whole
/// difference between the two pages: same grid, same colour ramp, different series behind it.
/// </summary>
public static class InstrumentCalendar
{
    /// <summary>
    /// The smallest series worth a calendar. Matches the whole-market page's floor: fewer than
    /// three trading days is a grid with nothing to say and nearly always a range that landed on
    /// a holiday week.
    /// </summary>
    private const int FewestDays = 3;

    public static async Task<InstrumentCalendarSeries> LoadAsync(
        TencentKline kline,
        MarketProfile market,
        string code,
        string display,
        DateOnly start,
        DateOnly end,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        // Localized here rather than left to the stock-bars method's English guards, for the same
        // reason the whole-market loader does it: the one rejection the page cannot rule out by
        // construction is the custom range's two pickers, which can be set either way round.
        if (start >= end)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        if (end.DayNumber - start.DayNumber > TencentKline.MostBarsPerRequest)
        {
            throw new InvalidOperationException(Strings.Format("TurnoverRangeTooLong", TencentKline.MostBarsPerRequest));
        }

        // The bars endpoint is asked only for codes of the market in force. The page's
        // search filters to them and its presets are drawn from them, but a typed
        // submission and a favourite saved under another market both reach here, and
        // the refusal belongs in the reader's language.
        if (!market.Accepts(code))
        {
            throw new InvalidOperationException(Strings.Format("WrongMarket", market.Name));
        }

        progress?.Report(Strings.Format("GainCalendarFetching", display));

        // StockBarsAsync, not DailyBarsAsync: the same rows for an index as for a stock, plus the
        // instrument's display name riding along in the envelope — one round trip instead of two.
        var bars = await kline.StockBarsAsync(code, start, end, cancellation);

        if (bars.Count < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverTooFewDays"));
        }

        var name = kline.LastName(code);

        // Day zero is 0%, as on the whole-market page: there is no prior close inside the range,
        // and reaching outside it for one would make the first cell depend on a day the calendar
        // does not show.
        var returns = bars
            .Select((bar, i) => i == 0 || bars[i - 1].Close <= 0 ? 0 : ((bar.Close / bars[i - 1].Close) - 1) * 100)
            .ToList();

        // Turnover in 亿 of the venue's currency fills the Totals column the record asks
        // for. The return calendar never draws it, but the animation plan's axis maths
        // wants a non-zero peak and the figure is already here — inventing a dummy would
        // be worse than carrying the real one. The divisor is the market's, because a US
        // bar's amount is dollars rather than 万元.
        var totals = bars.Select(b => b.AmountWan / market.AmountToYi).ToList();

        var series = new TurnoverSeries(
            [.. bars.Select(b => b.Date)],
            totals,
            returns,
            [name],
            name);

        return new InstrumentCalendarSeries(series, code, name);
    }

}

/// <param name="Series">The calendar-shaped series, with the instrument's name as its return source.</param>
/// <param name="Code">The instrument's code, for the favourites row.</param>
/// <param name="Name">The instrument's display name as the quote source spells it.</param>
public sealed record InstrumentCalendarSeries(TurnoverSeries Series, string Code, string Name);
