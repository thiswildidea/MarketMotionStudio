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
/// Measured from the level <see cref="CandleSeries.RangeReturn"/> measures from — the close
/// before the range when the source gave one, the range's own first open otherwise. The two
/// paths have to agree about it: two scales that put zero in different places would put two
/// curves on one axis that could not be read against each other. On the intraday board it is
/// the previous close, which is what makes a day's comparison a comparison of the day.
/// </summary>
/// <param name="First">
/// The axis position this instrument's own history starts on, which is not the board's
/// first one for something that listed later — or that was suspended through the
/// board's opening stretch. Before it the track holds <see cref="double.NaN"/>, which
/// draws nothing and wins no comparison.
/// </param>
/// <param name="Baseline">The price every one of <paramref name="Returns"/> is a percentage of.</param>
public sealed record CandleTrack(
    string Code,
    string Name,
    IReadOnlyList<double> Returns,
    int First,
    int Last,
    double Baseline)
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
/// <param name="Sessions">
/// What the intraday board was built from, kept so that another of its days can be drawn
/// without asking the source again; null on a daily board, whose axis is a span rather than
/// a session. See <see cref="Days"/>.
/// </param>
/// <param name="Drawn">
/// The session every curve on an intraday board is drawn on, or null on a daily one. The
/// day control shows it, and it is the only day the board is a picture of.
/// </param>
/// <param name="Series">
/// What the tracks were built from, kept so that a board can be rebuilt over some of them
/// without asking the source again — see <see cref="CandleBoardLoader.Only"/>. In track
/// order, and with the instruments that came back empty already dropped.
/// </param>
public sealed record CandleBoard(
    IReadOnlyList<string> Stamps,
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<CandleTrack> Tracks,
    CandlePeriod Period,
    IReadOnlyList<string> Skipped,
    IReadOnlyList<MinuteSession>? Sessions = null,
    MinuteDay? Drawn = null,
    IReadOnlyList<CandleSeries>? Series = null)
{
    public int Count => Stamps.Count;

    /// <summary>Whether the frame is a comparison rather than one instrument's chart.</summary>
    public bool Comparing => Tracks.Count > 1;

    public DateOnly Start => Dates[0];

    public DateOnly End => Dates[^1];

    /// <summary>
    /// The days this board can be drawn on, newest first — what the day control offers on an
    /// intraday board, and empty on a daily one. Every one of them arrived with the fetch, so
    /// moving between them is a redraw; see <see cref="CandleBoardLoader.On"/>.
    /// </summary>
    public IReadOnlyList<MinuteDay> Days =>
        Sessions is { Count: > 0 } sessions ? CandleBoardLoader.SharedDays(sessions) : [];

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

    /// <summary>
    /// The most instruments the apart frame can carry: one panel each, stacked.
    ///
    /// Three, and not because the palette runs out — that is <see cref="MostTracks"/>, and it
    /// still applies to the list. A panel is a ninth of the frame's height at three, which is
    /// about a third of what one instrument's chart gets, and a fourth would put each of them
    /// under a hundred pixels of plot: a curve with no room for its own axis, in a frame whose
    /// whole reason for being split up was that each could be read on its own scale.
    /// </summary>
    public const int MostPanels = 3;

    /// <param name="months">
    /// How far back, or <see cref="CandleLoader.CustomMonths"/> for the two dates — the
    /// same tag the single-instrument fetch reads, so one preference means one thing on
    /// both. Ignored on the intraday periods, which take no span at all: they answer with
    /// the last few sessions the source still holds, and the board then draws the day they
    /// all share.
    /// </param>
    /// <param name="day">
    /// Which of the days they share to draw, or empty for the newest. A saved preference
    /// naming a session the source has since dropped — or that these particular instruments
    /// do not share — falls back to the newest rather than drawing nothing.
    /// </param>
    public static async Task<CandleBoard> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        CandlePeriod period,
        int months,
        DateOnly from,
        DateOnly to,
        IProgress<string> progress,
        CancellationToken cancellation,
        string day = "")
    {
        if (CandleLoader.IsMinute(period))
        {
            var sessions = new List<MinuteSession>(entries.Count);
            var missing = new List<string>();

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
                    missing.Add(entry.Name);
                }
            }

            var days = SharedDays(sessions);

            var chosen = days.FirstOrDefault(d => string.Equals(d.Id, day, StringComparison.Ordinal))
                ?? days.FirstOrDefault();

            return chosen is null
                ? new CandleBoard([], [], [], period, missing)
                : Build(sessions, period, missing, chosen);
        }

        var series = new List<CandleSeries>(entries.Count);
        var skipped = new List<string>();

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

        return Compose(series, period, skipped);
    }

    /// <summary>
    /// The whole board on another of its days: a redraw, not a fetch.
    ///
    /// Every day the control offers arrived with the requests that built the board, so moving
    /// between them costs the painting and nothing else. Asking again would be six more requests
    /// for rows already in hand — and, since the source keeps only the last few sessions, a
    /// second request is also the one thing that could quietly answer with a different window.
    ///
    /// A day the board does not offer leaves it as it was, rather than drawing an empty frame.
    /// </summary>
    public static CandleBoard On(CandleBoard board, string day)
    {
        if (board.Sessions is not { Count: > 0 } sessions)
        {
            return board;
        }

        var wanted = SharedDays(sessions)
            .FirstOrDefault(d => string.Equals(d.Id, day, StringComparison.Ordinal));

        return wanted is null ? board : Build(sessions, board.Period, board.Skipped, wanted);
    }

    /// <summary>
    /// The same board over its first <paramref name="count"/> instruments — a redraw, not a
    /// fetch, and not a trim either.
    ///
    /// The apart frame draws one instrument per panel and has room for
    /// <see cref="MostPanels"/> of them, so the instruments past the third are not drawn. They
    /// are dropped from the **axis** as well, rather than merely left undrawn: the axis is the
    /// union of the days its tracks traded, and an instrument the frame is not about must not
    /// stretch the dates everyone else is read against. Rebuilt from the fetched series rather
    /// than clipped, because which positions a track carries forward is not recoverable from
    /// the returns alone — a carried-forward value does not look like one.
    ///
    /// Asked for a board that already has that many or fewer, it returns the board itself.
    /// </summary>
    public static CandleBoard Only(CandleBoard board, int count)
    {
        if (count <= 0 || board.Series is not { Count: > 0 } series || count >= series.Count)
        {
            return board;
        }

        return Compose(
            [.. series.Take(count)], board.Period, board.Skipped, board.Sessions, board.Drawn);
    }

    /// <summary>
    /// The days every instrument on the board has, newest first: what a multi-instrument minutes
    /// chart may be drawn on.
    ///
    /// Shared rather than each one's own latest, because "these three, on one day" is the
    /// question — a frame comparing Monday's move on one listing against Tuesday's on another
    /// is not a comparison, and its axis would be two different days spliced together. Whole
    /// sessions first and part-days only if they share no whole one: a chart missing its own
    /// opening would sit in the list as an ordinary date. These are also the order the board
    /// takes its default from, so the first of them is the day it opens on.
    /// </summary>
    public static IReadOnlyList<MinuteDay> SharedDays(IReadOnlyList<MinuteSession> sessions)
    {
        if (sessions.Count == 0)
        {
            return [];
        }

        foreach (var whole in new[] { true, false })
        {
            var offered = whole ? sessions[0].Whole : sessions[0].Days;

            var shared = offered
                .Where(d => sessions.All(
                    s => s.Days.Any(o => string.Equals(o.Id, d.Id, StringComparison.Ordinal))))
                .OrderByDescending(d => d.Date)
                .ToList();

            if (shared.Count > 0)
            {
                return shared;
            }
        }

        return [];
    }

    /// <summary>One day of every instrument on the board, onto one axis.</summary>
    private static CandleBoard Build(
        IReadOnlyList<MinuteSession> sessions, CandlePeriod period,
        IReadOnlyList<string> skipped, MinuteDay day) =>
        Compose(
            [.. sessions.Select(s => CandleMinutes.ForDay(s, s.Find(day.Id) ?? s.Days[0]))],
            period, skipped, sessions, day);

    /// <summary>The board a set of series makes, on the union of the axis they have.</summary>
    private static CandleBoard Compose(
        List<CandleSeries> series, CandlePeriod period, IReadOnlyList<string> skipped,
        IReadOnlyList<MinuteSession>? sessions = null, MinuteDay? drawn = null)
    {
        var minute = CandleLoader.IsMinute(period);

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

        return new CandleBoard(stamps, dates, tracks, period, skipped, sessions, drawn, series);
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
    /// Its own first bar is where the curve starts, wherever on the axis that falls, and the gap
    /// between two of its bars is carried forward rather than drawn as a hole: a listing
    /// suspended for a fortnight did not return to zero while it was away.
    ///
    /// The percentages are of <see cref="CandleSeries.Baseline"/> and not of the first bar's
    /// open — the difference being the whole of the intraday board. See there.
    /// </summary>
    private static CandleTrack Track(
        CandleSeries one, Dictionary<string, int> place, bool minute)
    {
        var returns = new double[place.Count];

        for (var i = 0; i < returns.Length; i++)
        {
            returns[i] = double.NaN;
        }

        var baseline = one.Baseline;
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

            returns[at] = baseline > 0 ? ((bar.Close / baseline) - 1) * 100 : 0;

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

        return new CandleTrack(one.Code, one.Name, returns, first, last, baseline);
    }
}
