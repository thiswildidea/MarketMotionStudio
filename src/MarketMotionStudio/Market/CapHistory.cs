namespace MarketMotionStudio.Market;

/// <summary>
/// One trading day of a circulating-value history.
/// </summary>
/// <param name="Cap">Circulating market value, in 亿 of the venue's own currency.</param>
/// <param name="Price">
/// The price that value was taken at. On an A-share this is the day's unadjusted
/// close; on Hong Kong it is the day's average traded price — see
/// <see cref="CapHistory"/> for why that market cannot have a close here.
/// </param>
public sealed record CapDay(DateOnly Date, double Cap, double Price);

/// <summary>
/// One instrument's circulating market value over a range, with the price it was
/// taken at beside it.
///
/// Held as two parallel figures rather than as a value alone because the question
/// this series exists to answer is about the two of them *together*: a price that
/// sets a new high while the value does not is a company that issued shares in
/// between, and one whose value outgrows its price bought some back. Either reading
/// needs both lines on one axis, and neither can be derived from the other.
/// </summary>
public sealed record CapSeries(
    string Code,
    string Name,
    string CurrencyKey,
    bool PriceIsAverage,
    CapDay[] Days);

/// <summary>
/// One instrument's two figures, laid along the board's own date axis.
///
/// The arrays are as long as the board's axis and only <see cref="First"/>..<see cref="Last"/>
/// are ever read: an instrument that listed after the range began has no value before
/// its own first day, and drawing one there would be a plunge the company never made.
///
/// Days the instrument itself did not trade — a suspension, or a holiday one venue
/// kept and another did not — carry the last figure forward, filled in when the board
/// is built. A company is still worth what it was worth on a day its shares rested,
/// and a line with holes in it reads as missing data rather than as a quiet day.
///
/// A class rather than a record because every aggregate below is computed once, in
/// the constructor. The frame asks for the peak, the trough, their indices and the
/// mean again on every one of sixty frames a second, and over ten years of days that
/// is the same few thousand comparisons sixty times over for figures that cannot have
/// moved since they were written.
/// </summary>
public sealed class CapTrack
{
    public CapTrack(
        string code,
        string name,
        IReadOnlyList<double> cap,
        IReadOnlyList<double> price,
        int first,
        int last)
    {
        Code = code;
        Name = name;
        Cap = cap;
        Price = price;
        First = first;
        Last = last;

        var capTop = cap[first];
        var capBottom = cap[first];
        var priceTop = price[first];
        var priceBottom = price[first];
        var capSum = 0.0;
        var priceSum = 0.0;

        CapPeakAt = first;
        CapTroughAt = first;
        PricePeakAt = first;
        PriceTroughAt = first;

        for (var i = first; i <= last; i++)
        {
            if (cap[i] > capTop)
            {
                capTop = cap[i];
                CapPeakAt = i;
            }

            if (cap[i] < capBottom)
            {
                capBottom = cap[i];
                CapTroughAt = i;
            }

            if (price[i] > priceTop)
            {
                priceTop = price[i];
                PricePeakAt = i;
            }

            if (price[i] < priceBottom)
            {
                priceBottom = price[i];
                PriceTroughAt = i;
            }

            capSum += cap[i];
            priceSum += price[i];
        }

        CapPeak = capTop;
        CapTrough = capBottom;
        PricePeak = priceTop;
        PriceTrough = priceBottom;

        var held = last - first + 1;

        MeanCap = capSum / held;
        MeanPrice = priceSum / held;
    }

    public string Code { get; }

    public string Name { get; }

    /// <summary>The company's value on each day of the board's axis, in 亿.</summary>
    public IReadOnlyList<double> Cap { get; }

    /// <summary>The price that value was taken at, on each day of the board's axis.</summary>
    public IReadOnlyList<double> Price { get; }

    /// <summary>The first axis position this instrument has a figure for.</summary>
    public int First { get; }

    /// <summary>The last axis position this instrument has a figure for.</summary>
    public int Last { get; }

    public double CapPeak { get; }

    public double CapTrough { get; }

    public double PricePeak { get; }

    public double PriceTrough { get; }

    public int CapPeakAt { get; }

    public int CapTroughAt { get; }

    public int PricePeakAt { get; }

    public int PriceTroughAt { get; }

    public double MeanCap { get; }

    public double MeanPrice { get; }

    /// <summary>The value now: this series' own last day rather than a fresh quote.</summary>
    public double FinalCap => Cap[Last];

    /// <summary>How many of the board's days this instrument covers.</summary>
    public int Covered => Last - First + 1;
}

/// <summary>
/// One or more instruments' circulating value over the same span, on one date axis.
///
/// **The axis is the union of the days they have**, as it is on the holdings board and
/// for the same reason. The alternative — the days they all have — would cut a
/// comparison down to the youngest listing's stretch, and the frame would look
/// entirely plausible while answering a shorter question than the one that was asked.
/// Each track simply begins where its own history does.
///
/// Several instruments share this page's currency because the page only offers the
/// market in force, which is also why its picker is filtered to that market. Comparing
/// across venues would put figures in 元, HK$ and USD on one axis, which no rescale
/// makes honest.
/// </summary>
/// <param name="Skipped">
/// Instruments the source could not carry a value for at all. Reported rather than
/// drawn flat along the bottom: an index has no turnover rate, and neither does
/// anything the source quotes without one — which has nothing to do with how the
/// company did.
/// </param>
public sealed record CapBoard(
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<CapTrack> Tracks,
    string CurrencyKey,
    bool PriceIsAverage,
    IReadOnlyList<string> Skipped)
{
    public int Count => Dates.Count;

    public DateOnly Start => Dates[0];

    public DateOnly End => Dates[^1];

    /// <summary>Whether the frame compares several instruments rather than telling one apart.</summary>
    public bool Comparing => Tracks.Count > 1;

    /// <summary>The tallest value any line reaches, for the axis.</summary>
    public double CapPeak => Tracks.Max(t => t.CapPeak);

    /// <summary>The tallest price any line reaches, for the axis.</summary>
    public double PricePeak => Tracks.Max(t => t.PricePeak);

    /// <summary>The trough of them all, which is what decides how much of the panel the
    /// earliest years get.</summary>
    public double CapTrough => Tracks.Min(t => t.CapTrough);
}

/// <summary>
/// Walks the kline endpoint backwards to gather years of daily circulating market
/// value for one instrument.
///
/// The value is not a field the source carries anywhere — it is a product, and both
/// of its factors have to be recovered from the row:
///
///     circulating shares = volume / turnover rate
///     value              = price × circulating shares
///
/// The turnover rate is <c>volume / shares</c>, which is why the first line works.
/// It is the only historical share count this source will give up: there is no
/// per-day capitalisation field on any endpoint, and the total share count's history
/// is not served either. What is recovered is therefore the *circulating* count
/// (流通股本), never the total — which the page has to say, because on an issuer with
/// a large restricted portion the two are not close.
///
/// Two things about that first line are measured, not assumed:
///
/// - The rate arrives with two decimals, so one day's share count carries roughly a
///   percent of noise. The count is a step function — it moves on an issuance or a
///   buyback and is flat between — so the noise is taken out with a centred median
///   rather than a trailing one: a centred window places a step on the day it
///   happened, while a trailing one slides the whole staircase half a window late.
///   Measured on 京东方A, whose count went 115.9 → 233 → 338 → 372 → 362 亿股 across
///   four placements and a cancellation, every step lands on the year it belongs to.
/// - The volume field's unit differs by venue: lots on the mainland, shares in Hong
///   Kong. Taken from the same branch as the price below, since the two are one
///   question about one row.
///
/// What is *not* done is the obvious shortcut — today's value scaled by the ratio of
/// two adjusted closes. An adjustment factor is not a share-count multiple: it also
/// carries cash dividends, and on 贵州茅台 it is 7.06 where the share count grew
/// 5.02-fold. Scaling by it put that company's 2016 value at −791 亿, a figure that
/// would have drawn as a curve climbing out of negative territory.
/// </summary>
internal static class CapHistory
{
    /// <summary>
    /// Requests beyond this are not made. Twenty pages is about twelve years of
    /// trading days; the walk stops on its own when a page brings nothing earlier,
    /// and this is the backstop that keeps a pathological response from looping.
    /// </summary>
    private const int MostRequests = 20;

    /// <summary>
    /// The furthest back one walk can reach, in calendar days. Pages bound their
    /// date pickers by this rather than by a number picked for how it sounds: past
    /// it the walk runs out of requests before it runs out of range, and the series
    /// starts later than the date that was asked for.
    /// </summary>
    public const int MostDays = MostRequests * TencentKline.MostBarsPerRequest;

    /// <summary>
    /// How many days' share counts one median is taken over.
    ///
    /// Twenty keeps a step's own day at the window's centre. Wider and a placement
    /// smears across a month; narrower and the two-decimal rate shows through as
    /// day-to-day jitter on a figure that is in truth flat.
    /// </summary>
    private const int MedianSpan = 20;

    /// <summary>
    /// Fewer days than this and the series is not offered at all.
    ///
    /// A handful of days is enough to compute a value and not enough to draw a
    /// history, and the failure that matters is the quiet one: an instrument whose
    /// turnover field is missing or zero yields very few usable rows, and a board
    /// built from them would draw a confident line across a range it never measured.
    /// </summary>
    private const int FewestDays = 20;

    /// <summary>
    /// Whether this market's rows can carry a value history at all.
    ///
    /// All three. New York was left out at first over the precision of its turnover
    /// rate, and that reading was wrong. Measured on 2026-10-07: sixty-day rolling
    /// medians of the recovered share count move 0.01–0.03% a day, which is the order
    /// of the mainland's 0.03% and Hong Kong's 0.03%, and the general endpoint walks a
    /// US code back to 2009 — the depth it gives a mainland one.
    ///
    /// What does differ is what the rate is a fraction *of*. On the mainland and in
    /// Hong Kong it is shares in circulation; in New York it is every share the company
    /// has, insiders' included, so the line there is a total value rather than a
    /// circulating one. Against the snapshot's own circulating figure the recovered
    /// count runs high by each company's insider stake — 0.0% at Apple, 4.1% at NVIDIA,
    /// 9.4% at Amazon, 11.7% at Tesla, which is the order those stakes are held in.
    /// </summary>
    public static bool Serves(MarketId market) =>
        market is MarketId.AShare or MarketId.HongKong or MarketId.UnitedStates;

    /// <summary>
    /// Whether one code's volume field counts shares rather than lots.
    ///
    /// Not a property of the venue prefix: the STAR market quotes in shares while the
    /// rest of the mainland quotes in lots, and a prefix guess would be wrong on
    /// exactly the listings nobody would think to check. The test is the one
    /// <c>StockSeries</c> already applies — does <c>volume × price</c> come to the
    /// amount? Where the volume is lots the product is short by a factor of a hundred,
    /// so the ratio's median sits near one hundred or near one, and the two are a
    /// hundredfold apart, which is not a threshold anyone has to tune.
    ///
    /// Hong Kong is not asked, because the ratio cannot be formed there: its price
    /// arrives rebased, which moves the ratio by whatever the adjustment factor is and
    /// could in principle carry it across the threshold. Its volume is counted in
    /// shares, measured on 腾讯控股 — 10,030,081 shares against HK$4,286,181,540 traded
    /// is HK$427.33, which is that day's price.
    ///
    /// Neither is New York, and for a second reason: the ratio cannot be formed there
    /// either, because its amount field is dollars where the mainland's is 万元. That
    /// is the same hundred the lot is made of, so the ratio reads a difference in
    /// units as a difference in counting and answers "lots" about a market that has
    /// none — which put every US value a hundredfold high. A US quote counts shares;
    /// there is no lot to decide between.
    /// </summary>
    private static bool CountsShares(IEnumerable<TencentKline.StockBar> bars, bool hongKong,
        bool unitedStates)
    {
        if (hongKong || unitedStates)
        {
            return true;
        }

        var ratios = bars
            .Where(b => b.RawVolume > 0 && b.Close > 0 && b.AmountWan > 0)
            .Select(b => (b.RawVolume * 100.0 * b.Close / 10_000.0) / b.AmountWan)
            .OrderBy(r => r)
            .ToArray();

        return ratios.Length > 0 && ratios[ratios.Length / 2] > 10;
    }

    /// <summary>
    /// The adjustment one code is asked for, and whether the price beside the value is
    /// a traded average rather than a close.
    ///
    /// An A-share is asked for with no adjustment at all, and that is the whole trick:
    /// the general endpoint answers an empty adjustment with its own <c>day</c> block,
    /// eleven fields wide, whose close is the price the stock actually traded at that
    /// day, unadjusted. Every adjusted block on the source rebases the price to
    /// something else and a value taken at a rebased price is not a value.
    ///
    /// Hong Kong has no such block — both of its adjusted blocks carry the same amount
    /// and volume but a rebased price, and an empty adjustment is not served there. So
    /// the price is the amount over the volume: the day's average traded price, which
    /// is the day's own money over the day's own shares and is unmoved by any
    /// adjustment. It is not the close, and the frame says so.
    /// </summary>
    private static (string Adjustment, bool PriceIsAverage) Basis(string code) =>
        code.StartsWith("hk") ? ("hfq", true) : ("", false);

    /// <summary>
    /// One instrument's value day by day, or null when the source cannot carry one.
    ///
    /// Internal because every caller wants a board: one instrument's series is put on
    /// an axis by <see cref="CapLoader"/>, even when there is only the one. Two ways to
    /// ask for a value history invite two answers that disagree about what the axis is.
    /// </summary>
    internal static async Task<CapSeries?> WalkAsync(
        TencentKline kline,
        string code,
        string display,
        DateOnly start,
        DateOnly end,
        MarketProfile market,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var hongKong = code.StartsWith("hk");
        var unitedStates = market.Id == MarketId.UnitedStates;
        var (adjustment, priceIsAverage) = Basis(code);

        var rows = new SortedList<DateOnly, TencentKline.StockBar>();
        var cursor = end;
        var earliestSeen = end;

        for (var request = 0; request < MostRequests; request++)
        {
            progress.Report($"{display}: {rows.Count} …");

            if (cursor < start)
            {
                break;
            }

            var bars = await kline.StockBarsAsync(
                code, start, cursor, cancellation, adjustment: adjustment, turnover: true);

            if (bars.Count == 0)
            {
                break;
            }

            foreach (var bar in bars)
            {
                // Rows the value cannot be taken from are dropped here rather than
                // carried: a day with no turnover figure yields no share count at all,
                // and treating that as a small count would draw a cliff in the middle
                // of a series that in truth never stopped to measure.
                if (bar.TurnoverRate > 0 && bar.RawVolume > 0)
                {
                    rows.TryAdd(bar.Date, bar);
                }
            }

            var earliest = bars[0].Date;

            if (earliest >= earliestSeen || earliest <= start)
            {
                break;
            }

            earliestSeen = earliest;
            cursor = earliest.AddDays(-1);
        }

        if (rows.Count < FewestDays)
        {
            return null;
        }

        var sharesPerVolume = CountsShares(rows.Values, hongKong, unitedStates) ? 1.0 : 100.0;
        var usable = new List<(DateOnly Date, double Shares, double Price)>();

        foreach (var (day, bar) in rows)
        {
            var price = hongKong ? bar.AmountWan * 10_000.0 / bar.RawVolume : bar.Close;

            if (price <= 0)
            {
                continue;
            }

            var shares = bar.RawVolume * sharesPerVolume / (bar.TurnoverRate / 100.0) / 1e8;

            if (shares > 0)
            {
                usable.Add((day, shares, price));
            }
        }

        if (usable.Count < FewestDays)
        {
            return null;
        }

        var counts = usable.Select(u => u.Shares).ToArray();
        var days = new CapDay[usable.Count];

        for (var i = 0; i < usable.Count; i++)
        {
            // The share count behind today's value is the median of its neighbours,
            // not today's own reading — see the note on MedianSpan. The price beside
            // it is today's, unsmoothed, because a price that moves is the point.
            var settled = Median(counts, i);

            days[i] = new CapDay(usable[i].Date, usable[i].Price * settled, usable[i].Price);
        }

        return new CapSeries(
            code,
            kline.LastName(code),
            market.CurrencyKey,
            priceIsAverage,
            days);
    }

    /// <summary>
    /// The median of a centred window, so that a step in the series is placed on the
    /// day it happened rather than half a window later.
    /// </summary>
    private static double Median(double[] values, int index)
    {
        var from = Math.Max(0, index - (MedianSpan / 2));
        var to = Math.Min(values.Length - 1, from + MedianSpan - 1);
        var window = new double[to - from + 1];

        for (var i = from; i <= to; i++)
        {
            window[i - from] = values[i];
        }

        Array.Sort(window);

        return window.Length % 2 == 1
            ? window[window.Length / 2]
            : (window[(window.Length / 2) - 1] + window[window.Length / 2]) / 2.0;
    }
}

/// <summary>
/// Builds one board from one or more instruments' value series, sharing a date axis.
///
/// Several instruments change nothing about how a value is recovered — the walk above
/// is the whole of that, and is walked once per instrument exactly as it always was.
/// What this adds is the comparison: the same question asked of several companies on
/// one axis, which is how it is actually asked. ("宁德时代 passed 中国石油 in 2021 —
/// when, and by how much?") The answer is readable only because the panel answers it
/// in one currency: the page offers the market in force and nothing else.
///
/// Each walk is answered one after another rather than in parallel. Concurrency here
/// would trade a fetch measured in seconds for one measured in fractions of them, at
/// the cost of asking the same endpoint for six streams at once — and a source that
/// answers that by throttling takes the slow path anyway, after making every other
/// page on the machine slow with it.
/// </summary>
public static class CapLoader
{
    /// <summary>
    /// The most companies one frame can carry.
    ///
    /// Six, which is what the holdings board arrived at for the same reason rather
    /// than by borrowing its number: six end-labels and six curves are still a
    /// comparison, and a dozen is a barcode wearing its own labels. Over it the page
    /// refuses rather than trims — a frame drawn from six of the nine companies
    /// somebody ticked answers about a list nobody chose, and looks entirely plausible
    /// while it does. Left independent of that page's constant so that changing one
    /// ceiling cannot quietly move the other.
    /// </summary>
    public const int MostTracks = 6;

    /// <summary>
    /// One board from one or more instruments, or null when nothing to draw came back.
    ///
    /// Null rather than an exception, and for the same reason the single walk returns
    /// null: "no value in this range" is an answer this page has words for — it is what
    /// an index does — not a fault in the page. Every instrument coming back empty is
    /// that answer; some coming back empty is not, and is reported in
    /// <see cref="CapBoard.Skipped"/> instead.
    /// </summary>
    public static async Task<CapBoard?> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        DateOnly start,
        DateOnly end,
        MarketProfile market,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        if (entries.Count == 0)
        {
            return null;
        }

        var walks = new List<CapSeries>(entries.Count);
        var skipped = new List<string>();

        foreach (var entry in entries)
        {
            var display = InstrumentNames.Display(entry.Code, entry.Name);

            var series = await CapHistory.WalkAsync(
                kline, entry.Code, display, start, end, market, progress, cancellation);

            // Nothing usable came back, which on this page has a particular and likely
            // cause: an index has no turnover rate at all, and neither does anything the
            // source quotes without one. Dropped from the frame but named — see the note
            // on `CapBoard.Skipped`.
            if (series is null)
            {
                skipped.Add(display);
                continue;
            }

            walks.Add(series);
        }

        if (walks.Count == 0)
        {
            return null;
        }

        // The union, walked in order — see the note on `CapBoard`.
        var union = new SortedSet<DateOnly>();

        foreach (var walk in walks)
        {
            foreach (var day in walk.Days)
            {
                union.Add(day.Date);
            }
        }

        var dates = union.ToArray();
        var at = new Dictionary<DateOnly, int>(dates.Length);

        for (var i = 0; i < dates.Length; i++)
        {
            at[dates[i]] = i;
        }

        var tracks = new List<CapTrack>(walks.Count);

        foreach (var walk in walks)
        {
            var first = at[walk.Days[0].Date];
            var last = at[walk.Days[^1].Date];

            var caps = new double[dates.Length];
            var prices = new double[dates.Length];
            var map = new Dictionary<DateOnly, CapDay>(walk.Days.Length);

            foreach (var day in walk.Days)
            {
                map[day.Date] = day;
            }

            // The last figure, carried across the days this instrument had none.
            var cap = 0d;
            var price = 0d;

            for (var i = first; i <= last; i++)
            {
                if (map.TryGetValue(dates[i], out var day))
                {
                    cap = day.Cap;
                    price = day.Price;
                }

                caps[i] = cap;
                prices[i] = price;
            }

            tracks.Add(new CapTrack(walk.Code, walk.Name, caps, prices, first, last));
        }

        // Every instrument on the frame is denominated the same way, because the page
        // offers one market; the first one to answer is as good a witness as any.
        var lead = walks[0];

        return new CapBoard(dates, tracks, lead.CurrencyKey, lead.PriceIsAverage, skipped);
    }
}
