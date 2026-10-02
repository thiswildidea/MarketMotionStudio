using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One currency pair: the code the source quotes it under, and the pair written the way a screen
/// writes it — <c>USD/CNY</c>.
///
/// The name needs no translating, which is the one thing on this page that is true of nothing
/// else in the app: every other board's rows are companies and indices, and those carry
/// <c>INST*</c> keys because the source's own name for them is Chinese and a frame drawn on an
/// English interface would otherwise read it out. A three-letter currency code is ISO's, and
/// the same six characters are what a dealer in Frankfurt and one in Osaka both type.
/// </summary>
public sealed record FxPair(string Code, string Pair);

/// <summary>
/// The two lists the page offers, and why they are two.
///
/// They are not two because one is "Chinese" — the source's foreign-exchange series splits by
/// when it started quoting each pair, and mixing the two lists on one board would put a pair
/// with twenty-one years of history next to one with nine and a bit, which reads as a comment
/// on the currencies rather than on the data. So the page offers them separately and says in
/// its own note which one reaches back how far.
/// </summary>
public static class FxLists
{
    public const string CnyKey = "Cny";

    public const string CrossesKey = "Crosses";

    /// <summary>
    /// The renminbi against six others.
    ///
    /// USD/CNY is the long one: 316 months, from 2005-10, which is the month after the peg was
    /// loosened and the first month the series has a price worth drawing. The other five start
    /// at 2016-01 and carry 124 months each, which is the source's own coverage and not a
    /// choice — a board of all six therefore fills in as 2016 arrives.
    /// </summary>
    public static readonly FxPair[] Cny =
    [
        new("whUSDCNY", "USD/CNY"),
        new("whEURCNY", "EUR/CNY"),
        new("whHKDCNY", "HKD/CNY"),
        new("whGBPCNY", "GBP/CNY"),
        new("whAUDCNY", "AUD/CNY"),
        new("whCADCNY", "CAD/CNY"),
    ];

    /// <summary>
    /// The major crosses: 325 months each, from 2005-07, and all six of them from the same
    /// month — which is the reason the corridor is worth drawing on this list at its longest.
    /// </summary>
    public static readonly FxPair[] Crosses =
    [
        new("whEURUSD", "EUR/USD"),
        new("whGBPUSD", "GBP/USD"),
        new("whAUDUSD", "AUD/USD"),
        new("whUSDJPY", "USD/JPY"),
        new("whUSDCHF", "USD/CHF"),
        new("whUSDCAD", "USD/CAD"),
    ];

    public static IReadOnlyList<FxPair> Of(string key) => key == CrossesKey ? Crosses : Cny;

    public static string KeyOf(IReadOnlyList<FxPair> list) =>
        list.Count > 0 && list[0].Code == Crosses[0].Code ? CrossesKey : CnyKey;
}

/// <summary>
/// One pair's own corridor, month by month: the rate itself and the widest the pair has been
/// inside the span.
///
/// Carried per pair rather than as one corridor for the board, because a corridor is a property
/// of one pair: 157.92 on USD/JPY and 1.1245 on EUR/USD are not two positions on one scale,
/// and the board's whole claim is that each pair is measured against its own.
/// </summary>
public sealed class FxCorridorSeries
{
    public FxCorridorSeries(
        FxPair[] pairs, DateOnly[] dates, double[][] closes, double[][] lows, double[][] highs)
    {
        Pairs = pairs;
        Dates = dates;
        Closes = closes;
        Lows = lows;
        Highs = highs;
    }

    public FxPair[] Pairs { get; }

    /// <summary>One entry per month, dated to the last day of the month it stands for.</summary>
    public DateOnly[] Dates { get; }

    /// <summary><c>Closes[k][i]</c> is pair k's rate in month i; zero where it was not quoted.</summary>
    public double[][] Closes { get; }

    /// <summary>The month's own low, and its high — the corridor is built out of these.</summary>
    public double[][] Lows { get; }

    public double[][] Highs { get; }

    public int Months => Dates.Length;

    public int Racers => Pairs.Length;

    /// <summary>
    /// How many pairs the source actually returned something for.
    ///
    /// A list whose six pairs were all asked for is not a list whose six pairs all answered,
    /// and a status line counting the request rather than the reply is a sentence about what
    /// was attempted.
    /// </summary>
    public int Quoted => Enumerable.Range(0, Racers).Count(k => Closes[k].Any(v => v > 0));
}

/// <summary>
/// Loads the pairs' monthly bars and lays them on one axis.
///
/// **Monthly, and one request per pair.** The endpoint answers a whole history in one reply —
/// 325 months against a 430-month ceiling — so there is no walk here and no paging, which is
/// also why the page can offer "as far back as there is" without costing twenty requests.
///
/// **The axis is a month, keyed by year and month.** Each pair closes its month on its own
/// venue's last trading day, and an intersection taken on the date itself would drop a month
/// whenever one pair settled a day later than another — the same defect the A+H page has and
/// the same fix.
///
/// **Unquoted months are zero, not carried forward.** A pair the source has nothing for has no
/// rate, and a carried-forward rate draws a row that stands still for years and then starts
/// moving, which claims the currency did nothing when what happened is that nobody recorded
/// it. Zero means "not on the board", which the renderer treats as absent.
/// </summary>
public static class FxRates
{
    private const string Period = "month";

    /// <summary>More months than any pair has: the source answers with what it has.</summary>
    private const int MonthsWanted = 360;

    /// <summary>
    /// Fewer than this and a corridor is a couple of months wide, which is a range, not a
    /// corridor.
    /// </summary>
    public const int FewestMonths = 12;

    public static async Task<FxCorridorSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<FxPair> pairs,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var perPair = new List<Dictionary<DateOnly, TencentKline.CandleBar>>(pairs.Count);

        for (var i = 0; i < pairs.Count; i++)
        {
            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})", pairs[i].Pair, i + 1, pairs.Count));

            var bars = await kline.RawBarsAsync(
                pairs[i].Code, Period, start, end, MonthsWanted, cancellation);

            var byMonth = new Dictionary<DateOnly, TencentKline.CandleBar>();

            // The last bar in a month is the month: the endpoint can return a month twice when
            // a request straddles it, and the earlier of the two is a partial month.
            foreach (var bar in bars)
            {
                if (bar.Close <= 0 || bar.Date < start || bar.Date > end)
                {
                    continue;
                }

                var key = MonthEnd(bar.Date.Year, bar.Date.Month);

                if (!byMonth.TryGetValue(key, out var held) || bar.Date >= held.Date)
                {
                    byMonth[key] = bar;
                }
            }

            perPair.Add(byMonth);
        }

        var dates = perPair
            .SelectMany(d => d.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        if (dates.Length < FewestMonths)
        {
            throw new InvalidOperationException(Strings.Get("FxCorridorTooFew"));
        }

        var closes = new double[pairs.Count][];
        var lows = new double[pairs.Count][];
        var highs = new double[pairs.Count][];

        for (var k = 0; k < pairs.Count; k++)
        {
            closes[k] = new double[dates.Length];
            lows[k] = new double[dates.Length];
            highs[k] = new double[dates.Length];

            for (var i = 0; i < dates.Length; i++)
            {
                if (perPair[k].TryGetValue(dates[i], out var bar))
                {
                    closes[k][i] = bar.Close;
                    lows[k][i] = bar.Low > 0 ? bar.Low : bar.Close;
                    highs[k][i] = bar.High > 0 ? bar.High : bar.Close;
                }
            }
        }

        return new FxCorridorSeries([.. pairs], dates, closes, lows, highs);
    }

    /// <summary>
    /// Where each pair sits in its own corridor on the last month, highest first.
    ///
    /// 100% is the corridor's ceiling — the pair has not been dearer at any point in the span —
    /// and 0% is its floor. The board is sorted by this, so a status line reporting the top and
    /// the bottom of it is reporting the two rows the final frame puts first and last.
    /// </summary>
    public static (int Index, double Position)[] Standings(FxCorridorSeries series)
    {
        var last = series.Months - 1;
        var outList = new List<(int Index, double Position)>();

        for (var k = 0; k < series.Racers; k++)
        {
            if (series.Closes[k][last] > 0)
            {
                outList.Add((k, Corridor.Position(series, k, last)));
            }
        }

        return [.. outList.OrderByDescending(s => s.Position).ThenBy(s => s.Index)];
    }

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));

    /// <summary>Owns the arithmetic the renderer draws, so the two cannot disagree.</summary>
    public static class Corridor
    {
        /// <summary>
        /// The corridor as it stood at month <paramref name="i"/>: the lowest low and the
        /// highest high **so far**, not over the whole span.
        ///
        /// An expanding window, which is what makes the picture a corridor rather than a
        /// gauge: the walls are where the pair has been, so early on they are narrow and the
        /// rate fills them, and a month that goes further than any month before it pushes one
        /// of them outwards. Drawing the whole span's range from the first frame would give a
        /// fixed ruler and a dot moving along it.
        /// </summary>
        public static (double Low, double High) Walls(FxCorridorSeries series, int k, int i)
        {
            var low = double.MaxValue;
            var high = double.MinValue;

            for (var m = 0; m <= i; m++)
            {
                if (series.Closes[k][m] <= 0)
                {
                    continue;
                }

                low = Math.Min(low, series.Lows[k][m]);
                high = Math.Max(high, series.Highs[k][m]);
            }

            if (low > high)
            {
                return (0, 0);
            }

            return (low, high);
        }

        /// <summary>
        /// Where the rate is between those two walls, 0 at the floor and 1 at the ceiling.
        /// </summary>
        public static double Position(FxCorridorSeries series, int k, int i)
        {
            var close = series.Closes[k][i];

            if (close <= 0)
            {
                return 0;
            }

            var (low, high) = Walls(series, k, i);

            // One month of history is a corridor of zero width, and a rate divided by its own
            // zero width is not a position. Midway is the honest answer for a corridor that has
            // not been walked in yet — it is not a claim that the rate is mid-range.
            return high - low <= 0 ? 0.5 : Math.Clamp((close - low) / (high - low), 0, 1);
        }
    }
}
