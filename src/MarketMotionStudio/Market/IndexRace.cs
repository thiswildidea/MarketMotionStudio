using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The groups of indices the page offers, and why the widest one is a group at all.
///
/// Every other board in this app is drawn from one market — the market the settings page chose —
/// and every entry on it is quoted by the same venue. This board is the exception: it puts the
/// three markets on one axis, so it is **not governed by the market setting** and never asks it.
/// That is also why the groups are offered rather than derived: "which indices" is the page's
/// own question, and the answer is a hand-picked dozen rather than whatever one market's roster
/// happens to hold.
/// </summary>
public static class WorldIndexLists
{
    public const string AllKey = "All";

    public const string AShareKey = "AShare";

    public const string HongKongKey = "HongKong";

    public const string UnitedStatesKey = "UnitedStates";

    /// <summary>
    /// The mainland's own: the composite, the two cap-weighted benchmarks, a mid-cap board, a
    /// growth board and the large-cap half of Shanghai. Six, because a race with two entrants
    /// from one market is a race between two things that move together.
    /// </summary>
    public static readonly RaceEntry[] AShare =
    [
        new("sh000001", "上证指数"),
        new("sh000300", "沪深300"),
        new("sz399001", "深证成指"),
        new("sh000905", "中证500"),
        new("sz399006", "创业板指"),
        new("sh000016", "上证50"),
    ];

    /// <summary>Hong Kong's three: the index, its mainland-constituent sibling, and the tech board.</summary>
    public static readonly RaceEntry[] HongKong =
    [
        new("hkHSI", "恒生指数"),
        new("hkHSCEI", "国企指数"),
        new("hkHSTECH", "恒生科技"),
    ];

    /// <summary>
    /// New York's three. The source reaches back to 1950 on the S&amp;P and only to 2009 on the
    /// Dow, which is the reason this board has to know when each row joined — see
    /// <see cref="IndexRace.LoadAsync"/>.
    /// </summary>
    public static readonly RaceEntry[] UnitedStates =
    [
        new("usINX", "标普500"),
        new("usIXIC", "纳斯达克"),
        new("usDJI", "道琼斯"),
    ];

    /// <summary>All twelve, in market order: the board the page opens on.</summary>
    public static readonly RaceEntry[] All = [.. AShare.Concat(HongKong).Concat(UnitedStates)];

    public static IReadOnlyList<RaceEntry> Of(string key) => key switch
    {
        AShareKey => AShare,
        HongKongKey => HongKong,
        UnitedStatesKey => UnitedStates,
        _ => All,
    };

    public static string KeyOf(IReadOnlyList<RaceEntry> list) =>
        list.Count == 0 ? AllKey
            : list[0].Code == AShare[0].Code ? AShareKey
            : list[0].Code == HongKong[0].Code ? HongKongKey
            : list[0].Code == UnitedStates[0].Code ? UnitedStatesKey
            : AllKey;
}

/// <summary>
/// Runs the twelve indices against each other over one range: the cumulative change in each,
/// month by month.
///
/// **Monthly, and one request per index.** The endpoint answers a whole monthly history in one
/// reply — 430 months against a 430-month ceiling — so there is no walk here. A daily board
/// across three markets would also be a board of mismatched sessions: the mainland's holidays
/// are not Hong Kong's and neither is New York's, and a day any one of them lacked would either
/// drop out of every row or be carried forward into a claim that nothing moved.
///
/// **Unadjusted, and that is the whole of the comparison.** Every other board here is drawn from
/// an adjusted series, because a dividend is not a fall. An index has no dividend to adjust for
/// — but that is not the reason. The reason is the one the A+H page found: an adjustment is a
/// rebasing of one series, and putting two rebased series side by side compares two different
/// things. `RawBarsAsync` is the call that cannot be something else by accident.
///
/// **A row that has not started yet is not on the board**, and this is the one board that needs
/// saying. The S&amp;P reaches back to 1950, the Dow to 2009, 恒生科技 to 2020. On a shared axis
/// that begins in 1950, the honest picture is a board that fills in: each row joins on its own
/// first month and is measured from that month's close — so what is compared is the *change*
/// each index made, never the level it happened to be quoted at. A row given a zero before its
/// own history began would sit at 0.00% for decades, rank above every index that was ever down,
/// and read as a market that did nothing.
///
/// **The axis is a month, keyed by year and month.** Each index closes its month on its own
/// venue's last trading day, and an intersection taken on the date itself would drop a month
/// whenever one venue settled a day later than another — the same defect the A+H page has and
/// the same fix.
/// </summary>
public static class IndexRace
{
    private const string Period = "month";

    /// <summary>
    /// More months than the endpoint will answer in one request carries: it returns what it has,
    /// which for these codes is 430 on the mainland ones and everything on the others.
    /// </summary>
    private const int MonthsWanted = 430;

    /// <summary>
    /// Fewer than a year of months and a "long run" is a sprint: twelve bars is barely enough to
    /// say who is ahead.
    /// </summary>
    public const int FewestMonths = 12;

    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> indices,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var perIndex = new List<Dictionary<DateOnly, double>>(indices.Count);

        for (var i = 0; i < indices.Count; i++)
        {
            var entry = indices[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})",
                InstrumentNames.Display(entry.Code, entry.Name), i + 1, indices.Count));

            var bars = await kline.RawBarsAsync(
                entry.Code, Period, start, end, MonthsWanted, cancellation);

            var byMonth = new Dictionary<DateOnly, double>();

            // The last bar in a month is the month: the endpoint can return a month twice when a
            // request straddles it, and the earlier of the two is a partial month.
            foreach (var bar in bars)
            {
                if (bar.Close <= 0 || bar.Date < start || bar.Date > end)
                {
                    continue;
                }

                // Bars arrive oldest first, so the last row carrying a month is that month: a
                // request that straddles one can return it twice, and the earlier of the two is
                // the partial.
                byMonth[MonthEnd(bar.Date.Year, bar.Date.Month)] = bar.Close;
            }

            perIndex.Add(byMonth);
        }

        var dates = perIndex
            .SelectMany(d => d.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        if (dates.Length < FewestMonths)
        {
            throw new InvalidOperationException(Strings.Get("IndexRaceTooFew"));
        }

        var returns = new List<double[]>();
        var starts = new List<int>();

        for (var k = 0; k < indices.Count; k++)
        {
            var row = new double[dates.Length];

            // Its own first quoted month inside the range. Everything before it is absence, not
            // a value: measured from the board's first month instead, a row that joined in 2020
            // would carry the whole run it missed as a zero.
            var own = -1;

            for (var i = 0; i < dates.Length && own < 0; i++)
            {
                if (perIndex[k].ContainsKey(dates[i]))
                {
                    own = i;
                }
            }

            starts.Add(own < 0 ? int.MaxValue : own);

            if (own < 0)
            {
                returns.Add(row);
                continue;
            }

            var @base = perIndex[k][dates[own]];

            for (var i = own; i < dates.Length; i++)
            {
                if (perIndex[k].TryGetValue(dates[i], out var close) && close > 0)
                {
                    row[i] = ((close / @base) - 1) * 100;
                }
            }

            returns.Add(row);
        }

        if (starts.All(s => s == int.MaxValue))
        {
            throw new InvalidOperationException(Strings.Get("IndexRaceTooFew"));
        }

        // Named in the interface's own language, which is the one place the row's identity is
        // decided: the source answers these codes with Chinese names, and `INST*` is how a frame
        // drawn on an English interface still reads "S&P 500".
        var entries = indices
            .Select(e => new RaceEntry(e.Code, InstrumentNames.Display(e.Code, e.Name)))
            .ToArray();

        // The amount slot carries the same numbers. This board is drawn on the return metric and
        // nothing here reads the other one — an index has no turnover to accumulate that would
        // mean anything beside a percentage — but the series type is built for two measures off
        // one fetch, and an array of zeros would be a claim that one exists.
        return new SectorRaceSeries(entries, dates, returns, returns, starts);
    }

    /// <summary>
    /// The final standings, best first, over the rows that were ever on the board.
    ///
    /// Not <see cref="SectorRaceSeries.Standings"/>, which includes every racer: an index with no
    /// month of its own inside the range holds a final value of zero, and a status line that
    /// called it the bottom of the list would be naming an index the picture never showed.
    /// </summary>
    public static (int Index, double Value)[] Standings(SectorRaceSeries series)
    {
        var last = series.Days - 1;
        var outList = new List<(int Index, double Value)>();

        for (var k = 0; k < series.Racers; k++)
        {
            if (series.StartOf(k) <= last)
            {
                outList.Add((k, series.Returns[k][last]));
            }
        }

        return [.. outList.OrderByDescending(s => s.Value).ThenBy(s => s.Index)];
    }

    /// <summary>How many of the group's indices the source answered for at all.</summary>
    public static int Quoted(SectorRaceSeries series) =>
        Enumerable.Range(0, series.Racers).Count(k => series.StartOf(k) < int.MaxValue);

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));
}
