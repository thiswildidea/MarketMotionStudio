using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>One entry in a race: a sector index or a single stock.</summary>
/// <param name="Code">The full code, `sh000928` style.</param>
/// <param name="Name">The display name — what the row's left gutter shows.</param>
public sealed record RaceEntry(string Code, string Name);

/// <summary>
/// The four rosters a race can be run on, and the load that turns a roster into a series.
///
/// The two built-in lists' codes were each verified against the quote endpoint by the source
/// tool — an unquotable code in a built-in list is a defect nobody who hits fetch can work
/// around, so this is one place the codes are carried as tested literals rather than derived.
/// </summary>
public static class SectorLists
{
    public const int Fewest = 3;

    /// <summary>More than this and a vertical frame is a barcode, not a race.</summary>
    public const int Most = 16;

    /// <summary>CSI Level-1 industries: mutually exclusive, collectively exhaustive, and ten.</summary>
    public static readonly RaceEntry[] Level1 =
    [
        new("sh000928", "能源"),
        new("sh000929", "材料"),
        new("sh000930", "工业"),
        new("sh000931", "可选消费"),
        new("sh000932", "主要消费"),
        new("sh000933", "医药卫生"),
        new("sh000934", "金融"),
        new("sh000935", "信息技术"),
        new("sh000936", "通信"),
        new("sh000937", "公用事业"),
    ];

    /// <summary>Recognisable themes: the ones people argue about.</summary>
    public static readonly RaceEntry[] Themes =
    [
        new("sz399997", "白酒"),
        new("sz399975", "证券"),
        new("sz399986", "银行"),
        new("sz399989", "医疗"),
        new("sz399967", "军工"),
        new("sz399971", "传媒"),
        new("sz399808", "新能源"),
        new("sz399976", "新能源车"),
        new("sh000827", "环保"),
        new("sh000922", "红利"),
        new("sz399998", "煤炭"),
        new("sh000819", "有色金属"),
        new("sz399995", "基建"),
        new("sh000949", "农业"),
        new("sz399996", "智能家居"),
    ];

    /// <summary>The custom picker's candidate pool: both lists, deduplicated, in order.</summary>
    public static IReadOnlyList<RaceEntry> Union()
    {
        var seen = new HashSet<string>();
        var outList = new List<RaceEntry>();

        foreach (var entry in Level1.Concat(Themes))
        {
            if (seen.Add(entry.Code))
            {
                outList.Add(entry);
            }
        }

        return outList;
    }
}

/// <summary>Which of the two measures a race is run on.</summary>
public enum RaceMetric
{
    /// <summary>Cumulative percentage change from the range's first day. Zero axis centred, red up green down.</summary>
    Return,

    /// <summary>Cumulative turnover in 亿元 — monotonic, the story is where the money went.</summary>
    Amount,
}

/// <summary>
/// One fetched race: every entrant's two measures over the days all of them share.
///
/// Two measures out of one fetch because they come from the same bars, and switching the
/// metric must be a redraw rather than a re-fetch — the numbers are already here.
/// </summary>
/// <param name="Entries">The racers, in roster order.</param>
/// <param name="Dates">Trading days every entrant has, ascending.</param>
/// <param name="Returns">Per entrant, cumulative change in per cent from the first day.</param>
/// <param name="Amounts">Per entrant, turnover in 亿元 accumulated day by day.</param>
public sealed record SectorRaceSeries(
    IReadOnlyList<RaceEntry> Entries,
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<double[]> Returns,
    IReadOnlyList<double[]> Amounts)
{
    public int Days => Dates.Count;

    public int Racers => Entries.Count;

    public double[] Values(RaceMetric metric) => [.. (metric is RaceMetric.Return ? Returns : Amounts).SelectMany(v => v[^1..])];

    /// <summary>Final standings, best first — what the closing champion glow picks its winner from.</summary>
    public (int Index, double Value)[] Standings(RaceMetric metric)
    {
        var finals = metric is RaceMetric.Return ? Returns : Amounts;

        return [.. Enumerable.Range(0, Racers)
            .Select(k => (Index: k, Value: finals[k][^1]))
            .OrderByDescending(s => s.Value)];
    }
}

/// <summary>Loads a race from the daily-bars endpoint, one entrant at a time.</summary>
public static class SectorSeries
{
    /// <summary>
    /// Fetches each entrant's bars and builds both measures over the days they all share.
    ///
    /// Serial on purpose — the source tool serialised to be gentle on the endpoint, and a dozen
    /// parallel requests to somebody else's public API is the behaviour of a scraper. Two of the
    /// source's cleaning rules ride along unchanged: an unsettled current day is dropped (its bar
    /// holds only the opening auction), and a day any entrant lacks is dropped from everyone
    /// (one missing bar would make that frame's ranking jump for no visible reason).
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        MarketProfile market,
        IReadOnlyList<RaceEntry> entries,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        // The amount field's unit belongs to the venue, not to the endpoint: ten
        // thousand of it is one 亿 in Shanghai, Shenzhen and Hong Kong, and a hundred
        // million of it is one 亿 in New York, where the field is plain dollars.
        // Dividing by the wrong one is a figure out by a factor no axis label would
        // make visible.
        var toYi = market.AmountToYi;
        var perEntry = new List<(RaceEntry Entry, Dictionary<DateOnly, (double Close, double AmountYi)> Bars)>();

        for (var i = 0; i < entries.Count; i++)
        {
            var entry = entries[i];
            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})", entry.Name, i + 1, entries.Count));

            var bars = await kline.StockBarsAsync(entry.Code, start, end, cancellation);

            perEntry.Add((entry, bars.ToDictionary(
                b => b.Date,
                b => (b.Close, b.AmountWan / toYi))));
        }

        // The days every entrant has. One missing day is one jump in the standings.
        var shared = new HashSet<DateOnly>(perEntry[0].Bars.Keys);

        foreach (var (_, bars) in perEntry.Skip(1))
        {
            shared.IntersectWith(bars.Keys);
        }

        var dates = shared.OrderBy(d => d).ToArray();

        if (dates.Length < 5)
        {
            throw new InvalidOperationException(Strings.Get("SectorTooFewSharedDays"));
        }

        var returns = new List<double[]>();
        var amounts = new List<double[]>();

        foreach (var (_, bars) in perEntry)
        {
            // The return's base is the first *shared* day's close, so every racer starts at
            // exactly zero on the day the chart calls day one.
            var @base = bars[dates[0]].Close;
            var acc = 0.0;

            var ret = new double[dates.Length];
            var amt = new double[dates.Length];

            for (var i = 0; i < dates.Length; i++)
            {
                var bar = bars[dates[i]];

                ret[i] = (bar.Close / @base - 1) * 100;
                acc += bar.AmountYi;
                amt[i] = acc;
            }

            returns.Add(ret);
            amounts.Add(amt);
        }

        return new SectorRaceSeries(
            [.. perEntry.Select(p => p.Entry)], dates, returns, amounts);
    }
}
