using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One holding's distance below its own high, month by month.
///
/// The fourteenth page says what a holding earned. This one says what it cost to earn it: how far
/// below its own high a holder sat, and how long it took to get back. Those are two different
/// numbers and they do not rise together — over the last ten years the Nasdaq fund fell 25.5% and
/// was back at its high in six months, while the CSI 500 fund fell 56% and took eighty-six. A
/// board that printed only the depth would rank the two the wrong way round for anyone deciding
/// whether they could have held on.
/// </summary>
/// <param name="Entries">The holdings, in roster order.</param>
/// <param name="Dates">The months any holding has, ascending.</param>
/// <param name="Underwater">Per holding, per cent below its own high so far. Zero or negative.</param>
/// <param name="Starts">Per holding, the month it joins the board; past the end when never.</param>
/// <param name="Deepest">Per holding, the most negative point of <paramref name="Underwater"/>.</param>
/// <param name="HealedMonths">
/// Per holding, the months from its deepest point to the close that regained the high it fell
/// from: 0 when it never fell, <see cref="Drawdown.NotHealed"/> when the range ends first.
/// </param>
public sealed record DrawdownSeries(
    IReadOnlyList<RaceEntry> Entries,
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<double[]> Underwater,
    IReadOnlyList<int> Starts,
    IReadOnlyList<double> Deepest,
    IReadOnlyList<int> HealedMonths)
{
    public int Days => Dates.Count;

    public int Racers => Entries.Count;

    /// <summary>The month holding <paramref name="k"/> joins the board, or a month past the end.</summary>
    public int StartOf(int k) => k < Starts.Count ? Starts[k] : 0;
}

/// <summary>
/// Runs the eight holdings against their own history rather than against each other.
///
/// **Adjusted, for the same reason the asset race is.** What is measured here is what a holder
/// had, and a fund's distributions never appear in its price — a money-market fund's price barely
/// moves while its holder earned a fifth, and a fund that split its units shows a cliff that no
/// holder experienced. Measured unadjusted, the one row here that never fell would look like it
/// had spent a decade in a hole it was never in. See <see cref="AssetRace"/>.
///
/// **The high is each holding's own, and it starts on its own first month.** A holding that
/// joins in 2019 is not measured against a 2016 high it did not have — it starts level, at zero
/// below its own high, and every month after that is a month it was actually held. This is the
/// rule the index race established and it matters more here: on a board of depths, a row given a
/// fake −40% for years it did not exist would sit at the bottom of a board whose bottom is the
/// worst place on it.
///
/// **The depth and the climb are measured in that order.** The deepest month has to be final
/// before "how long to climb back" means anything. Written as one pass, a shallow dip early in
/// the range sets the clock and the real fall is never timed at all — which is exactly what the
/// first draft of the probe that sized this page did, and it reported every holding healed in one
/// or two months on a board where one of them took seven years.
/// </summary>
public static class Drawdown
{
    private const string Period = "month";

    /// <summary>More months than the endpoint answers in one request: it returns what it has.</summary>
    private const int MonthsWanted = 430;

    /// <summary>Less than a year of months and a depth is a wobble.</summary>
    public const int FewestMonths = 12;

    /// <summary>The range ended before the high was regained.</summary>
    public const int NotHealed = -1;

    /// <summary>Never below its own high inside the range at all.</summary>
    public const int NeverFell = 0;

    /// <summary>Shallower than this and the holding did not meaningfully fall.</summary>
    private const double Flat = 0.005;

    public static async Task<DrawdownSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> assets,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var perAsset = new List<Dictionary<DateOnly, double>>(assets.Count);

        for (var i = 0; i < assets.Count; i++)
        {
            var entry = assets[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})",
                InstrumentNames.Display(entry.Code, entry.Name), i + 1, assets.Count));

            // Adjusted, not raw: see the class note. The one call whose name cannot be mistaken
            // for the other one — a raw series here puts a hole in a row that never had one.
            var bars = await kline.TotalReturnBarsAsync(
                entry.Code, Period, start, end, MonthsWanted, cancellation);

            var byMonth = new Dictionary<DateOnly, double>();

            // The last bar in a month is the month: a request that straddles one returns it
            // twice, and the earlier of the two is the partial.
            foreach (var bar in bars)
            {
                if (bar.Close <= 0 || bar.Date < start || bar.Date > end)
                {
                    continue;
                }

                byMonth[MonthEnd(bar.Date.Year, bar.Date.Month)] = bar.Close;
            }

            perAsset.Add(byMonth);
        }

        var dates = perAsset
            .SelectMany(d => d.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        if (dates.Length < FewestMonths)
        {
            throw new InvalidOperationException(Strings.Get("DrawdownTooFew"));
        }

        var underwater = new List<double[]>();
        var starts = new List<int>();
        var deepest = new List<double>();
        var healed = new List<int>();

        for (var k = 0; k < assets.Count; k++)
        {
            var row = new double[dates.Length];

            // Its own first quoted month inside the range. Everything before it is absence, not
            // a value: a fund launched in 2019 measured from 2016 would carry three years it did
            // not exist as a depth, and a fake depth is the worst place on this board.
            var own = -1;

            for (var i = 0; i < dates.Length && own < 0; i++)
            {
                if (perAsset[k].ContainsKey(dates[i]))
                {
                    own = i;
                }
            }

            starts.Add(own < 0 ? int.MaxValue : own);

            if (own < 0)
            {
                underwater.Add(row);
                deepest.Add(0);
                healed.Add(NeverFell);
                continue;
            }

            // Pass one: the high in force at each month, and how far below it the close was.
            // A month the source skips holds the month before it — the hole is the source's, not
            // the holding's, and a month quoted at zero would read as a total loss.
            var closes = new double[dates.Length];
            var highs = new double[dates.Length];
            var last = perAsset[k][dates[own]];
            var high = last;

            for (var i = own; i < dates.Length; i++)
            {
                if (perAsset[k].TryGetValue(dates[i], out var close) && close > 0)
                {
                    last = close;
                }

                if (last > high)
                {
                    high = last;
                }

                closes[i] = last;
                highs[i] = high;
                row[i] = ((last / high) - 1) * 100;
            }

            // The deepest month, and the high it fell from. Both have to be final before the
            // climb can be timed — see the class note.
            var at = own;
            var worst = 0.0;

            for (var i = own; i < dates.Length; i++)
            {
                if (row[i] < worst)
                {
                    worst = row[i];
                    at = i;
                }
            }

            var from = highs[at];
            var months = worst > -Flat ? NeverFell : NotHealed;

            // Pass two: the first close back at the high the deepest month fell from. Not the
            // first month back at zero-below-its-high — a holding can set a new high on the way
            // back up and be level without ever having recovered the fall, and level is not the
            // same word as mended.
            if (months == NotHealed)
            {
                for (var i = at + 1; i < dates.Length; i++)
                {
                    if (closes[i] >= from)
                    {
                        months = i - at;
                        break;
                    }
                }
            }

            underwater.Add(row);
            deepest.Add(worst);
            healed.Add(months);
        }

        if (starts.All(s => s == int.MaxValue))
        {
            throw new InvalidOperationException(Strings.Get("DrawdownTooFew"));
        }

        // Named in the interface's own language: the source answers these codes with Chinese
        // names, and `INST*` is how a frame drawn on an English interface still reads "CSI 300
        // ETF".
        var entries = assets
            .Select(e => new RaceEntry(e.Code, InstrumentNames.Display(e.Code, e.Name)))
            .ToArray();

        return new DrawdownSeries(entries, dates, underwater, starts, deepest, healed);
    }

    /// <summary>
    /// The closing standings, shallowest first — the holding closest to its own high leads.
    ///
    /// Over the rows that were ever on the board: one with no month of its own inside the range
    /// holds a final depth of zero, and a status line calling it the leader would be naming a
    /// holding the picture never showed.
    /// </summary>
    public static (int Index, double Value)[] Standings(DrawdownSeries series)
    {
        var last = series.Days - 1;
        var outList = new List<(int Index, double Value)>();

        for (var k = 0; k < series.Racers; k++)
        {
            if (series.StartOf(k) <= last)
            {
                outList.Add((k, series.Underwater[k][last]));
            }
        }

        return [.. outList.OrderByDescending(s => s.Value).ThenBy(s => s.Index)];
    }

    /// <summary>
    /// The holding that fell furthest at any point in the range.
    ///
    /// Not the deepest one today, which is what <see cref="Standings"/>' last row is: a holding
    /// can have been 56% under water in 2018 and be 3% under water now, and a status line that
    /// named the row at the bottom of today's board would be naming the wrong fall — the one this
    /// page exists to report is the worst one, whenever it happened.
    /// </summary>
    public static (int Index, double Value) Worst(DrawdownSeries series)
    {
        var at = -1;
        var worst = 0.0;

        for (var k = 0; k < series.Racers; k++)
        {
            if (series.StartOf(k) >= series.Days)
            {
                continue;
            }

            if (at < 0 || series.Deepest[k] < worst)
            {
                worst = series.Deepest[k];
                at = k;
            }
        }

        return (at, worst);
    }

    /// <summary>How many of the group's holdings the source answered for at all.</summary>
    public static int Quoted(DrawdownSeries series) =>
        Enumerable.Range(0, series.Racers).Count(k => series.StartOf(k) < int.MaxValue);

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));
}
