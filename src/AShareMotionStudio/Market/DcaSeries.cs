using System.Globalization;

namespace AShareMotionStudio.Market;

/// <summary>How often a plan buys.</summary>
public enum DcaFrequency
{
    /// <summary>Every trading day, the way the source video that inspired the page does it.</summary>
    Daily = 0,

    /// <summary>The first trading day of each ISO week.</summary>
    Weekly = 1,

    /// <summary>The first trading day of each month.</summary>
    Monthly = 2,
}

/// <summary>One day of the plan, as the chart draws it.</summary>
/// <param name="Date">The trading day.</param>
/// <param name="Invested">What has been paid in so far, in the venue's currency.</param>
/// <param name="Value">What the accumulated shares are worth at that day's close.</param>
public sealed record DcaPoint(DateOnly Date, double Invested, double Value);

/// <summary>
/// One plan run to the end of its data: the daily marks, and the closing figures the
/// statistic cards read out.
/// </summary>
public sealed record DcaSeries(
    string Code,
    string Name,
    IReadOnlyList<DcaPoint> Points,
    int Buys,
    double Amount,
    DcaFrequency Frequency)
{
    public DateOnly Start => Points[0].Date;

    public DateOnly End => Points[^1].Date;

    public double FinalInvested => Points[^1].Invested;

    public double FinalValue => Points[^1].Value;

    public double Profit => FinalValue - FinalInvested;

    /// <summary>The headline percentage: what the plan returned over what was paid in.</summary>
    public double ReturnPercent => FinalInvested > 0 ? (FinalValue / FinalInvested - 1) * 100 : 0;

    /// <summary>The tallest figure either line reaches, for the axis.</summary>
    public double Peak => Math.Max(Points.Max(p => p.Value), Points.Max(p => p.Invested));
}

/// <summary>
/// Builds a plan from one instrument's daily closes.
///
/// The closes come from the same bars endpoint every other page reads, with one
/// difference: a plan is about *years*, and one request carries only
/// <see cref="TencentKline.MostBarsPerRequest"/> bars — about two and a half years.
/// So the range is walked backwards one request at a time, each one ending the day
/// before the earliest bar the last one returned, until the start date is under it
/// or the source stops answering with earlier data.
///
/// The simulation itself is deliberately plain: on each buy date the fixed amount
/// buys <c>amount / close</c> shares at that day's close, and every day is marked
/// with what has been paid in and what the shares are then worth. No fees, no
/// slippage, no timing but the calendar — the closing figures are a description of
/// the price series, not of anything anyone could have executed, which is what the
/// frame's disclaimer says.
/// </summary>
public static class DcaPlanner
{
    /// <summary>
    /// Requests beyond this are not made. Twenty pages is about twelve years of
    /// trading days, which is past where the source's adjusted history thins out
    /// anyway — the walk stops on its own when a page returns nothing earlier, and
    /// this is the backstop that keeps a pathological response from looping.
    /// </summary>
    private const int MostRequests = 20;

    public static async Task<DcaSeries> LoadAsync(
        TencentKline kline,
        string code,
        string display,
        DcaFrequency frequency,
        double amount,
        DateOnly start,
        DateOnly end,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        if (amount <= 0)
        {
            throw new ArgumentException("The amount must be positive.", nameof(amount));
        }

        // ---- the closes, walked backwards a page at a time --------------------------
        var closes = new SortedList<DateOnly, double>();

        var cursor = end;
        var earliestSeen = end;

        for (var request = 0; request < MostRequests; request++)
        {
            progress.Report($"{display}: {closes.Count} …");

            var bars = await kline.StockBarsAsync(code, start, cursor, cancellation);

            if (bars.Count == 0)
            {
                break;
            }

            foreach (var bar in bars)
            {
                closes.TryAdd(bar.Date, bar.Close);
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

        if (closes.Count < 2)
        {
            throw new InvalidOperationException($"{code}: not enough daily bars to plan with.");
        }

        // ---- the simulation ---------------------------------------------------------
        var days = closes.Keys.ToArray();
        var points = new List<DcaPoint>(days.Length);
        var shares = 0d;
        var invested = 0d;
        var buys = 0;

        var lastWeek = ISOWeek.GetWeekOfYear(days[0].ToDateTime(TimeOnly.MinValue));
        var lastMonth = days[0].Month;

        foreach (var day in days)
        {
            var close = closes[day];

            // The week and month are read from the *first trading day* in them, not
            // from a calendar grid: a holiday on a Monday means the week's buy lands
            // on Tuesday, and that is what a person putting money in would have done.
            var dateTime = day.ToDateTime(TimeOnly.MinValue);
            var week = ISOWeek.GetWeekOfYear(dateTime);

            var isBuy = frequency switch
            {
                DcaFrequency.Daily => true,
                DcaFrequency.Weekly => week != lastWeek,
                _ => day.Month != lastMonth,
            };

            lastWeek = week;
            lastMonth = day.Month;

            if (isBuy)
            {
                shares += amount / close;
                invested += amount;
                buys++;
            }

            points.Add(new DcaPoint(day, invested, shares * close));
        }

        return new DcaSeries(code, display, points, buys, amount, frequency);
    }
}
