using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>
/// A coin's candles, in the same shape the stock candle page draws.
///
/// The stock loader asks an endpoint for the period it wants — <c>week</c> and
/// <c>month</c> are blocks that endpoint serves alongside <c>day</c>. Neither crypto
/// source has that: Yahoo serves daily bars and CoinGecko serves daily closes, and
/// neither will aggregate. So the weekly and monthly candles are **made here, from the
/// daily ones**, which is not the same arithmetic as the stock page's and is worth
/// saying plainly: an aggregate of daily bars is exact for a coin in a way it would not
/// be for a share, because a coin has no holiday and no half-day — every day in the
/// span exists, so a week is its seven days' own high, low, opening and closing.
///
/// The candle is stamped with the first day of the span it covers rather than the last,
/// which is where a venue puts a weekly bar too: a chart that reads "the week of the
/// 4th" pointing at the 10th is a chart whose axis is a week out.
///
/// Volume is summed across the span, and only ever read as a height against the
/// tallest — see the note on <see cref="CryptoQuotes"/> about its unit.
/// </summary>
public static class CryptoCandleLoader
{
    /// <summary>
    /// How many days before the range are fetched so the range has a close to be
    /// measured from.
    ///
    /// A chart of a range is quoted against the level before it, which is the close of
    /// the last day outside it — and asking for the range alone loses that: the frame
    /// would measure the span against its own opening instead, which is a different
    /// number on the days it matters. Ten days is more than any gap a coin has, since
    /// it has none.
    /// </summary>
    private const int LookBehind = 10;

    /// <summary>The most coins one comparison frame can carry — the palette's own ceiling.</summary>
    public const int MostTracks = CandleBoardLoader.MostTracks;

    /// <summary>
    /// One coin's candles over a range, on the period asked for.
    ///
    /// An empty series is returned rather than thrown when the range holds no bars: a
    /// coin listed after the range began has nothing in it, and that is an answer the
    /// page puts in words. See <see cref="CandleSeries"/> for what a series makes of
    /// zero bars — every derived figure is zero, and the page says so instead of drawing
    /// a flat line at nothing.
    /// </summary>
    public static async Task<CandleSeries> LoadAsync(
        CryptoQuotes quotes,
        string code,
        string name,
        CandlePeriod period,
        DateOnly from,
        DateOnly to,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var asset = CryptoAsset.Of(code)
            ?? throw new ArgumentException($"Not a coin this app offers: {code}", nameof(code));

        // The look-behind is fetched and then dropped; see `LookBehind`.
        var bars = await quotes.BarsAsync(asset, from.AddDays(-LookBehind), to, progress, cancellation);

        var previous = 0d;
        var kept = new List<TencentKline.CandleBar>(bars.Count);

        foreach (var bar in bars)
        {
            if (bar.Date < from)
            {
                previous = bar.Close;
                continue;
            }

            kept.Add(bar);
        }

        return new CandleSeries(
            code, InstrumentNames.Display(code, name), period,
            period switch
            {
                CandlePeriod.Weekly => Aggregate(kept, byWeek: true),
                CandlePeriod.Monthly => Aggregate(kept, byWeek: false),
                _ => kept,
            },
            previous);
    }

    /// <summary>
    /// One coin's candles inside a single day, at one of the minute periods.
    ///
    /// Nothing is aggregated here, and that is the difference from the daily loader: the
    /// source answers the minute grain directly, so a week or a month made out of these
    /// would be a shape nobody asked for, and the page offers the minute periods as a
    /// different question rather than as a finer answer to the same one.
    ///
    /// An empty series is returned rather than thrown: a day the source no longer holds
    /// — further back than <see cref="CryptoQuotes.Minute1Days"/> on the finest grain —
    /// comes back with nothing in it, and the page puts that in words.
    /// </summary>
    public static async Task<CandleSeries> LoadIntradayAsync(
        CryptoQuotes quotes,
        string code,
        string name,
        CandlePeriod period,
        DateOnly day,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var asset = CryptoAsset.Of(code)
            ?? throw new ArgumentException($"Not a coin this app offers: {code}", nameof(code));

        var bars = await quotes.IntradayBarsAsync(asset, day, period, progress, cancellation);

        return new CandleSeries(
            code, InstrumentNames.Display(code, name), period, bars,
            await PreviousCloseAsync(quotes, asset, day, cancellation));
    }

    /// <summary>
    /// What the coin closed at on the day before the one being drawn.
    ///
    /// Asked of the daily series rather than taken from the minutes, because a day's move
    /// is measured against the day before it and not against its own first minute: a
    /// chart of one session that opened at 60,000 and closed at 61,000 rose 1.7% on the
    /// day if the day before ended at 60,000, and 0% if it is measured against its own
    /// opening. <see cref="CandleSeries.PreviousClose"/> is the field that decides, and
    /// zero there means "use the first bar", which is the wrong answer on every intraday
    /// period.
    ///
    /// Swallowed rather than thrown when the daily ask fails. It is one figure on the
    /// frame and not the frame: a day whose move is measured from its own opening is
    /// still a day drawn correctly, and losing the whole chart to a second request would
    /// be a worse trade than losing one number.
    /// </summary>
    private static async Task<double> PreviousCloseAsync(
        CryptoQuotes quotes, CryptoAsset asset, DateOnly day, CancellationToken cancellation)
    {
        try
        {
            var before = await quotes.BarsAsync(
                asset, day.AddDays(-LookBehind), day.AddDays(-1), null, cancellation);

            return before.Count > 0 ? before[^1].Close : 0;
        }
        catch (Exception)
        {
            return 0;
        }
    }

    /// <summary>
    /// Several coins' candles inside one day, on one axis.
    ///
    /// Composed by the stock board's own code, which already keys an intraday axis by the
    /// day *and* the clock — so six coins over the same twenty-four hours line up on the
    /// minutes they share without this class having an opinion about how.
    /// </summary>
    public static async Task<CandleBoard> LoadIntradayBoardAsync(
        CryptoQuotes quotes,
        IReadOnlyList<RaceEntry> entries,
        CandlePeriod period,
        DateOnly day,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var series = new List<CandleSeries>(entries.Count);
        var skipped = new List<string>();

        foreach (var entry in entries)
        {
            try
            {
                series.Add(await LoadIntradayAsync(
                    quotes, entry.Code, entry.Name, period, day, progress, cancellation));
            }
            catch (Exception)
            {
                skipped.Add(InstrumentNames.Display(entry.Code, entry.Name));
            }
        }

        return CandleBoardLoader.Compose(
            [.. series.Where(s => s.Count > 0)], period, skipped);
    }

    /// <summary>
    /// Several coins on one axis, as cumulative percentages — the same board the stock
    /// comparison draws, composed by the same code.
    ///
    /// Serial, and each coin asked for on its own: the comparison is the union of their
    /// days and each begins where its own history does, so a coin that has existed since
    /// 2014 is not silently cut down to the youngest one's age. See
    /// <see cref="CandleBoardLoader.Compose"/>.
    ///
    /// A coin that came back empty is named in <c>Skipped</c> rather than thrown: one
    /// coin the range does not reach is not the board's failure, and six coins are six
    /// chances for one of them to be that.
    /// </summary>
    public static async Task<CandleBoard> LoadBoardAsync(
        CryptoQuotes quotes,
        IReadOnlyList<RaceEntry> entries,
        CandlePeriod period,
        DateOnly from,
        DateOnly to,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var series = new List<CandleSeries>(entries.Count);
        var skipped = new List<string>();

        foreach (var entry in entries)
        {
            try
            {
                series.Add(await LoadAsync(
                    quotes, entry.Code, entry.Name, period, from, to, progress, cancellation));
            }
            catch (Exception)
            {
                skipped.Add(InstrumentNames.Display(entry.Code, entry.Name));
            }
        }

        return CandleBoardLoader.Compose(
            [.. series.Where(s => s.Count > 0)], period, skipped);
    }

    /// <summary>
    /// Daily bars folded into weeks or into months.
    ///
    /// A week is the ISO week — Monday to Sunday, and the week number the calendar gives
    /// it — rather than seven days counted from the range's start, because "the week
    /// Bitcoin did X" is a week everyone agrees about. A month is the calendar month,
    /// for the same reason.
    ///
    /// The open is the first day's open and the close the last day's close, so the
    /// aggregate's body is the span's own move and not an average of anything.
    /// </summary>
    private static List<TencentKline.CandleBar> Aggregate(
        IReadOnlyList<TencentKline.CandleBar> bars, bool byWeek)
    {
        var folded = new List<TencentKline.CandleBar>(bars.Count / (byWeek ? 7 : 30) + 1);

        var open = 0d;
        var high = 0d;
        var low = 0d;
        var close = 0d;
        var volume = 0d;
        var start = DateOnly.MinValue;
        var bucket = "";

        foreach (var bar in bars)
        {
            var key = byWeek
                ? $"{ISOWeek.GetYear(bar.Date.ToDateTime(TimeOnly.MinValue))}-" +
                  $"{ISOWeek.GetWeekOfYear(bar.Date.ToDateTime(TimeOnly.MinValue))}"
                : $"{bar.Date.Year}-{bar.Date.Month}";

            if (key != bucket)
            {
                if (bucket.Length > 0)
                {
                    folded.Add(new TencentKline.CandleBar(start, open, high, low, close, volume));
                }

                bucket = key;
                start = bar.Date;
                open = bar.Open;
                high = bar.High;
                low = bar.Low;
                volume = 0;
            }

            high = Math.Max(high, bar.High);
            low = Math.Min(low, bar.Low);
            close = bar.Close;
            volume += bar.Volume;
        }

        if (bucket.Length > 0)
        {
            folded.Add(new TencentKline.CandleBar(start, open, high, low, close, volume));
        }

        return folded;
    }
}
