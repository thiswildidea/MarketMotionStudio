using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One fetch, carrying **two measures** of the same trading days.
///
/// <list type="bullet">
/// <item><description><see cref="Totals"/> — whole-market turnover in 亿元, the venues added
/// together.</description></item>
/// <item><description><see cref="Returns"/> — the Shanghai composite's daily change in per
/// cent.</description></item>
/// </list>
///
/// Two measures rather than two fetches because they come out of the same bars, and one switch in
/// the interface moves between them without going back to the network.
///
/// **They are not summed the same way, and that asymmetry is the point.** Turnover is a quantity,
/// so adding Shanghai to Shenzhen gives a whole-market figure. A percentage change is a ratio, and
/// adding two of them means nothing — so the return series is the *first* venue's alone, which is
/// why the frame says "上证指数" rather than naming the combination.
/// </summary>
/// <param name="Dates">Trading days, ascending.</param>
/// <param name="Totals">Combined turnover for each day, same length and order.</param>
/// <param name="Returns">
/// Daily percentage change of the first venue's close. The first entry is zero: there is no prior
/// close inside the range to compare against, and reaching outside it for one would make the first
/// bar depend on a day the chart does not show.
/// </param>
/// <param name="Markets">Display names of the markets summed, for the frame's subtitle.</param>
/// <param name="ReturnSource">
/// The name of whatever <see cref="Returns"/> was computed from. The whole-market page's returns
/// come from one venue's composite index; the gain-loss calendar page's come from the chosen
/// instrument. The return metric's subtitle names it, so an arbitrary instrument needs to hand
/// its name through here — empty means the whole-market default.
/// </param>
public sealed record TurnoverSeries(
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<double> Totals,
    IReadOnlyList<double> Returns,
    IReadOnlyList<string> Markets,
    string ReturnSource = "")
{
    public int Count => Dates.Count;

    public double Peak { get; } = Totals.Count > 0 ? Totals.Max() : 0;

    public double Low { get; } = Totals.Count > 0 ? Totals.Min() : 0;

    public double Average { get; } = Totals.Count > 0 ? Totals.Average() : 0;

    public int PeakIndex { get; } = IndexOf(Totals, Totals.Count > 0 ? Totals.Max() : 0);

    public int LowIndex { get; } = IndexOf(Totals, Totals.Count > 0 ? Totals.Min() : 0);

    /// <summary>The best day's change, in per cent. Negative if every day fell.</summary>
    public double ReturnMax { get; } = Returns.Count > 0 ? Returns.Max() : 0;

    /// <summary>The worst day's change, in per cent.</summary>
    public double ReturnMin { get; } = Returns.Count > 0 ? Returns.Min() : 0;

    /// <summary>
    /// The largest move in either direction, which is what the colour ramp is scaled against.
    ///
    /// Symmetric on purpose: scaling gains and falls independently would make a 1% rise and a 1%
    /// drop the same depth of colour in a period that happened to have a crash in it, so the
    /// picture would misstate which days were the dramatic ones.
    /// </summary>
    public double ReturnAbsMax { get; } = Returns.Count > 0
        ? Math.Max(Math.Abs(Returns.Max()), Math.Abs(Returns.Min()))
        : 0;

    public int ReturnMaxIndex { get; } = IndexOf(Returns, Returns.Count > 0 ? Returns.Max() : 0);

    public int ReturnMinIndex { get; } = IndexOf(Returns, Returns.Count > 0 ? Returns.Min() : 0);

    /// <summary>
    /// Days that rose. Strictly greater than zero, so an unchanged close counts as neither up nor
    /// down — and the two counts therefore need not add up to the number of days, which is honest
    /// rather than tidy.
    /// </summary>
    public int UpDays { get; } = Returns.Count(v => v > 0);

    public int DownDays { get; } = Returns.Count(v => v < 0);

    private static int IndexOf(IReadOnlyList<double> values, double wanted)
    {
        for (var i = 0; i < values.Count; i++)
        {
            // Comparing the value back to one taken from the same list, so this is an identity
            // test rather than a tolerance question.
            if (values[i] == wanted)
            {
                return i;
            }
        }

        return 0;
    }
}

/// <summary>Which slice of the market a series covers.</summary>
public enum MarketScope
{
    /// <summary>Shanghai plus Shenzhen — the figure the financial press means by 两市.</summary>
    Whole,

    /// <summary>Everything listed on the Shanghai exchange, STAR board included.</summary>
    Shanghai,

    /// <summary>Everything listed on the Shenzhen exchange, ChiNext included.</summary>
    Shenzhen,

    /// <summary>The Shanghai main board: the exchange total less its STAR board.</summary>
    ShanghaiMain,

    /// <summary>The STAR board. The composite, not the STAR 50 constituents.</summary>
    Star,

    /// <summary>The Shenzhen main board: the exchange total less its ChiNext board.</summary>
    ShenzhenMain,

    /// <summary>The ChiNext board. The composite, not the ChiNext index's 100 constituents.</summary>
    ChiNext,

    /// <summary>Both exchanges plus the BSE 50 — the widest figure the source can offer.</summary>
    WithBeijing,

    /// <summary>
    /// One person's own basket — indices and stocks side by side. Not a board, so none of the
    /// recipes above apply: there is nothing to add up to and nothing to subtract, only the rows
    /// the reader put there.
    /// </summary>
    Watchlist,
}

/// <summary>
/// Sums a basket of the reader's own instruments into the same series a board produces.
///
/// **A missing day is a zero, not a dropped day.** Every board above is built from indices, and
/// an index trades on every session, so the rule "keep only the days every code has" never bit —
/// it was a cheap way of being safe. A stock halts. Under that rule one halted name out of
/// sixteen would remove the day from the chart entirely, and a day missing from this chart looks
/// exactly like a day on which nothing traded: the picture stays plausible and the number in the
/// header stops matching the number of bars. Halted means no turnover, which is a zero, so the
/// day stays and that instrument contributes nothing to it.
///
/// **The return is the equal-weighted average of the members' own daily changes**, and each
/// member's change is measured against *its own* previous close rather than the previous row of
/// the combined axis — a halted name has no change to contribute and counts as zero.
///
/// <para>
/// Equal-weighted because the basket is a list, not a portfolio: there is no holding size to
/// weight by, and weighting by turnover would quietly redefine it as "the average yuan traded",
/// which is a different question. The daily closes come from the same forward-adjusted series the
/// amounts do, which costs nothing extra — the backward-adjusted series differs from it by one
/// constant factor, and a factor cancels in every ratio drawn here.
/// </para>
/// </summary>
public static class BasketTurnover
{
    /// <summary>The same floor the boards use: three days is the least that shows a trend.</summary>
    private const int FewestDays = 3;

    public static async Task<TurnoverSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<(string Code, string Name)> basket,
        DateOnly start,
        DateOnly end,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (basket.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverBasketEmpty"));
        }

        if (end.DayNumber - start.DayNumber > TencentKline.MostBarsPerRequest)
        {
            throw new InvalidOperationException(
                Strings.Format("TurnoverRangeTooLong", TencentKline.MostBarsPerRequest));
        }

        if (start >= end)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        var fetched = new List<(string Code, Dictionary<DateOnly, DailyBar> Bars)>();

        foreach (var (code, _) in basket)
        {
            progress?.Report(Strings.Format("TurnoverFetching", code.ToUpperInvariant()));

            fetched.Add((code, await kline.DailyBarsAsync(code, start, end, cancellation)));
        }

        // The union, not the intersection — see the class note. A day is on the axis if *any*
        // member traded on it, which is what "the basket's trading days" means.
        var dates = fetched
            .SelectMany(f => f.Bars.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToList();

        if (dates.Count < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverTooFewDays"));
        }

        var lastClose = new Dictionary<string, double>();
        var previous = new Dictionary<string, DateOnly>();
        var totals = new List<double>(dates.Count);
        var returns = new List<double>(dates.Count);

        foreach (var day in dates)
        {
            var total = 0.0;
            var change = 0.0;

            foreach (var (code, bars) in fetched)
            {
                if (!bars.TryGetValue(day, out var bar))
                {
                    // Halted, or not yet listed: no turnover, and no change to average in.
                    continue;
                }

                total += bar.TurnoverYi;

                if (lastClose.TryGetValue(code, out var prior) && prior > 0)
                {
                    change += ((bar.Close / prior) - 1) * 100;
                }

                lastClose[code] = bar.Close;
                previous[code] = day;
            }

            totals.Add(total);
            returns.Add(change / fetched.Count);
        }

        _ = previous;

        return new TurnoverSeries(
            dates, totals, returns,
            [Strings.Format("TurnoverBasketLabel", basket.Count)]);
    }
}

/// <summary>
/// Builds a market series for whichever slice of the market was asked for.
///
/// Every board is measured by a **composite** index, never a constituent one. On this source
/// the two disagree in exactly the way that matters here: the Shenzhen component index and the
/// Shenzhen composite carry the *same* amount (the whole exchange's), while the STAR 50
/// carries only its fifty constituents' — a third of the board. Composites throughout is the
/// one rule that keeps every number on the page the same kind of number.
///
/// The two main boards have no composite of their own, so they are **derived**: the exchange's
/// total less its growth board, per day. Both sides of that subtraction come from the same
/// source and the same口径, so the difference is exact rather than approximate — at the price
/// of fetching two indices and discarding half of each.
///
/// `bj899050` is the **BSE 50 index**, which covers fifty constituents rather than the whole
/// Beijing exchange, so including it produces a different measure and a smaller one than a true
/// whole-market figure. That is why it is a choice and why the page says so next to it rather
/// than in a manual.
/// </summary>
public static class MarketTurnover
{
    /// <summary>
    /// One board's recipe. Amounts are summed over <see cref="Adds"/> then, per day, over
    /// <see cref="Subtracts"/>; the return series comes from <see cref="ReturnCode"/> alone,
    /// because a percentage change cannot be summed or subtracted — it belongs to one index, and
    /// the market the board lives in is the honest one to name.
    /// </summary>
    private sealed record Board(
        string LabelKey, string[] Adds, string[] Subtracts, string ReturnCode);

    private static readonly Board[] Boards =
    [
        new("TurnoverScopeWhole", ["sh000001", "sz399106"], [], "sh000001"),
        new("TurnoverScopeShanghai", ["sh000001"], [], "sh000001"),
        new("TurnoverScopeShenzhen", ["sz399106"], [], "sz399106"),
        new("TurnoverScopeShanghaiMain", ["sh000001"], ["sh000680"], "sh000001"),
        new("TurnoverScopeStar", ["sh000680"], [], "sh000680"),
        new("TurnoverScopeShenzhenMain", ["sz399106"], ["sz399102"], "sz399106"),
        new("TurnoverScopeChiNext", ["sz399102"], [], "sz399102"),
        new("TurnoverScopeWithBeijing", ["sh000001", "sz399106", "bj899050"], [], "sh000001"),
    ];

    /// <summary>
    /// The smallest series worth animating. Fewer than three days is a chart with nothing to show a
    /// trend with, and it is nearly always a sign the range landed on a holiday week rather than
    /// that the market was quiet.
    /// </summary>
    private const int FewestDays = 3;

    /// <summary>
    /// The codes a board is made of, as the recipe that produces it: what is added and what is
    /// taken away.
    ///
    /// Offered rather than duplicated because the intraday board needs the same answer about the
    /// same slice, and a second copy of the table above would be a second place for "the Shanghai
    /// main board" to mean two different things. The derived boards are the reason this returns a
    /// subtraction rather than a flat list: the main board is the exchange less its growth board on
    /// *every* time axis this app draws, and a minute-by-minute chart that forgot that would show
    /// the whole exchange while its title said the main board.
    /// </summary>
    public static (string[] Adds, string[] Subtracts) Codes(MarketScope scope)
    {
        var board = Boards[(int)scope];

        return (board.Adds, board.Subtracts);
    }

    public static async Task<TurnoverSeries> LoadAsync(
        TencentKline kline,
        MarketScope scope,
        DateOnly start,
        DateOnly end,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (end.DayNumber - start.DayNumber > TencentKline.MostBarsPerRequest)
        {
            // Refused rather than quietly shortened. The source returns at most one request's
            // worth, so a longer range would come back trimmed at the far end with nothing saying
            // so — a chart that claims a range it does not cover.
            throw new InvalidOperationException(Strings.Format("TurnoverRangeTooLong", TencentKline.MostBarsPerRequest));
        }

        // Checked here as well as in the client, because here it can be said in the reader's
        // language. Left to the client it arrives as an English `ArgumentException` inside an
        // otherwise translated status line. It is also the one rejection the page cannot rule
        // out by construction: the month ranges count backwards from today, but the custom
        // range is two pickers that can be set either way round.
        if (start >= end)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        var board = Boards[(int)scope];
        var label = Strings.Get(board.LabelKey);

        // One fetch per distinct code, each exactly once — a derived board needs both sides of its
        // subtraction, and the return index rides along free inside one of the fetches.
        var codes = board.Adds.Concat(board.Subtracts).Distinct().ToArray();
        var fetched = new List<(string Code, Dictionary<DateOnly, DailyBar> Bars)>();

        foreach (var code in codes)
        {
            progress?.Report(Strings.Format("TurnoverFetching", label));

            // Sequential rather than parallel. A handful of requests is not worth the concurrency,
            // and one at a time keeps the progress message honest about what is being waited on.
            fetched.Add((code, await kline.DailyBarsAsync(code, start, end, cancellation)));
        }

        // Only days every fetched index has. A single index's missing day would otherwise make
        // the day's total half of what it should be — or, on a derived board, a negative number —
        // and the chart would show a crash that never happened. The one failure here that looks
        // like data rather than a bug.
        var dates = fetched[0].Bars.Keys
            .Where(d => fetched.All(f => f.Bars.ContainsKey(d)))
            .OrderBy(d => d)
            .ToList();

        if (dates.Count < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverTooFewDays"));
        }

        var bars = fetched.ToDictionary(f => f.Code, f => f.Bars);

        double AmountOn(string code, DateOnly day) => bars[code][day].TurnoverYi;

        var totals = dates
            .Select(d => board.Adds.Sum(c => AmountOn(c, d)) - board.Subtracts.Sum(c => AmountOn(c, d)))
            .ToList();

        // The return belongs to one index — see the note on Board. Day zero is 0% because the day
        // before it is outside the range.
        var returnCode = board.ReturnCode;
        var closes = dates.Select(d => bars[returnCode][d].Close).ToList();

        var returns = closes
            .Select((close, i) => i == 0 || closes[i - 1] <= 0 ? 0 : ((close / closes[i - 1]) - 1) * 100)
            .ToList();

        return new TurnoverSeries(dates, totals, returns, [label]);
    }
}
