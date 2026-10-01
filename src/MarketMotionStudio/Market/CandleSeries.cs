using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>How much market time one candle covers.</summary>
public enum CandlePeriod
{
    Daily = 0,
    Weekly = 1,
    Monthly = 2,
}

/// <summary>
/// How the same four prices are drawn.
///
/// All four read the same bars, so switching between them re-fetches nothing: it
/// is a choice about the picture, not about the data.
/// </summary>
public enum CandleStyle
{
    /// <summary>The body between open and close, with the wick through it.</summary>
    Candles = 0,

    /// <summary>Open and close as ticks either side of the high-low line.</summary>
    Bars = 1,

    /// <summary>Closes only, joined.</summary>
    Line = 2,

    /// <summary>Closes only, filled down to the axis.</summary>
    Area = 3,
}

/// <summary>
/// How the animation gets through the series.
///
/// The two answer different questions about the same range. Growing asks "what did
/// the whole stretch look like" and ends on the finished chart; scrolling asks
/// "what did it look like at the time" and never shows more than a window of it,
/// trading the long view for the detail of one candle.
/// </summary>
public enum CandleMotion
{
    Grow = 0,
    Scroll = 1,
}

/// <summary>
/// One span offered for one period, as a number of months back from today.
/// </summary>
/// <param name="Months">How far back; zero is as far as the source has.</param>
/// <param name="Key">Resource key naming the span.</param>
public sealed record CandleRange(int Months, string Key);

/// <summary>
/// One instrument's candles, and the figures a chart of them is read for.
/// </summary>
/// <param name="Code">The full code, `sh600519` style.</param>
/// <param name="Name">The instrument's name, for the title and the file name.</param>
/// <param name="Period">What one candle covers.</param>
/// <param name="Bars">The candles, oldest first, on the venue's adjusted series.</param>
public sealed record CandleSeries(
    string Code, string Name, CandlePeriod Period, IReadOnlyList<TencentKline.CandleBar> Bars)
{
    public int Count => Bars.Count;

    public DateOnly Start => Bars[0].Date;

    public DateOnly End => Bars[^1].Date;

    /// <summary>The highest price touched, not the highest close: it is the top of the chart.</summary>
    public double High { get; } = Bars.Count > 0 ? Bars.Max(b => b.High) : 0;

    public double Low { get; } = Bars.Count > 0 ? Bars.Min(b => b.Low) : 0;

    /// <summary>Where the range opens — the first bar's open, which is what a range return is measured from.</summary>
    public double Opening { get; } = Bars.Count > 0 ? Bars[0].Open : 0;

    public double Closing { get; } = Bars.Count > 0 ? Bars[^1].Close : 0;

    /// <summary>The range's return: the last close over the first open.</summary>
    public double RangeReturn { get; } =
        Bars.Count > 0 && Bars[0].Open > 0 ? ((Bars[^1].Close / Bars[0].Open) - 1) * 100 : 0;

    /// <summary>
    /// How far the price travelled, high over low, as a percentage of the low.
    ///
    /// Deliberately not the largest single candle's range: "the range was this
    /// wide" and "one day moved this much" are different facts, and the first is
    /// what a chart's vertical extent already shows.
    /// </summary>
    public double Amplitude { get; } =
        Bars.Count > 0 && Bars.Min(b => b.Low) > 0 ? ((Bars.Max(b => b.High) / Bars.Min(b => b.Low)) - 1) * 100 : 0;

    public int UpBars { get; } = Bars.Count(b => b.Close >= b.Open);

    public int DownBars { get; } = Bars.Count(b => b.Close < b.Open);

    public double VolumePeak { get; } = Bars.Count > 0 ? Bars.Max(b => b.Volume) : 0;

    /// <summary>
    /// The moving average over <paramref name="length"/> candles, aligned with the
    /// bars: an entry is null until there are enough closes behind it.
    ///
    /// Aligned rather than trimmed, so a renderer asks for index <c>i</c> of the
    /// average and gets the one belonging to bar <c>i</c>; an average that started
    /// at its first full window would have to be offset at every use, and the
    /// offset is the sort of thing that is right in one place and wrong in another.
    /// </summary>
    public double?[] Average(int length)
    {
        var averages = new double?[Bars.Count];
        var sum = 0.0;

        for (var i = 0; i < Bars.Count; i++)
        {
            sum += Bars[i].Close;

            if (i >= length)
            {
                sum -= Bars[i - length].Close;
            }

            if (i >= length - 1)
            {
                averages[i] = sum / length;
            }
        }

        return averages;
    }
}

/// <summary>
/// The periods, the spans each offers, and the loading.
///
/// A period's spans are its own because the reach of one request is counted in
/// candles and the length of a range is counted in months: a daily chart three
/// years long is seven hundred candles, a monthly one is thirty-six, and offering
/// "ten years" on the daily period would be offering a chart of two and a half
/// thousand bars in a frame nine hundred pixels wide — a barcode no one can read,
/// fetched six requests at a time.
/// </summary>
public static class CandleLoader
{
    /// <summary>The block name a period is asked for by, which is what the endpoint calls it.</summary>
    public static string Slug(CandlePeriod period) => period switch
    {
        CandlePeriod.Weekly => "week",
        CandlePeriod.Monthly => "month",
        _ => "day",
    };

    /// <summary>Resource key for a period's name, as the interface and the frame both say it.</summary>
    public static string NameKey(CandlePeriod period) => period switch
    {
        CandlePeriod.Weekly => "CandlePeriodWeekly",
        CandlePeriod.Monthly => "CandlePeriodMonthly",
        _ => "CandlePeriodDaily",
    };

    /// <summary>
    /// The spans the daily period offers: up to three years, which is as far as a
    /// candle stays wide enough to see.
    /// </summary>
    public static readonly CandleRange[] DailyRanges =
    [
        new(3, "StudioRange3M"),
        new(6, "StudioRange6M"),
        new(12, "StudioRange12M"),
        new(36, "DcaRange3Y"),
    ];

    public static readonly CandleRange[] WeeklyRanges =
    [
        new(12, "StudioRange12M"),
        new(36, "DcaRange3Y"),
        new(60, "DcaRange5Y"),
        new(120, "DcaRange10Y"),
    ];

    public static readonly CandleRange[] MonthlyRanges =
    [
        new(36, "DcaRange3Y"),
        new(60, "DcaRange5Y"),
        new(120, "DcaRange10Y"),
        new(0, "DcaRangeMax"),
    ];

    public static CandleRange[] Ranges(CandlePeriod period) => period switch
    {
        CandlePeriod.Weekly => WeeklyRanges,
        CandlePeriod.Monthly => MonthlyRanges,
        _ => DailyRanges,
    };

    /// <summary>
    /// How many candles a span comes to, for the period it is being asked on.
    ///
    /// An estimate, and used as a ceiling rather than as an instruction: it says
    /// how many of the candles the source returns to keep. Asking for the trading
    /// days in a month would be counting weekends, so the count is what is aimed
    /// at and the calendar span is only what the request is clipped to.
    /// </summary>
    private static int Wanted(CandlePeriod period, int months) => period switch
    {
        // Weeks and months are counted directly: twelve months of monthly candles
        // is twelve of them, and dividing by twelve here is the sort of slip that
        // shows as a chart with ten candles where a decade was asked for.
        CandlePeriod.Weekly => (int)Math.Round(months * (52.0 / 12)),
        CandlePeriod.Monthly => months,
        _ => (int)Math.Round(months * (252.0 / 12)),
    };

    /// <summary>How many times the walk asks before it takes what it has.</summary>
    private const int MostRequests = 6;

    /// <summary>
    /// The most candles one walk can hold: the request limit times the number of
    /// requests it makes. A span longer than this is refused rather than quietly
    /// trimmed — the walk keeps the newest candles and drops the oldest in silence,
    /// and a chart beginning two years after the start date someone typed is a wrong
    /// answer that looks like a right one.
    /// </summary>
    public const int MostCandles = MostRequests * TencentKline.MostBarsPerRequest;

    /// <summary>
    /// The span tag meaning "the two dates in the pickers" rather than a count of
    /// months back from today. Not zero, which already means "as far back as the
    /// source has" on the monthly period.
    /// </summary>
    public const int CustomMonths = -1;

    /// <summary>
    /// Gathers one instrument's candles for a period and a span counted back from
    /// today.
    ///
    /// Walked backwards rather than asked for in one go, because a request carries
    /// at most <see cref="TencentKline.MostBarsPerRequest"/> candles and answers
    /// from the end date backwards: three years of daily bars is two requests, and
    /// asking for all of them at once returns the most recent six hundred and
    /// calls it three years.
    /// </summary>
    public static Task<CandleSeries> LoadAsync(
        TencentKline kline, string code, string name, CandlePeriod period, int months,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var today = DateOnly.FromDateTime(DateTime.Now);

        return WalkAsync(
            kline, code, name, period,
            months > 0 ? today.AddMonths(-months) : today.AddYears(-40),
            today,
            months > 0 ? Wanted(period, months) : 0,
            progress, cancellation);
    }

    /// <summary>
    /// The same, for a span given as two dates.
    ///
    /// The dates are honoured as dates rather than turned back into a count of months
    /// from today: a range ending last March is a question about last March, and a month
    /// count answers about a different stretch of the calendar that happens to be the
    /// same length.
    /// </summary>
    public static Task<CandleSeries> LoadAsync(
        TencentKline kline, string code, string name, CandlePeriod period,
        DateOnly from, DateOnly to, IProgress<string> progress, CancellationToken cancellation) =>
        WalkAsync(kline, code, name, period, from, to, WantedFor(period, from, to), progress, cancellation);

    /// <summary>
    /// How many candles a span between two dates comes to.
    ///
    /// An estimate used the way <see cref="Wanted"/> is — a ceiling to stop at rather
    /// than a count to go and collect. Weeks and months are counted in their own units
    /// because a month is not thirty days and a fifth week is not a sixth of a month.
    /// </summary>
    public static int WantedFor(CandlePeriod period, DateOnly from, DateOnly to)
    {
        var days = Math.Max(0, to.DayNumber - from.DayNumber);

        return period switch
        {
            CandlePeriod.Weekly => Math.Max(1, (int)Math.Round(days / 7.0)),
            CandlePeriod.Monthly => Math.Max(1, ((to.Year - from.Year) * 12) + to.Month - from.Month + 1),
            _ => Math.Max(1, (int)Math.Round(days * (252.0 / 365))),
        };
    }

    /// <summary>
    /// The walk both entry points end up in: a range, a ceiling on how many candles to
    /// keep, and no opinion about where the range came from.
    ///
    /// `end` is where the asking starts and is not necessarily today — a custom span may
    /// end years ago, and starting from today would spend its requests on candles the
    /// caller did not ask for.
    /// </summary>
    private static async Task<CandleSeries> WalkAsync(
        TencentKline kline, string code, string name, CandlePeriod period,
        DateOnly start, DateOnly end, int wanted,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var slug = Slug(period);

        // A few over what is wanted, so a span that is one candle short of its
        // estimate does not come back a candle short of the chart.
        var perRequest = Math.Clamp(wanted > 0 ? wanted + 8 : TencentKline.MostBarsPerRequest,
            5, TencentKline.MostBarsPerRequest);

        var held = new SortedDictionary<DateOnly, TencentKline.CandleBar>();
        var cursor = end;
        var earliestSeen = end;

        // Declared outside the loop so that, when it ends, `request` still says how far it
        // got: a break leaves it short of the limit, running to the end leaves it equal.
        // That difference is the whole distinction between "there is nothing earlier" and
        // "this walk was not given enough requests to reach the start".
        var request = 0;

        for (; request < MostRequests; request++)
        {
            progress.Report($"{name}: {held.Count} …");

            if (wanted > 0 && held.Count >= wanted)
            {
                break;
            }

            var page = await kline.CandleBarsAsync(code, slug, start, cursor, perRequest, cancellation);

            if (page.Count == 0)
            {
                break;
            }

            foreach (var bar in page)
            {
                held[bar.Date] = bar;
            }

            var earliest = page[0].Date;

            // Nothing earlier arrived: either the span is covered or the listing's
            // history starts here, which the source does not distinguish and the
            // walk does not need to.
            if (earliest >= earliestSeen || earliest <= start)
            {
                break;
            }

            earliestSeen = earliest;
            cursor = earliest.AddDays(-1);

            // The whole window would sit before the range's own start, so nothing it
            // could answer belongs in the chart. Asking anyway is not free: the walk
            // reaches exactly this state on its last pass, and the request it makes is
            // the degenerate one the US venues cannot tell from a ticker that does not
            // exist.
            if (cursor < start)
            {
                break;
            }
        }

        var ordered = held.Values.ToList();

        // The requests ran out before the walk reached the start of the span it was given,
        // so what it holds is the newest candles alone: a chart that begins years after the
        // date someone typed, and looks like a chart of the whole span. There is no honest
        // way to return that. The two cases that must not land here are the open-ended span,
        // which states no start to fall short of, and a listing whose history begins inside
        // the span — both of those stop the walk by breaking, which leaves `request` below
        // the limit.
        if (request >= MostRequests && wanted > 0 && ordered.Count > 0 && ordered[0].Date > start)
        {
            throw new InvalidOperationException(Localization.Strings.Format(
                "CandleRangeTooLong",
                Localization.Strings.Get(NameKey(period)),
                MostCandles));
        }

        if (wanted > 0 && ordered.Count > wanted)
        {
            ordered = ordered.Skip(ordered.Count - wanted).ToList();
        }

        if (ordered.Count < 3)
        {
            throw new InvalidOperationException(Localization.Strings.Get("TurnoverTooFewDays"));
        }

        return new CandleSeries(code, name, period, ordered);
    }

    /// <summary>A price, with the decimals its size asks for rather than a fixed two.</summary>
    public static string Price(double value)
    {
        var decimals = Math.Abs(value) >= 1000 ? 0 : Math.Abs(value) >= 10 ? 2 : 3;

        return value.ToString("N" + decimals.ToString(CultureInfo.InvariantCulture),
            CultureInfo.InvariantCulture);
    }

    /// <summary>A price in the shortest form that still says which price it is, for an axis.</summary>
    public static string Axis(double value)
    {
        var decimals = Math.Abs(value) >= 1000 ? 0 : Math.Abs(value) >= 100 ? 1 : 2;

        return value.ToString("N" + decimals.ToString(CultureInfo.InvariantCulture),
            CultureInfo.InvariantCulture);
    }

    /// <summary>A date on the axis: the day itself daily, the month otherwise.</summary>
    public static string Label(DateOnly day, CandlePeriod period) =>
        period is CandlePeriod.Daily
            ? day.ToString("MM-dd", CultureInfo.InvariantCulture)
            : day.ToString("yyyy-MM", CultureInfo.InvariantCulture);

    /// <summary>A date the same way in every locale, for the header and for file names.</summary>
    public static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
}
