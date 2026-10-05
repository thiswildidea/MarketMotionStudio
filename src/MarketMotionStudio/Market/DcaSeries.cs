using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>How often a plan buys.</summary>
public enum DcaFrequency
{
    /// <summary>Every trading day, the way the source video that inspired the page does it.</summary>
    Daily = 0,

    /// <summary>The first trading day of each ISO week.</summary>
    Weekly = 1,

    /// <summary>The first trading day of each month.</summary>
    Monthly = 2,
}

/// <summary>
/// How a plan's picture advances.
///
/// Two motions, and they answer different questions — the same pair the candle page and the
/// holdings page offer, and for the same reason. <see cref="Grow"/> lays the whole span down,
/// so the frame is the plan's entire story and its shape on screen is its shape in time.
/// <see cref="Scroll"/> holds a window of the span and walks it forward, which is the only
/// way a decade of daily marks stays wide enough to read: grown across twelve years, a
/// three-month wobble is two pixels and a bad year is a slope.
/// </summary>
public enum DcaMotion
{
    /// <summary>The whole span, filled from its first day to its last.</summary>
    Grow = 0,

    /// <summary>A window of fixed length, walked from the start of the span to its end.</summary>
    Scroll = 1,
}

/// <summary>
/// One plan, drawn along the board's own date axis.
///
/// The two series are what the plan is: what the shares bought so far are worth, and what has
/// been paid in for them. Both are indexed by the board's day rather than by this instrument's
/// own, because a plan is only comparable with another plan when both are read on the same
/// calendar — see <see cref="DcaBoard"/>.
/// </summary>
/// <param name="First">The board's index of this instrument's first trading day in the range.</param>
/// <param name="Last">The board's index of its last one.</param>
/// <param name="Buys">How many times it bought, which is its own: an instrument that listed
/// later bought fewer times and paid in less.</param>
public sealed record DcaTrack(
    string Code,
    string Name,
    IReadOnlyList<double> Value,
    IReadOnlyList<double> Invested,
    int First,
    int Last,
    int Buys)
{
    public double FinalValue => Value[Last];

    public double FinalInvested => Invested[Last];

    public double Profit => FinalValue - FinalInvested;

    /// <summary>The headline percentage: what the plan returned over what was paid in.</summary>
    public double ReturnPercent => FinalInvested > 0 ? (FinalValue / FinalInvested - 1) * 100 : 0;

    /// <summary>The tallest figure this plan's value line reaches, for the board's axis.</summary>
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
/// One or more plans run over the same span on one axis, on one cadence and one amount.
///
/// **One axis, and it is the union of the days they have.** The alternative — the days they all
/// have — would quietly cut a decade-long comparison down to the youngest listing's three years,
/// and the frame would look entirely plausible while answering a shorter question than the one
/// that was asked. So the axis is every day any of them traded, and each plan simply begins where
/// its own history does.
///
/// **One amount and one cadence for all of them, not one per plan.** The question a comparison
/// asks is *which of these was the better place for the money*, and that question has an answer
/// only if the money went in the same way — put different amounts in on different schedules and
/// the picture is a statement about the amounts. An instrument that listed later still buys fewer
/// times and pays in less, because for part of the span it could not be bought; that difference
/// is the instrument's, not the plan's, and it is the one thing the comparison is allowed to show.
/// </summary>
/// <param name="Skipped">
/// Instruments the range could not hold — one that listed after it, or was suspended throughout.
/// Reported rather than drawn: a line along nothing would say "this plan did nothing for ten
/// years", which is not what happened.
/// </param>
public sealed record DcaBoard(
    IReadOnlyList<DateOnly> Dates,
    IReadOnlyList<DcaTrack> Tracks,
    double Amount,
    DcaFrequency Frequency,
    IReadOnlyList<string> Skipped)
{
    public DateOnly Start => Dates[0];

    public DateOnly End => Dates[^1];

    /// <summary>Whether the frame is a comparison rather than a single plan.</summary>
    public bool Comparing => Tracks.Count > 1;

    /// <summary>How many buys the frame names: the most any one plan managed.</summary>
    public int Buys => Tracks.Count == 0 ? 0 : Tracks.Max(t => t.Buys);

    /// <summary>
    /// Which plan's paid-in line the frame draws when several are on it.
    ///
    /// Six paid-in lines on one axis are one thick line — buy the same amount on the same cadence
    /// from the same day and the six staircases are the same staircase drawn six times — so the
    /// frame draws one, and it is the one that has paid in the most. That is the earliest of them,
    /// and it is the upper bound of all six: drawing the *least* would make every other plan look
    /// further ahead than it is, which is the one lie a comparison must not tell.
    /// </summary>
    public int Reference
    {
        get
        {
            var at = 0;

            for (var i = 1; i < Tracks.Count; i++)
            {
                if (Tracks[i].FinalInvested > Tracks[at].FinalInvested)
                {
                    at = i;
                }
            }

            return at;
        }
    }

    /// <summary>The tallest figure any line reaches, the shared paid-in line included.</summary>
    public double Peak
    {
        get
        {
            var top = 0.0;

            foreach (var track in Tracks)
            {
                top = Math.Max(top, track.Peak);
            }

            return Tracks.Count == 0 ? top : Math.Max(top, Tracks[Reference].FinalInvested);
        }
    }
}

/// <summary>
/// Builds plans from one or more instruments' daily closes.
///
/// The closes come from <see cref="HistoryWalk"/>, the shared backwards walk that
/// gathers years of bars from an endpoint that serves them six hundred and forty
/// at a time; see there for why the range is negotiated rather than asked for.
///
/// The simulation itself is deliberately plain: on each buy date the fixed amount
/// buys <c>amount / close</c> shares at that day's close, and every day is marked
/// with what has been paid in and what the shares are then worth. No fees, no
/// slippage, no timing but the calendar — the closing figures are a description of
/// the price series, not of anything anyone could have executed, which is what the
/// frame's disclaimer says.
///
/// The closes are adjusted ones (see <see cref="HistoryWalk"/>), so a dividend and
/// a split are already inside the answer: the price a distribution would knock
/// down does not fall here, which is to say the plan is drawn as though every
/// distribution were reinvested at that day's close. That is a measure, and it is
/// the generous one — a holder who took the cash, or who owed tax on it, earned
/// less than these figures say.
///
/// **The buy dates are read from each instrument's own calendar, not from a grid.**
/// A holiday on a Monday means the week's buy lands on Tuesday, and that is what a
/// person putting money in would have done. The same reading is why a week or a month
/// is recognised by the trading day that opens it rather than by its number: the first
/// trading day of the range belongs to the week it is in and does not also buy, or
/// the first week would be bought into twice — once at the edge and once in full.
/// </summary>
public static class DcaPlanner
{
    /// <summary>
    /// The most plans one frame can carry.
    ///
    /// Six end-labels, six card values and six curves are still a comparison; a dozen is a
    /// barcode with its labels on top of one another. The page refuses an over-long list rather
    /// than drawing the first few — a frame that silently dropped the seventh would answer about
    /// a list nobody chose.
    /// </summary>
    public const int MostTracks = 6;

    public static async Task<DcaBoard> LoadBoardAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> entries,
        DcaFrequency frequency,
        double amount,
        DateOnly start,
        DateOnly end,
        IProgress<string> progress,
        CancellationToken cancellation)
    {
        if (amount <= 0)
        {
            throw new ArgumentException("The amount must be positive.", nameof(amount));
        }

        if (entries.Count == 0)
        {
            throw new InvalidOperationException("A board needs at least one plan.");
        }

        var walks = new List<(string Code, string Name, SortedList<DateOnly, double> Closes)>(entries.Count);
        var skipped = new List<string>();

        foreach (var entry in entries)
        {
            var display = InstrumentNames.Display(entry.Code, entry.Name);

            var closes = await HistoryWalk.ClosesAsync(kline, entry.Code, display, start, end, progress, cancellation);

            // A plan needs something to buy and at least one mark after it. Anything less is the
            // range never reaching this instrument, and it is named rather than drawn — see the
            // note on `DcaBoard.Skipped`.
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

        // The union, walked in order — see the note on `DcaBoard`.
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

        var tracks = new List<DcaTrack>(walks.Count);

        foreach (var walk in walks)
        {
            var days = walk.Closes.Keys;
            var first = at[days[0]];
            var last = at[days[^1]];

            var value = new double[dates.Length];
            var paid = new double[dates.Length];

            var shares = 0d;
            var invested = 0d;
            var buys = 0;

            var lastWeek = ISOWeek.GetWeekOfYear(days[0].ToDateTime(TimeOnly.MinValue));
            var lastMonth = days[0].Month;

            // The last mark, carried across the days this instrument did not trade — a suspension,
            // or a holiday one venue kept and another did not. The shares were still worth what
            // they were worth, and a plan buys nothing on a day the venue was shut, so the
            // cadence is read off the days this one actually had.
            var held = 0d;

            for (var i = first; i <= last; i++)
            {
                if (walk.Closes.TryGetValue(dates[i], out var close))
                {
                    var dateTime = dates[i].ToDateTime(TimeOnly.MinValue);
                    var week = ISOWeek.GetWeekOfYear(dateTime);

                    var isBuy = frequency switch
                    {
                        DcaFrequency.Daily => true,
                        DcaFrequency.Weekly => week != lastWeek,
                        _ => dates[i].Month != lastMonth,
                    };

                    lastWeek = week;
                    lastMonth = dates[i].Month;

                    if (isBuy)
                    {
                        shares += amount / close;
                        invested += amount;
                        buys++;
                    }

                    held = shares * close;
                }

                value[i] = held;
                paid[i] = invested;
            }

            tracks.Add(new DcaTrack(walk.Code, walk.Name, value, paid, first, last, buys));
        }

        return new DcaBoard(dates, tracks, amount, frequency, skipped);
    }
}
