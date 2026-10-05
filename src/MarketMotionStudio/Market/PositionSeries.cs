namespace MarketMotionStudio.Market;

/// <summary>
/// How a holding's picture advances.
///
/// Two motions, and they answer different questions — the same pair the candle page offers,
/// and for the same reason. <see cref="Grow"/> lays the whole span down, so the frame is the
/// holding's entire story and its shape on screen is its shape in time. <see cref="Scroll"/>
/// holds a window of the span and walks it forward, which is the only way a decade of daily
/// marks stays wide enough to read: grown across twelve years, a three-month wobble is two
/// pixels and a crash is a slope.
/// </summary>
public enum PositionMotion
{
    /// <summary>The whole span, filled from its first day to its last.</summary>
    Grow = 0,

    /// <summary>A window of fixed length, walked from the start of the span to its end.</summary>
    Scroll = 1,
}

/// <summary>
/// One instrument's holding, laid out along the board's own date axis.
///
/// The value is what the shares bought with the board's capital are worth on that day.
/// The array is as long as the board's axis and only <see cref="First"/>..<see cref="Last"/>
/// are ever read: an instrument that listed after the range began has no holding before its
/// own first close, and drawing one at the axis would be a plunge the price never made.
///
/// Days the instrument itself did not trade — a suspension, or a holiday one venue kept and
/// another did not — carry the last mark forward. The shares were still worth what they were
/// worth, and a line with holes in it reads as missing data rather than as a quiet day.
/// </summary>
/// <param name="MaxDrawdownPct">
/// The deepest fall from a running peak, as a positive percentage — the figure a
/// holder is asked to stomach, and the one a return percentage alone hides.
/// </param>
public sealed record PositionTrack(
    string Code,
    string Name,
    IReadOnlyList<double> Value,
    int First,
    int Last,
    double Capital,
    double MaxDrawdownPct)
{
    public double FinalValue => Value[Last];

    public double Profit => FinalValue - Capital;

    /// <summary>The headline percentage: what the holding returned over what was paid in.</summary>
    public double ReturnPercent => Capital > 0 ? (FinalValue / Capital - 1) * 100 : 0;

    /// <summary>The tallest figure this holding reaches, for the board's axis.</summary>
    public double Peak
    {
        get
        {
            var top = Value[First];

            for (var i = First; i <= Last; i++)
            {
                top = Math.Max(top, Value[i]);
            }

            return top;
        }
    }
}

/// <summary>
/// One or more holdings run over the same span on one axis, sharing one capital.
///
/// **One axis, and it is the union of the days they have.** The alternative — the days they
/// all have — would quietly cut a decade-long comparison down to the youngest listing's three
/// years, and the frame would look entirely plausible while answering a shorter question than
/// the one that was asked. So the axis is every day any of them traded, and each track simply
/// begins where its own history does.
///
/// That is also why there is one capital and not one per track: with the same amount put in
/// on each instrument's own first day, the curves are directly comparable, and the distance
/// between two of them at a given date is the answer to "which of these was the better place
/// for it". Two different amounts would make the picture a statement about the amounts.
/// </summary>
/// <param name="Skipped">
/// Instruments the range could not hold — one that listed after it, or was suspended
/// throughout. Reported rather than drawn at a flat cost: a line along the capital is a line
/// that says "this one did nothing for ten years", which is not what happened.
/// </param>
public sealed record PositionBoard(
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<PositionTrack> Tracks,
    double Capital,
    IReadOnlyList<string> Skipped)
{
    public DateOnly Start => Dates[0];

    public DateOnly End => Dates[^1];

    /// <summary>Whether the frame is a comparison rather than a single holding.</summary>
    public bool Comparing => Tracks.Count > 1;

    /// <summary>The tallest figure any line reaches, the capital included, for the axis.</summary>
    public double Peak => Math.Max(Tracks.Max(t => t.Peak), Capital);
}

/// <summary>
/// Builds a board from one or more instruments' daily closes: a single purchase at the first
/// close of the range that instrument has, then nothing but the mark-to-market.
///
/// This is the other half of the plan page's question. A plan buys on a schedule and its
/// interest is what the discipline averaged into; a holding buys once and its interest is
/// what the *price* did — which is why the capital line is flat and the drawdown is a headline
/// figure here while it is noise there. The same plainness as the plan: adjusted closes, no
/// fees, no dividends reinvested, so the numbers describe the price series and say so on the
/// frame.
///
/// The second instrument and the ones after it change nothing about that: each is bought once,
/// on its own first day, with the same amount, and then left alone. What the board adds is the
/// comparison — the same question asked of several instruments, which is how the question is
/// actually asked. ("Should I have held this, or that?") The curves are all in one currency
/// because the page only offers the market in force, which is also why the search on it is
/// filtered to that market.
/// </summary>
public static class PositionLoader
{
    /// <summary>
    /// The most holdings one frame can carry.
    ///
    /// A ceiling rather than a free-for-all, and the page refuses an over-long list rather than
    /// drawing the first few: six end-labels, six card values and six curves are still a
    /// comparison, and a dozen is a barcode with its labels on top of one another. Silently
    /// dropping the seventh would be worse than refusing it — the frame would answer about a
    /// list nobody chose.
    /// </summary>
    public const int MostTracks = 6;

    public static async Task<PositionBoard> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        double capital,
        DateOnly start,
        DateOnly end,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        if (capital <= 0)
        {
            throw new ArgumentException("The capital must be positive.", nameof(capital));
        }

        if (entries.Count == 0)
        {
            throw new InvalidOperationException("A board needs at least one holding.");
        }

        var walks = new List<(string Code, string Name, SortedList<DateOnly, double> Closes)>(entries.Count);
        var skipped = new List<string>();

        foreach (var entry in entries)
        {
            var display = InstrumentNames.Display(entry.Code, entry.Name);

            var closes = await HistoryWalk.ClosesAsync(kline, entry.Code, display, start, end, progress, cancellation);

            // A holding needs a buy and at least one mark after it. Anything less is the range
            // never reaching this instrument, and it is named rather than drawn — see the note
            // on `PositionBoard.Skipped`.
            if (closes.Count < 2)
            {
                skipped.Add(display);
                continue;
            }

            walks.Add((entry.Code, display, closes));
        }

        if (walks.Count == 0)
        {
            throw new InvalidOperationException("None of the instruments has a price inside the range.");
        }

        // The union, walked in order — see the note on `PositionBoard`.
        var union = new SortedSet<DateOnly>();

        foreach (var walk in walks)
        {
            foreach (var day in walk.Closes.Keys)
            {
                union.Add(day);
            }
        }

        var dates = union.ToArray();
        var at = new Dictionary<DateOnly, int>(dates.Length);

        for (var i = 0; i < dates.Length; i++)
        {
            at[dates[i]] = i;
        }

        var tracks = new List<PositionTrack>(walks.Count);

        foreach (var walk in walks)
        {
            // Bought once, at the first close the range actually holds. The walk trims to what
            // the source has, so this is the first trading day of the holding — or of the
            // listing, when it listed inside the range.
            var days = walk.Closes.Keys;
            var shares = capital / walk.Closes[days[0]];

            var first = at[days[0]];
            var last = at[days[^1]];

            var value = new double[dates.Length];

            // The last mark, carried across the days this instrument had none.
            var held = 0d;

            var peak = double.NegativeInfinity;
            var worst = 0d;

            for (var i = first; i <= last; i++)
            {
                if (walk.Closes.TryGetValue(dates[i], out var close))
                {
                    held = shares * close;
                }

                value[i] = held;

                // The drawdown is measured against the running peak of this holding's own
                // value, which is the question a holder asks ("how far down was I"), not
                // against the capital — a position that never fell below its cost still fell,
                // and by more than a return figure shows.
                if (held > peak)
                {
                    peak = held;
                }

                worst = Math.Max(worst, peak > 0 ? (1 - held / peak) * 100 : 0);
            }

            tracks.Add(new PositionTrack(walk.Code, walk.Name, value, first, last, capital, worst));
        }

        return new PositionBoard(dates, tracks, capital, skipped);
    }
}
