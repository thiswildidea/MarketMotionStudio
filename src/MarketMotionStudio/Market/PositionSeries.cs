namespace MarketMotionStudio.Market;

/// <summary>
/// One day of a holding, as the chart draws it. The capital is the same number on
/// every row — that is the point of the page — but it is carried per row so the
/// renderer treats both lines the same way and one record is one frame of the story.
/// </summary>
/// <param name="Date">The trading day.</param>
/// <param name="Capital">What was paid in at the start, in the venue's currency.</param>
/// <param name="Value">What the shares bought with it are worth at that day's close.</param>
public sealed record PositionPoint(DateOnly Date, double Capital, double Value);

/// <summary>
/// One holding run to the end of its data: the daily marks, and the closing figures
/// the statistic cards read out.
/// </summary>
/// <param name="MaxDrawdownPct">
/// The deepest fall from a running peak, as a positive percentage — the figure a
/// holder is asked to stomach, and the one a return percentage alone hides.
/// </param>
public sealed record PositionSeries(
    string Code,
    string Name,
    IReadOnlyList<PositionPoint> Points,
    double Capital,
    double BuyPrice,
    double MaxDrawdownPct)
{
    public DateOnly Start => Points[0].Date;

    public DateOnly End => Points[^1].Date;

    public double FinalValue => Points[^1].Value;

    public double Profit => FinalValue - Capital;

    /// <summary>The headline percentage: what the holding returned over what was paid in.</summary>
    public double ReturnPercent => Capital > 0 ? (FinalValue / Capital - 1) * 100 : 0;

    /// <summary>The tallest figure either line reaches, for the axis.</summary>
    public double Peak => Math.Max(Points.Max(p => p.Value), Capital);
}

/// <summary>
/// Builds a holding from one instrument's daily closes: a single purchase at the
/// first close of the range, then nothing but the mark-to-market.
///
/// This is the other half of the plan page's question. A plan buys on a schedule
/// and its interest is what the discipline averaged into; a holding buys once and
/// its interest is what the *price* did — which is why the capital line is flat
/// and the drawdown is a headline figure here while it is noise there. The same
/// plainness as the plan: adjusted closes, no fees, no dividends reinvested, so
/// the numbers describe the price series and say so on the frame.
/// </summary>
public static class PositionLoader
{
    public static async Task<PositionSeries> LoadAsync(
        TencentKline kline,
        string code,
        string display,
        double capital,
        DateOnly start,
        DateOnly end,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        if (capital <= 0)
        {
            throw new ArgumentException("The capital must be positive.", nameof(capital));
        }

        var closes = await HistoryWalk.ClosesAsync(kline, code, display, start, end, progress, cancellation);

        if (closes.Count < 2)
        {
            throw new InvalidOperationException($"{code}: not enough daily bars to hold.");
        }

        // Bought once, at the first close the range actually holds. The walk trims
        // to what the source has, so this is the first trading day of the holding,
        // not the calendar date someone asked for.
        var days = closes.Keys.ToArray();
        var buyPrice = closes[days[0]];
        var shares = capital / buyPrice;

        var points = new List<PositionPoint>(days.Length);

        var peak = double.NegativeInfinity;
        var maxDrawdown = 0d;

        foreach (var day in days)
        {
            var value = shares * closes[day];

            // The drawdown is measured against the running peak of this holding's
            // own value, which is the question a holder asks ("how far down was I"),
            // not against the capital — a position that never fell below its cost
            // still fell, and by more than a return figure shows.
            if (value > peak)
            {
                peak = value;
            }

            maxDrawdown = Math.Max(maxDrawdown, peak > 0 ? (1 - value / peak) * 100 : 0);

            points.Add(new PositionPoint(day, capital, value));
        }

        return new PositionSeries(code, display, points, capital, buyPrice, maxDrawdown);
    }
}
