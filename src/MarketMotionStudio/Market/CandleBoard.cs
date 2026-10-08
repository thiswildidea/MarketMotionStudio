using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One instrument on a comparison board: its own candles turned into a cumulative
/// percentage, laid on the board's axis.
///
/// The percentage, not the price, because that is the only thing two instruments can be
/// compared in. A share at 1,600 and an index at 3,800 drawn on one price axis put the
/// index's whole year in the top third of the frame and flatten the share to a line
/// against the bottom of it — a picture of the two *levels*, which nobody asked for, and
/// one whose vertical distance at any date is meaningless.
///
/// Measured from the instrument's own first bar's **open** on this board, which is
/// <see cref="CandleSeries.RangeReturn"/>'s basis too: two scales that disagreed about
/// where zero is would put two curves on one axis that could not be read against each
/// other.
/// </summary>
/// <param name="First">
/// The axis position this instrument's own history starts on, which is not the board's
/// first one for something that listed later — or that was suspended through the
/// board's opening stretch. Before it the track holds <see cref="double.NaN"/>, which
/// draws nothing and wins no comparison.
/// </param>
public sealed record CandleTrack(
    string Code,
    string Name,
    IReadOnlyList<double> Returns,
    int First,
    int Last,
    double Opening,
    double Closing)
{
    /// <summary>What this instrument is ahead or behind by over the whole board.</summary>
    public double Final => Returns[Last];

    /// <summary>The furthest ahead the curve ever is, for the axis's top.</summary>
    public double Peak { get; } = Reach(Returns, First, Last, true);

    /// <summary>The furthest behind, for the axis's bottom.</summary>
    public double Trough { get; } = Reach(Returns, First, Last, false);

    private static double Reach(IReadOnlyList<double> returns, int first, int last, bool top)
    {
        var best = 0d;

        for (var i = first; i <= last; i++)
        {
            if (double.IsNaN(returns[i]))
            {
                continue;
            }

            best = top ? Math.Max(best, returns[i]) : Math.Min(best, returns[i]);
        }

        return best;
    }
}

/// <summary>
/// Two or more instruments' candles on one axis, as cumulative percentages.
///
/// The axis is the **union** of the days (or, intraday, of the minutes) any of them
/// traded, not the intersection. The intersection is the tempting one and it is wrong: a
/// comparison of something listed ten years ago against something listed three years ago
/// would silently become a comparison of the last three years, and the frame would look
/// entirely plausible while answering a shorter question than the one that was asked.
/// Each track therefore begins where its own history does and is simply absent before
/// that — the same choice the holdings board makes, and for the same reason.
///
/// A day one of them lacks is carried forward rather than dropped: the value between two
/// of its own bars is the last one it reported, and a suspension is not a return to zero.
/// </summary>
/// <param name="Stamps">
/// What the axis is labelled with — a date for the daily periods, a clock time for the
/// intraday ones, which is what one session's axis is counted in.
/// </param>
public sealed record CandleBoard(
    IReadOnlyList<string> Stamps,
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<CandleTrack> Tracks,
    CandlePeriod Period,
    IReadOnlyList<string> Skipped)
{
    public int Count => Stamps.Count;

    /// <summary>Whether the frame is a comparison rather than one instrument's chart.</summary>
    public bool Comparing => Tracks.Count > 1;

    public DateOnly Start => Dates[0];

    public DateOnly End => Dates[^1];

    /// <summary>The axis's top and bottom: the furthest any curve got, either way.</summary>
    public double Peak => Tracks.Count == 0 ? 0 : Tracks.Max(t => t.Peak);

    public double Trough => Tracks.Count == 0 ? 0 : Tracks.Min(t => t.Trough);

    /// <summary>Whether the axis is counted in minutes of one session rather than in days.</summary>
    public bool Intraday => CandleLoader.IsMinute(Period);
}

/// <summary>
/// Loads a comparison board: one instrument at a time, then all of them onto one axis.
///
/// Serial on purpose, as every roster loader in this app is — a dozen simultaneous
/// requests to somebody else's public endpoint is the behaviour of a scraper, and these
/// are fetched one after another for the same reason they are everywhere else.
/// </summary>
public static class CandleBoardLoader
{
    /// <summary>
    /// The most instruments one frame can carry: the number of colours the palette has.
    ///
    /// Six rather than the watchlist's sixteen, because these are curves read against each
    /// other rather than rows read one at a time, and a seventh curve takes a colour the
    /// sixth already has — two lines of one colour on a chart whose whole purpose is
    /// telling them apart.
    /// </summary>
    public const int MostTracks = 6;

    /// <param name="months">
    /// How far back, or <see cref="CandleLoader.CustomMonths"/> for the two dates — the
    /// same tag the single-instrument fetch reads, so one preference means one thing on
    /// both. Ignored on the intraday periods, which take no span at all: they answer with
    /// the last few sessions the source still holds, and the board then draws the day they
    /// all share.
    /// </param>
    public static async Task<CandleBoard> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        CandlePeriod period,
        int months,
        DateOnly from,
        DateOnly to,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        var minute = CandleLoader.IsMinute(period);
        var series = new List<CandleSeries>(entries.Count);
        var skipped = new List<string>();

        if (minute)
        {
            var sessions = new List<MinuteSession>(entries.Count);

            foreach (var entry in entries)
            {
                try
                {
                    sessions.Add(await CandleMinutes.LoadAsync(
                        kline, entry.Code, entry.Name, period, progress, cancellation));
                }
                catch (Exception)
                {
                    // One listing with no minutes is not the board's failure: index futures
                    // have them, the BSE 50 does not, and neither Hong Kong nor New York does
                    // at all. Named in the status line rather than thrown.
                    skipped.Add(entry.Name);
                }
            }

            var day = SharedDay(sessions);

            if (day is null)
            {
                return new CandleBoard([], [], [], period, skipped);
            }

            foreach (var session in sessions)
            {
                var mine = session.Find(day.Id) ?? session.Days[0];

                series.Add(CandleMinutes.ForDay(session, mine));
            }
        }
        else
        {
            foreach (var entry in entries)
            {
                try
                {
                    series.Add(months == CandleLoader.CustomMonths
                        ? await CandleLoader.LoadAsync(
                            kline, entry.Code, entry.Name, period, from, to, progress, cancellation)
                        : await CandleLoader.LoadAsync(
                            kline, entry.Code, entry.Name, period, months, progress, cancellation));
                }
                catch (Exception)
                {
                    skipped.Add(entry.Name);
                }
            }
        }

        series = [.. series.Where(s => s.Count > 0)];

        var (stamps, dates, keys) = Axis(series, minute);

        if (keys.Count == 0)
        {
            return new CandleBoard([], [], [], period, skipped);
        }

        var place = new Dictionary<string, int>(StringComparer.Ordinal);

        for (var i = 0; i < keys.Count; i++)
        {
            place[keys[i]] = i;
        }

        var tracks = new List<CandleTrack>(series.Count);

        foreach (var one in series)
        {
            tracks.Add(Track(one, place, minute));
        }

        return new CandleBoard(stamps, dates, tracks, period, skipped);
    }

    /// <summary>
    /// The session every instrument on the board has, newest first: the day a multi-instrument
    /// minutes chart is a picture of.
    ///
    /// Shared rather than each one's own latest, because "these three, on one day" is the
    /// question — a frame comparing Monday's move on one listing against Tuesday's on another
    /// is not a comparison, and its axis would be two different days spliced together. Whole
    /// sessions are preferred; if they share none, the newest day they all have any part of is
    /// used, which is a shorter picture rather than no picture.
    /// </summary>
    private static MinuteDay? SharedDay(IReadOnlyList<MinuteSession> sessions)
    {
        if (sessions.Count == 0)
        {
            return null;
        }

        foreach (var pool in new[] { true, false })
        {
            var offered = pool
                ? sessions[0].Whole
                : [.. sessions[0].Days];

            for (var i = offered.Count - 1; i >= 0; i--)
            {
                var id = offered[i].Id;

                if (sessions.All(s => s.Days.Any(d => string.Equals(d.Id, id, StringComparison.Ordinal))))
                {
                    return sessions[0].Find(id);
                }
            }
        }

        return null;
    }

    /// <summary>
    /// The axis: every instant any instrument traded, oldest first, with what the frame
    /// labels it by.
    ///
    /// Keyed by a fixed-width string so that sorting the keys sorts the axis — a date
    /// followed by the clock for the intraday periods, the date alone otherwise.
    /// </summary>
    private static (List<string> Stamps, List<DateOnly> Dates, List<string> Keys) Axis(
        List<CandleSeries> series, bool minute)
    {
        var keys = new SortedSet<string>(StringComparer.Ordinal);
        var stamp = new Dictionary<string, string>(StringComparer.Ordinal);
        var day = new Dictionary<string, DateOnly>(StringComparer.Ordinal);

        foreach (var one in series)
        {
            foreach (var bar in one.Bars)
            {
                var key = minute
                    ? bar.Date.ToString("yyyyMMdd", CultureInfo.InvariantCulture) + bar.Clock
                    : bar.Date.ToString("yyyyMMdd", CultureInfo.InvariantCulture);

                keys.Add(key);

                if (!stamp.ContainsKey(key))
                {
                    stamp[key] = minute ? Clock(bar.Clock) : CandleLoader.Iso(bar.Date);
                    day[key] = bar.Date;
                }
            }
        }

        var ordered = keys.ToList();

        return (
            [.. ordered.Select(k => stamp[k])],
            [.. ordered.Select(k => day[k])],
            ordered);
    }

    /// <summary>"0935" as "09:35"— the minute endpoint's own stamp, read as a time.</summary>
    private static string Clock(string clock) =>
        clock.Length == 4 ? clock[..2] + ":" + clock[2..] : clock;

    /// <summary>
    /// One instrument's cumulative return on the board's axis.
    ///
    /// Its own first bar is its zero, wherever on the axis that falls, and the gap between
    /// two of its bars is carried forward rather than drawn as a hole: a listing suspended
    /// for a fortnight did not return to zero while it was away.
    /// </summary>
    private static CandleTrack Track(
        CandleSeries one, Dictionary<string, int> place, bool minute)
    {
        var returns = new double[place.Count];

        for (var i = 0; i < returns.Length; i++)
        {
            returns[i] = double.NaN;
        }

        var opening = one.Bars[0].Open;
        var first = -1;
        var last = -1;

        foreach (var bar in one.Bars)
        {
            var key = minute
                ? bar.Date.ToString("yyyyMMdd", CultureInfo.InvariantCulture) + bar.Clock
                : bar.Date.ToString("yyyyMMdd", CultureInfo.InvariantCulture);

            if (!place.TryGetValue(key, out var at))
            {
                continue;
            }

            returns[at] = opening > 0 ? ((bar.Close / opening) - 1) * 100 : 0;

            if (first < 0)
            {
                first = at;
            }

            last = at;
        }

        if (first < 0)
        {
            first = 0;
            last = Math.Max(0, returns.Length - 1);
        }

        var carried = 0d;

        for (var i = first; i <= last; i++)
        {
            if (double.IsNaN(returns[i]))
            {
                returns[i] = carried;
            }
            else
            {
                carried = returns[i];
            }
        }

        return new CandleTrack(
            one.Code, one.Name, returns, first, last, opening, one.Bars[^1].Close);
    }
}
