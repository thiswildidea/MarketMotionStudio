using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The axis a span of days is drawn on.
///
/// <para>
/// A day's minutes are already a good axis: they run 09:30 to 15:00 with a hole where the
/// market ate lunch, and a hole on an axis is a fact about the day. A hundred and twenty of
/// them are not — twenty thousand minutes of which some four thousand contain a price, with
/// nights and weekends between. Drawing a year on that axis puts December's curve two pixels
/// from November's and leaves eighty-one per cent of the frame empty.
/// </para>
///
/// <para>
/// **So the span's axis is the samples themselves, evenly.** One slot per sample, whatever
/// the sample is: a day's close, or a minute inside a day. What that costs — a week's
/// overnight gap being as wide as an hour inside Tuesday — is exactly what the clock axis
/// already charges for its own lunch break, and buys a curve whose horizontal speed is
/// proportional to nothing but the counting of prices, which is what a reader measures by eye.
/// </para>
///
/// <para>
/// This is the same object for every span because it is the answer to one question, posed
/// twice a frame: *what does this position on the axis say?* Below it every renderer keeps
/// working off minutes it has always asked for, and because those minutes are now slot numbers
/// nothing downstream had to learn a second vocabulary.
/// </para>
/// </summary>
/// <param name="Slots">Each position, and which day and minute of real time it stands for.</param>
/// <param name="Labels">What to print under the positions that carry a date.</param>
/// <param name="Ticks">The positions to print labels at — five, or fewer.</param>
public sealed record SpanAxis(
    IReadOnlyList<(DateOnly Day, int Minute)> Slots,
    IReadOnlyDictionary<int, string> Labels,
    IReadOnlyList<int> Ticks);

/// <summary>
/// Turns what the returns engine answers into the one shape this app's frames already draw.
///
/// <para>
/// **Not a second pipeline.** The frames below were built around a session of minutes, and every
/// one of the things they ask of it — a first position, a last one, a high water mark and its
/// position, what is worth what at each point — a span has too, differently measured. Adapting
/// costs one file; duplicating would cost two engines for one definition of profit, and they
/// would drift, which is the failure that never announces itself.
/// </para>
///
/// <para>
/// **A slot's number is the samples' own order.** Not a counter that has to be reconciled with
/// the curve, and not a time: the hundred-and-fortieth sample of a year's closes is the
/// hundred-and-fortieth position, which is also where every other series on the frame has put
/// it. Two lines plotted on one axis by their own arithmetic would be two lines that disagree
/// about where Tuesday is.
/// </para>
/// </summary>
public static class SpanFrame
{
    /// <summary>
    /// How many date labels an axis carries before they start printing over each other.
    ///
    /// Measured rather than guessed: five labels across the narrowest frame this app publishes
    /// leave each its own width of clear space at the caption size every frame uses.
    /// </summary>
    private const int MostTicks = 5;

    /// <summary>
    /// Builds the axis one span is drawn on, and names its ticks.
    ///
    /// Every position that opens a new trading day is a candidate — a day is the unit a reader
    /// asks about a span — and the candidates are thinned to <see cref="MostTicks"/> rather than
    /// every one being printed. The first and last always survive: an axis whose ends are not
    /// named does not say what it spans.
    /// </summary>
    public static SpanAxis AxisFor(ReturnHistory history)
    {
        var slots = new List<(DateOnly Day, int Minute)>(history.Samples.Count);
        var labels = new Dictionary<int, string>();
        var candidates = new List<int>();

        // **One day is a clock, not a calendar.** A single session announces no new days, so the
        // date rule below printed "10/30" once in the corner and left the rest of the axis empty.
        // Its ticks belong on times, the way the intraday page has always drawn them.
        if (history.From == history.To && history.Grain == ReturnGrain.Session)
        {
            // **Slots are filled here too.** They read as redundant on a single day — the labels
            // and ticks below are clock times, and the session keeps its own minutes — but the
            // index half of the 双屏 page places its prices *by* them: an empty list reads as "no
            // positions on the axis" and the whole board comes back unfetched (实测：10/26 单日
            // 区间「取到 0 / 3 个指数」，下半屏只剩「未选指数」).
            for (var i = 0; i < history.Samples.Count; i++)
            {
                slots.Add((history.Samples[i].Day, history.Samples[i].Minute));
            }

            var picks = Thin([.. Enumerable.Range(0, history.Samples.Count)]);
            var clock = new Dictionary<int, string>();

            foreach (var i in picks)
            {
                clock[history.Samples[i].Minute] = PortfolioSession.Clock(history.Samples[i].Minute);
            }

            return new SpanAxis(slots, clock, [.. picks.Select(i => history.Samples[i].Minute)]);
        }

        var seen = DateOnly.MinValue;

        for (var i = 0; i < history.Samples.Count; i++)
        {
            var sample = history.Samples[i];

            slots.Add((sample.Day, sample.Minute));

            if (sample.Day == seen)
            {
                continue;
            }

            seen = sample.Day;

            candidates.Add(i);
            labels[i] = sample.Day.ToString("M/d", CultureInfo.InvariantCulture);
        }

        return new SpanAxis(slots, labels, Thin(candidates));
    }

    /// <summary>
    /// Keeps the ends and thins the middle of a run of candidate positions.
    ///
    /// Even thinning rather than every-nth-day: a thirty-day month thinning to one label a week
    /// puts them on the 1st, 8th, 15th, 22nd and 29th, so the *last* label is the month's last
    /// trading day rather than whichever one division happened to spare.
    /// </summary>
    private static IReadOnlyList<int> Thin(IReadOnlyList<int> candidates)
    {
        if (candidates.Count <= MostTicks)
        {
            return [.. candidates];
        }

        var picked = new List<int>(MostTicks);

        for (var i = 0; i < MostTicks; i++)
        {
            var at = i * (candidates.Count - 1) / (MostTicks - 1);
            var slot = candidates[at];

            if (picked.Count == 0 || picked[^1] != slot)
            {
                picked.Add(slot);
            }
        }

        return picked;
    }

    /// <summary>
    /// One span, written out as the session every frame below already reads.
    ///
    /// <paramref name="axis"/> comes from the same history, made by <see cref="AxisFor"/>, so the
    /// frame's curve, its moments and the index lines riding beside it are counted off one set of
    /// positions rather than three.
    /// </summary>
    public static PortfolioSession ToSession(ReturnHistory history, SpanAxis axis)
    {
        // **One session keeps its own clock.** A span numbers its samples by position, because its
        // axis is a run of samples rather than a run of minutes. A single day *is* a run of
        // minutes, and numbering it by position made the frame print 05:31 for the last of 332
        // samples (331 minutes after midnight) instead of 15:00 (实测：读者截图 `05:31`). One day
        // wide keeps its minutes everywhere — clock, axis, markers and the list then agree with the
        // intraday page instead of drifting off it.
        var single = history.From == history.To && history.Grain == ReturnGrain.Session;

        int At(int i) => single ? history.Samples[i].Minute : i;

        var samples = new List<PnlSample>(history.Samples.Count);

        for (var i = 0; i < history.Samples.Count; i++)
        {
            samples.Add(new PnlSample(At(i), history.Samples[i].Pnl, history.Samples[i].Value));
        }

        return new PortfolioSession(
            Label(history),
            OpenMinute: samples.Count > 0 ? samples[0].Minute : 0,
            CloseMinute: samples.Count > 0 ? samples[^1].Minute : 0,
            Samples: samples,
            Moments: Moments(history, single),
            Holdings: history.Rows
                .Select(row => new PnlHolding(
                    row.Code,
                    row.Name,
                    row.Shares,
                    row.Opening,
                    row.Cost,
                    row.Opened,
                    row.Last,
                    row.Pnl,
                    row.Value,
                    row.Priced))
                .ToList(),
            Last: history.Last,
            Peak: history.Peak,
            Trough: history.Trough,
            PeakMinute: Extremum(history, best: true, single),
            TroughMinute: Extremum(history, best: false, single),
            Value: history.EndValue,
            PrevValue: history.StartEquity,
            HkdCny: history.HkdCny,
            TradeCount: history.Fills.Count,

            // **The fills themselves, not just how many there were.** The frame prints 成交 N 笔 and
            // draws a marker on the sample each fill landed on; both read `Trades`, and an empty
            // list here meant a span could carry a dozen fills and still say 成交 0 笔 with no
            // markers at all (实测：10/30 买了 11,300 股超图，画面写着成交 0 笔).
            Trades: [.. history.Fills.Select(f => new PnlTrade(
                f.Trade.Code, f.Trade.Name, f.Trade.Side, f.Trade.Price, f.Trade.Shares, At(f.Slot)))],
            Closed: history.Unpriced,
            FetchedAt: history.FetchedAt,
            Opening: history.Opening,
            OpeningCosts: history.OpeningCosts)
        {
            SlotLabels = axis.Labels,
            SlotTicks = axis.Ticks,
            SlotIsDaily = history.Grain == ReturnGrain.Daily,
            SingleDay = single,
        };
    }

    /// <summary>
    /// What the frame says it is looking at: the range actually drawn.
    ///
    /// The requested range rather than the answer, silently corrected — a request for a year
    /// against a snapshot three weeks old draws three weeks, and a frame that called that year
    /// would be the one number on it the reader could check and find wanting. Where the two agree
    /// it is one day, printed once.
    /// </summary>
    private static string Label(ReturnHistory history) =>
        history.From == history.To
            ? history.From.ToString("M/d", CultureInfo.InvariantCulture)
            : history.From == DateOnly.MinValue
                ? Strings.Get("SpanRangeUnset")
                : Strings.Format("SpanRange",
                    history.From.ToString("M/d", CultureInfo.InvariantCulture),
                    history.To.ToString("M/d", CultureInfo.InvariantCulture));

    /// <summary>
    /// The book, point by point, alongside the curve — which is why the list under the curve
    /// changes as it plays: a position sold in the range stops being counted where it was sold
    /// rather than at the start of the picture.
    ///
    /// <para>
    /// **What a position has contributed is the change in what it is carrying less what it cost.**
    /// Not its profit against the year's open, which for a purchase made inside the range would
    /// open on a number belonging to somebody else, and not the engine's own number either: that
    /// one is range-wide where this is asked minute by minute. Measured in yuan, after the rate,
    /// which is the unit the line above these rows is drawn in.
    /// </para>
    /// </summary>
    private static List<PnlMoment> Moments(ReturnHistory history, bool single)
    {
        var moments = new List<PnlMoment>(history.Moments.Count);

        if (history.Moments.Count == 0)
        {
            return moments;
        }

        // Pass one: what each position was carrying against its own cost at the range's first
        // point, which is where every contribution has to be measured *from*. A purchase made on
        // the third day of a month has no business opening the month's picture on its own profit.
        var opening = history.Moments[0];
        var before = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);

        foreach (var code in opening.Shares.Keys)
        {
            before[code] = Carried(history, opening, code);
        }

        foreach (var moment in history.Moments)
        {
            var contributions = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
            var codes = moment.Shares.Keys
                .Concat(before.Keys)
                .Distinct(StringComparer.OrdinalIgnoreCase);

            foreach (var code in codes)
            {
                contributions[code] = Carried(history, moment, code) -
                    (before.TryGetValue(code, out var was) ? was : 0);
            }

            moments.Add(new PnlMoment(
                single ? moment.Minute : moments.Count,
                moment.Shares, moment.Costs, moment.Marks, contributions));
        }

        return moments;
    }

    /// <summary>
    /// What one position is carrying against its own diluted cost at one point, in yuan.
    ///
    /// A position sold out mid-range is carrying nothing, which is also what it contributed from
    /// there on — the sale's own money already belongs to whichever point it happened at.
    /// </summary>
    private static double Carried(ReturnHistory history, ReturnMoment moment, string code)
    {
        var shares = moment.Shares.TryGetValue(code, out var held) ? held : 0;

        if (shares <= 0)
        {
            return 0;
        }

        var cost = moment.Costs.TryGetValue(code, out var bought) ? bought : 0;
        var mark = moment.Marks.TryGetValue(code, out var price) ? price : 0;

        return shares * (mark - cost) * Rate(history, code);
    }

    /// <summary>
    /// The rate one code's money is read in: dollars for a Hong Kong listing, one for everything
    /// else. <see cref="ReturnHistory.HkdCny"/> is zero for a book with no such row, and a rate
    /// nobody asked for would quietly move every mainland figure on the frame.
    /// </summary>
    private static double Rate(ReturnHistory history, string code) =>
        code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) && history.HkdCny > 0
            ? history.HkdCny
            : 1;

    /// <summary>Where the curve's best and worst points are, in slots rather than minutes.</summary>
    private static int Extremum(ReturnHistory history, bool best, bool single)
    {
        var at = 0;

        for (var i = 1; i < history.Samples.Count; i++)
        {
            var better = best
                ? history.Samples[i].Pnl > history.Samples[at].Pnl
                : history.Samples[i].Pnl < history.Samples[at].Pnl;

            if (better)
            {
                at = i;
            }
        }

        return single ? history.Samples[at].Minute : at;
    }
}
