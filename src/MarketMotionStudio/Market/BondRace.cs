using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The nine bond indices the page races, grouped by whether equity is attached to them.
///
/// **These are indices, not funds, and that is a decision with a cost.** The asset race races
/// things that can be held; this board races numbers that are published. The reason is that the
/// bond world has no equivalent of the four equity ETFs: a mainland bond ETF's price series is
/// dominated by distributions — the urban-construction ETF reads −89% over ten years and the
/// corporate-bond ETF +949% over five, both of them share-class arithmetic rather than a bond
/// market — so a fund and an index on one board would rank a cliff above a coupon. Nine indices
/// are at least measured the same way.
///
/// **The cost is that a coupon is not in the number.** Every row here is a price index: the
/// source ignores the adjustment parameter for an index, so what comes back is what the index
/// was quoted at, and most of what a bond pays a holder never appears in its quote. A board of
/// price indices therefore understates every row, and understates the long-dated credit rows most
/// of all. That belongs in the note the page shows and in the help chapter, not buried here —
/// see <see cref="BondRace"/> for why the loader cannot quietly correct it.
///
/// **Two of the five rows this page was asked for are not in it.** 中证全债 was the fourth name
/// on the list and does not exist on this source: the code that looks like it, <c>sh000023</c>,
/// is 沪分离债 and its monthly series stops at 2015-08, eleven years before the board ends. The
/// whole 000xxx and 399xxx space was swept for a name containing 债 or 券 — twenty-three indices,
/// none of them a total-bond index, because 中证全债 is a 中证指数公司 code (H11001) and was never
/// given a quote symbol. The seats were filled with the deepest credit indices the source does
/// answer. <c>sh000145</c>, asked for as a treasury index, is 优势资源 — an equity index.
///
/// **Names are the source's own.** Every label below is what the snapshot answers for that code,
/// which is what a frame reads through <c>INST*</c> on a non-Chinese interface.
/// </summary>
public static class BondLists
{
    public const string AllKey = "All";

    /// <summary>Credit and rates with no equity attached: the six that behave like bonds.</summary>
    public const string PureKey = "Pure";

    /// <summary>Convertibles: a bond until the underlying runs, then not one at all.</summary>
    public const string ConvertKey = "Convert";

    /// <summary>
    /// Six, ordered by what they are a claim on: the sovereign curve first, then corporate credit
    /// from both exchanges. 沪企债30 is last because it is thirty constituents rather than a whole
    /// market, which is also why it is the row that spends the decade at the bottom.
    /// </summary>
    public static readonly RaceEntry[] Pure =
    [
        new("sh000012", "国债指数"),
        new("sh000013", "企债指数"),
        new("sh000022", "沪公司债"),
        new("sz399301", "深信用债"),
        new("sz399302", "深公司债"),
        new("sh000061", "沪企债30"),
    ];

    /// <summary>
    /// Three, because one convertible row would make the board a story about one exchange's
    /// listing rules. These are the rows that travel the whole board: measured from their own
    /// first month they have held both first and last place inside a decade.
    /// </summary>
    public static readonly RaceEntry[] Convertible =
    [
        new("sh000832", "中证转债"),
        new("sh000139", "上证转债"),
        new("sz399307", "深证转债"),
    ];

    /// <summary>All nine, bonds first: the board the page opens on.</summary>
    public static readonly RaceEntry[] All = [.. Pure.Concat(Convertible)];

    public static IReadOnlyList<RaceEntry> Of(string key) => key switch
    {
        PureKey => Pure,
        ConvertKey => Convertible,
        _ => All,
    };

    public static string KeyOf(IReadOnlyList<RaceEntry> list) =>
        list.Count == 0 ? AllKey
            : list[0].Code == Pure[0].Code ? PureKey
            : list[0].Code == Convertible[0].Code ? ConvertKey
            : AllKey;
}

/// <summary>
/// Runs the nine bond indices against each other over one range: the cumulative change in each,
/// month by month.
///
/// **Unadjusted, and for the opposite reason to the asset race.** That board is drawn from
/// <see cref="TencentKline.TotalReturnBarsAsync"/> because what it races is money and a fund's
/// income is invisible in its price. This one is drawn from
/// <see cref="TencentKline.RawBarsAsync"/> because every row is an index, and an index has no
/// income to put back: the source ignores the adjustment parameter for one and answers with the
/// price series either way. Asking for an adjustment here would not add the coupon — no series on
/// this source carries it — it would only invite a rebasing that differs per code.
///
/// What that leaves is a board of price changes, and the note has to say so: a decade of holding
/// corporate credit earned far more than the +48.66% the 企债指数 row shows, and the gap is not
/// the same on every row. Understating nine rows by different amounts would be dishonest;
/// understating them and saying so in the caption is the best this source allows. It is also why
/// this board and the asset race cannot be read against each other even though they look alike.
///
/// **Monthly, one request per index.** 430 months is the endpoint's ceiling and every one of
/// these series is shorter than that, so there is no walk — nine requests and the board is built.
///
/// **A row that has not started yet is not on the board.** Each row joins on its own first month
/// inside the range and is measured from that month's close. That matters more here than on most
/// boards: 深证转债 begins in 2014-08, so on a ten-year board it is absent from the first five
/// years, and a zero placed under it instead would have ranked it above every bond that was ever
/// down.
/// </summary>
public static class BondRace
{
    private const string Period = "month";

    /// <summary>
    /// More months than the endpoint will answer in one request carries: it returns what it has,
    /// which for these codes is everything back to 2003.
    /// </summary>
    private const int MonthsWanted = 430;

    /// <summary>Less than a year of months and a long run is a sprint.</summary>
    public const int FewestMonths = 12;

    /// <summary>
    /// The first whole month inside a window that starts mid-month.
    ///
    /// The source answers this period in whole months and labels each one with its **last day**:
    /// asked for a window from the 3rd it still answers the month containing the 3rd, and that
    /// row's close is the month's close — a month that began before the window did. Measuring a
    /// row from it is measuring from a date nobody chose: "近十年" from 2026-10-03 opened on
    /// 2016-10-31, which is a month early, and every row then came out low by whatever that month
    /// did. On the convertible indices — the volatile ones, and the ones at the top of this board
    /// — that was 1.9 to 2.4 points: 深证转债 read +63.04% where the ten years to 2026-09-30 were
    /// +65.48%. The asset race copied the same arithmetic, so this is shared ground, not a quirk
    /// of bonds; both loaders ask this method.
    ///
    /// A whole month is the smallest interval the source can be held to, so the partial one is
    /// dropped rather than propped up: the board begins on the first month that lies wholly
    /// inside the window. The cost is one month of the range, paid on every row equally and on a
    /// date the header then names correctly.
    /// </summary>
    public static DateOnly FirstWholeMonth(DateOnly start) =>
        start.Day == 1 ? start : new DateOnly(start.Year, start.Month, 1).AddMonths(1);

    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> bonds,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        // Both ends snapped to whole months before the source is asked anything, so the range the
        // rows are clipped to is the range the header names.
        start = FirstWholeMonth(start);
        end = MonthEnd(end.Year, end.Month);

        if (start > end)
        {
            throw new InvalidOperationException(Strings.Get("AssetRaceTooFew"));
        }

        var perBond = new List<Dictionary<DateOnly, double>>(bonds.Count);

        for (var i = 0; i < bonds.Count; i++)
        {
            var entry = bonds[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})",
                InstrumentNames.Display(entry.Code, entry.Name), i + 1, bonds.Count));

            // Raw, not adjusted: see the class note. Every row is an index, so the adjustment
            // this call would otherwise ask for does not exist in the answer — it would only
            // change which series the endpoint picks, per code, and a board whose rows are
            // rebased differently is a board about the rebasing.
            var bars = await kline.RawBarsAsync(
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

            perBond.Add(byMonth);
        }

        // Union, not intersection: 深证转债 starts in 2014 and a board that waited for every row
        // to be present would begin five years late rather than let one row join late.
        var dates = perBond
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

        for (var k = 0; k < bonds.Count; k++)
        {
            var row = new double[dates.Length];

            // Its own first quoted month inside the range.
            var own = -1;

            for (var i = 0; i < dates.Length && own < 0; i++)
            {
                if (perBond[k].ContainsKey(dates[i]))
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

            var @base = perBond[k][dates[own]];

            for (var i = own; i < dates.Length; i++)
            {
                if (perBond[k].TryGetValue(dates[i], out var close) && close > 0)
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
        // names, and `INST*` is how a frame drawn on an English interface still reads
        // "CSI Convertible Bond".
        var entries = bonds
            .Select(e => new RaceEntry(e.Code, InstrumentNames.Display(e.Code, e.Name)))
            .ToArray();

        // The amount slot carries the same numbers. This board is drawn on the return metric and
        // nothing here reads the other one — an index's accumulated turnover would mean nothing
        // beside a percentage — but the series type is built for two measures off one fetch, and
        // an array of zeros would be a claim that one exists.
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
