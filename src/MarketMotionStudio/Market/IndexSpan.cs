using System.Net.Http;

namespace MarketMotionStudio.Market;

/// <summary>
/// An index's own months and years, drawn on the span's axis rather than on a clock.
///
/// <para>
/// **The lower half of the frame answers "what else was happening", so it must be plotted on the
/// upper half's axis and not on a parallel one.** Two axes, one above the other, is a picture
/// that invites the reader to line a turn in the index up against whichever minute of their own
/// curve they happen to be looking at. <see cref="SpanFrame"/> already counted every sample into
/// a slot, so both halves are asking for the same numbering and getting it.
/// </para>
///
/// <para>
/// **A missing day is carried forward, not skipped.** An index that did not trade on a day the
/// book held mainland shares through — a holiday in one venue and not the other — has no price to
/// print, and dropping the row would move every later slot one position left and slide the whole
/// line out of register with the curve above it. Carrying the previous price forward holds the
/// line flat for exactly the gap that happened.
/// </para>
///
/// <para>
/// **Every number handed out is still a percentage**, against the close before the range began.
/// Across a year this matters more, not less: 恒生指数 at twenty-three thousand and 上证指数 at
/// three thousand six hundred cannot share a vertical axis at any granularity, and the change is
/// the one quantity they share.
/// </para>
/// </summary>
public static class IndexSpan
{
    /// <summary>Sentinel for "the day's close": the same convention <see cref="ReturnSample"/>
    /// keeps, so a daily span is not pretending to know an afternoon.</summary>
    private const int WholeDay = -1;

    /// <summary>How many indexes one load reads at once.</summary>
    private const int Bunch = 4;

    /// <summary>
    /// How far back the closing prices are asked for, beyond the span itself.
    ///
    /// The line has to start at zero per cent, which needs the close *before* the range: a year
    /// of 上证 that opens at "+1.4%" has invented a day of return nobody held. Ten calendar days
    /// covers a long weekend in either venue and the mainland's own week-long closures.
    /// </summary>
    private const int LookBackDays = 10;

    /// <summary>
    /// Reads each picked index across the span, on the slots <paramref name="axis"/> numbers.
    /// </summary>
    /// <param name="http">The shared client — the intraday session source answers off it.</param>
    /// <param name="kline">The quote source every closing price comes off.</param>
    /// <param name="entries">What the reader ticked, in the catalog's own order.</param>
    /// <param name="axis">The numbering the upper half of the frame is already drawn on.</param>
    /// <param name="grain">Minutes inside recent days, closes before them.</param>
    /// <param name="cancellation">Cooperative cancellation.</param>
    public static async Task<List<IndexIntradaySeries>> LoadAsync(
        HttpClient http,
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        SpanAxis axis,
        ReturnGrain grain,
        CancellationToken cancellation)
    {
        if (entries.Count == 0 || axis.Slots.Count == 0)
        {
            return [];
        }

        var first = axis.Slots[0].Day;
        var last = axis.Slots[^1].Day;

        // **A single day is a clock, not a count.** The axis numbers a one-day span by real
        // minutes — the session keeps its own clock — so the index line must too, and it must
        // stay an intraday series (venue open and close, no slot end): numbered by position it
        // would walk 0..240 against a window running 09:30 to 15:00 and never leave the left
        // edge. Multi-day spans number everything by position, which is the branch below.
        var singleDay = grain == ReturnGrain.Session && first == last;

        var gate = new SemaphoreSlim(Bunch);

        var tasks = entries.Select(async entry =>
        {
            await gate.WaitAsync(cancellation);

            try
            {
                var points = grain == ReturnGrain.Session
                    ? await Minutes(http, entry.Code, cancellation)
                    : await Closes(kline, entry.Code, entry.Name, first, last, cancellation);

                return Build(entry, axis, points, singleDay);
            }
            catch (Exception) when (!cancellation.IsCancellationRequested)
            {
                // A missing index is drawn as a missing line, which the navigator already declines
                // to tick. Putting an error bar across a frame that is still correct is worse than
                // the gap, and the next fetch asks again.
                return (IndexIntradaySeries?)null;
            }
            finally
            {
                gate.Release();
            }
        });

        var loaded = await Task.WhenAll(tasks);

        return [.. loaded.Where(series => series is not null).Select(series => series!)];
    }

    /// <summary>
    /// One index's closing prices over the span, and a little before it.
    ///
    /// Unadjusted, for the same reason the book's own prices are: this app says "the index rose
    /// four tenths of one per cent on the day", which is a sentence about the number 3,681 and
    /// not about a dividend nobody received.
    /// </summary>
    private static async Task<SortedDictionary<DateOnly, SortedDictionary<int, double>>> Closes(
        TencentKline kline, string code, string name, DateOnly first, DateOnly last,
        CancellationToken cancellation)
    {
        var closes = await HistoryWalk.ClosesAsync(
            kline, code, name, first.AddDays(-LookBackDays), last, null, cancellation, adjustment: "");

        var points = new SortedDictionary<DateOnly, SortedDictionary<int, double>>();

        foreach (var (day, price) in closes)
        {
            points[day] = new SortedDictionary<int, double> { [WholeDay] = price };
        }

        return points;
    }

    /// <summary>One index's recent sessions, minute by minute.</summary>
    private static async Task<SortedDictionary<DateOnly, SortedDictionary<int, double>>> Minutes(
        HttpClient http, string code, CancellationToken cancellation) =>
        await HoldingReturns.ReadSessionsOneAsync(http, code, cancellation);

    /// <summary>
    /// Places one index's prices on the span's slots, and hands back the series the frame draws.
    /// </summary>
    /// <param name="singleDay">
    /// Whether the span is one trading day wide — in which case the slots carry real minutes and
    /// the series keeps intraday semantics (no <see cref="IndexIntradaySeries.SlotEnd"/>), the
    /// same shape a same-day board reads.
    /// </param>
    private static IndexIntradaySeries? Build(
        RaceEntry entry, SpanAxis axis,
        SortedDictionary<DateOnly, SortedDictionary<int, double>> points,
        bool singleDay)
    {
        // Pass one: whatever the source has for each slot, blanks included. Doing it apart from
        // the filling is what lets the second pass be one rule rather than four branches — and it
        // is the blanks that carry the information about a closure.
        var raw = new double?[axis.Slots.Count];
        var opened = -1;

        for (var i = 0; i < axis.Slots.Count; i++)
        {
            var (day, at) = axis.Slots[i];

            if (points.TryGetValue(day, out var quoted) && Price(quoted, at) is { } price)
            {
                raw[i] = price;
                opened = opened < 0 ? i : opened;
            }
        }

        if (opened < 0)
        {
            return null;
        }

        // Pass two: carried forward. Nothing hunts backwards for a price that has not happened
        // yet, so a line missing its first days stays flat at its first real one rather than
        // borrowing the end of the range to fill them.
        var minutes = new List<IndexMinute>(axis.Slots.Count);
        var carried = raw[opened]!.Value;

        for (var i = 0; i < raw.Length; i++)
        {
            if (raw[i] is { } price)
            {
                carried = price;
            }

            minutes.Add(new IndexMinute(singleDay ? axis.Slots[i].Minute : i, carried));
        }

        return new IndexIntradaySeries(
            entry.Code,
            entry.Name,
            entry.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase),
            Previously(points, axis.Slots[opened], carried),
            minutes)
        {
            SlotEnd = singleDay ? null : minutes.Count - 1,
        };
    }

    /// <summary>What one slot's price is, whichever grain the line is drawn on.</summary>
    private static double? Price(SortedDictionary<int, double> day, int at)
    {
        if (day.TryGetValue(at, out var exact))
        {
            return exact;
        }

        if (at == WholeDay)
        {
            return null;
        }

        // A minute the index printed nothing for takes the last price before it, which is what
        // the line already does for a day the index never traded. A day asked for its close and
        // quoted none has nothing: `day` holds the sole sentinel key and missed it above.
        var carried = 0.0;

        foreach (var pair in day)
        {
            if (pair.Key > at)
            {
                break;
            }

            carried = pair.Value;
        }

        return carried > 0 ? carried : null;
    }

    /// <summary>
    /// The close the range is measured against: the last price before the range's first slot.
    ///
    /// Found rather than assumed, because either venue's first trading day inside a range is not
    /// always the range's first day — a Monday after a quarter-day closure would otherwise be
    /// measured against nothing and open flat, hiding the move the closure swallowed.
    /// </summary>
    private static double Previously(
        SortedDictionary<DateOnly, SortedDictionary<int, double>> points,
        (DateOnly Day, int Minute) opening,
        double fallback)
    {
        var (day, at) = opening;

        var before = points
            .Where(pair => pair.Key <= day)
            .SelectMany(pair => pair.Value.Where(slot => pair.Key < day || slot.Key < at)
                .Select(slot => (Day: pair.Key, Minute: slot.Key, Price: slot.Value)))
            .OrderBy(found => found.Day)
            .ThenBy(found => found.Minute)
            .Select(found => found.Price)
            .ToList();

        return before.Count > 0 ? before[^1] : fallback;
    }
}
