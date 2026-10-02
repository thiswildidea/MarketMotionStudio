using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The eight holdings the page races, grouped by what they are a claim on.
///
/// An index is a number someone publishes; these are things you can hold, and that is the whole
/// reason this board exists beside the index race. Each row is a fund quoted on a mainland
/// exchange, so every row is bought with the same money, in the same currency, through the same
/// broker — and the overseas ones carry the exchange rate inside them, which is what a mainland
/// holder's return actually was.
///
/// **Why funds and not the indices they track.** Because the index race already draws the
/// indices, and because an index cannot be bought. Tracking error, fees, the premium a
/// cross-border fund trades at when demand outruns its quota, and a share split that multiplies
/// your units and divides their price are all part of what a holder got. A board drawn on the
/// index would be a board about a number nobody could have owned.
///
/// **The roster is a judgement, and the shortest rows say so by joining late.** The commodity
/// fund starts in 2019 and the money-market fund's own series is only trustworthy from 2013, so
/// on a ten-year board they simply are not there at the start — the same rule the index race
/// established, and for the same reason: a row given a zero before its own history began would
/// rank above every asset that was ever down.
/// </summary>
public static class AssetClassLists
{
    public const string AllKey = "All";

    public const string EquityKey = "Equity";

    public const string NonEquityKey = "NonEquity";

    /// <summary>
    /// Shares in companies, four ways: the mainland's large caps, its mid caps, New York, and
    /// Hong Kong. Four, because one domestic row alone would make this a board about whether
    /// this market went up.
    /// </summary>
    public static readonly RaceEntry[] Equity =
    [
        new("sh510300", "沪深300ETF"),
        new("sh510500", "中证500ETF"),
        new("sh513100", "纳指ETF"),
        new("sz159920", "恒生ETF"),
    ];

    /// <summary>
    /// Everything that is not a share: government bonds, gold, a commodity, and cash. The last
    /// one earns its place by being the line every other row is measured against — an asset that
    /// returned nothing would still have beaten staying in cash on some of these years.
    /// </summary>
    public static readonly RaceEntry[] NonEquity =
    [
        new("sh511010", "国债ETF"),
        new("sh518880", "黄金ETF"),
        new("sz159985", "豆粕ETF"),
        new("sh511880", "货币ETF"),
    ];

    /// <summary>All eight, shares first: the board the page opens on.</summary>
    public static readonly RaceEntry[] All = [.. Equity.Concat(NonEquity)];

    public static IReadOnlyList<RaceEntry> Of(string key) => key switch
    {
        EquityKey => Equity,
        NonEquityKey => NonEquity,
        _ => All,
    };

    public static string KeyOf(IReadOnlyList<RaceEntry> list) =>
        list.Count == 0 ? AllKey
            : list[0].Code == Equity[0].Code ? EquityKey
            : list[0].Code == NonEquity[0].Code ? NonEquityKey
            : AllKey;
}

/// <summary>
/// Runs the eight holdings against each other over one range: the cumulative change in each,
/// month by month.
///
/// **The one decision that separates this board from the index race is the adjustment.** The
/// index race is drawn from <see cref="TencentKline.RawBarsAsync"/> — unadjusted, because an
/// index pays no dividend and because an adjustment rebases its series. This board is drawn from
/// <see cref="TencentKline.TotalReturnBarsAsync"/> — dividends and splits put back — because
/// what is being raced here is money, and most of what a bond and all of what a cash fund pays
/// you never appears in its price:
///
/// * the money-market fund's price goes from 100.161 to 100.901 across thirteen years. Unadjusted
///   that is +0.0%, which would put cash at the bottom of a board on which it never once fell,
///   and tell the reader that holding cash was the worst available choice. Adjusted it is +34%;
/// * a Nasdaq fund quoted at 0.998 in 2013 and 2.352 today looks, unadjusted, like +136% over
///   thirteen years. The index it tracks rose sixfold over the last decade alone, and the
///   difference is a share split: the holder's units were multiplied by exactly what their price
///   was divided by.
///
/// Both of those are wrong in the same direction and by a lot, so this is not a matter of taste.
/// It is also the reason the two boards cannot share a loader despite looking alike: same
/// arithmetic, opposite series, and the reason has to be readable where the call is made.
///
/// **Monthly, one request per holding.** The endpoint answers a whole monthly history in one
/// reply against a 430-month ceiling, so there is no walk here — and every one of these funds
/// trades on the mainland's calendar, so a monthly axis is also one on which no row is missing a
/// point another row has.
///
/// **A row that has not started yet is not on the board.** Each row joins on its own first month
/// inside the range and is measured from that month's close, so what is compared is the change
/// each holding made, never the level it happened to be quoted at.
/// </summary>
public static class AssetRace
{
    private const string Period = "month";

    /// <summary>
    /// More months than the endpoint will answer in one request carries: it returns what it has,
    /// which for these codes is everything.
    /// </summary>
    private const int MonthsWanted = 430;

    /// <summary>Less than a year of months and a long run is a sprint.</summary>
    public const int FewestMonths = 12;

    public static async Task<SectorRaceSeries> LoadAsync(
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
            // for the other one, because picking the wrong one here produces a board that is
            // plausible, complete, and wrong by a factor of five on two of its eight rows.
            var bars = await kline.TotalReturnBarsAsync(
                entry.Code, Period, start, end, MonthsWanted, cancellation);

            var byMonth = new Dictionary<DateOnly, double>();

            // The last bar in a month is the month: a request that straddles one can return it
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
            throw new InvalidOperationException(Strings.Get("AssetRaceTooFew"));
        }

        var returns = new List<double[]>();
        var starts = new List<int>();

        for (var k = 0; k < assets.Count; k++)
        {
            var row = new double[dates.Length];

            // Its own first quoted month inside the range. Everything before it is absence, not
            // a value: a fund launched in 2019 measured from 2016 would carry the three years it
            // did not exist as a zero, and a zero sits above every asset that was ever down.
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
                returns.Add(row);
                continue;
            }

            var @base = perAsset[k][dates[own]];

            for (var i = own; i < dates.Length; i++)
            {
                if (perAsset[k].TryGetValue(dates[i], out var close) && close > 0)
                {
                    row[i] = ((close / @base) - 1) * 100;
                }
            }

            returns.Add(row);
        }

        if (starts.All(s => s == int.MaxValue))
        {
            throw new InvalidOperationException(Strings.Get("AssetRaceTooFew"));
        }

        // Named in the interface's own language: the source answers these codes with Chinese
        // names, and `INST*` is how a frame drawn on an English interface still reads "CSI 300
        // ETF".
        var entries = assets
            .Select(e => new RaceEntry(e.Code, InstrumentNames.Display(e.Code, e.Name)))
            .ToArray();

        // The amount slot carries the same numbers. This board is drawn on the return metric and
        // nothing here reads the other one — a fund's accumulated turnover would mean nothing
        // beside a percentage — but the series type is built for two measures off one fetch, and
        // an array of zeros would be a claim that one exists.
        return new SectorRaceSeries(entries, dates, returns, returns, starts);
    }

    /// <summary>
    /// The final standings, best first, over the rows that were ever on the board.
    ///
    /// Not <see cref="SectorRaceSeries.Standings"/>, which includes every racer: a fund with no
    /// month of its own inside the range holds a final value of zero, and a status line that
    /// called it the bottom of the list would be naming a fund the picture never showed.
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

    /// <summary>How many of the group's holdings the source answered for at all.</summary>
    public static int Quoted(SectorRaceSeries series) =>
        Enumerable.Range(0, series.Racers).Count(k => series.StartOf(k) < int.MaxValue);

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));
}
