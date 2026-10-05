namespace MarketMotionStudio.Render;

/// <summary>
/// The pacing of one bar-growth animation, derived from its length and how many bars
/// it has to get through.
///
/// Every figure here is lifted from the browser tool this replaces rather than chosen
/// again, because the pacing is the part that was tuned by watching. Times are in
/// milliseconds because that is the unit those constants were written in; the
/// renderer converts from <see cref="FrameContext.Progress"/> on the way in.
/// </summary>
public sealed record AnimationPlan(
    double TotalMs,
    double IntroMs,
    double FinaleStartMs,
    double BarMs,
    double StaggerMs,
    double AxisStep,
    double AxisTop)
{
    /// <summary>
    /// Works out the pacing.
    ///
    /// The shape: a short opening while the titles fade in, a main stretch where the
    /// bars grow one after another, and a closing stretch where the average line, the
    /// extremes and the statistics arrive. The opening and closing are taken out of the
    /// total first and the bars share what is left, which is why changing the duration
    /// re-times the whole thing rather than trimming the end.
    /// </summary>
    public static AnimationPlan For(TimeSpan duration, int barCount, double peak)
    {
        var total = duration.TotalMilliseconds;

        // Capped as well as proportional. On a three-minute video four per cent would be
        // seven seconds of a static title, which is longer than anyone waits.
        var intro = Math.Min(2500, total * 0.04);

        // Clamped at both ends: the closing has fixed content to get through, so it
        // cannot be proportionally tiny on a short video, and does not need to be
        // proportionally huge on a long one.
        var finale = Math.Clamp(total * 0.10, 3000, 8000);

        var growSpan = total - intro - finale;

        // Each bar's own growth overlaps its neighbours'. The 2.2 makes a bar's rise
        // last a little over twice its slot, so several are visibly in motion at once —
        // at 1.0 they would rise strictly one at a time and the chart would look like it
        // was being filled in by hand.
        var barMs = Math.Min(1800, Math.Max(260, growSpan / Math.Max(1, barCount) * 2.2));

        // The last bar must *finish* at the end of the growth stretch, not start there,
        // which is why its own duration comes off before the spacing is divided.
        var stagger = barCount > 1 ? (growSpan - barMs) / (barCount - 1) : 0;

        var (step, top) = NiceScale(peak * 1.06, 5);

        return new AnimationPlan(total, intro, total - finale, barMs, stagger, step, top);
    }

    /// <summary>
    /// How long a scrolling window takes to open out into the whole range at the end of
    /// the closing stretch; see <see cref="Window"/>.
    ///
    /// Well inside that stretch rather than all of it: the stretch is at least three
    /// seconds long, and the closing cards do not start arriving until nearly two
    /// seconds into it. Opening first means they arrive on a frame that already shows
    /// the whole range, rather than on one still widening underneath them.
    /// </summary>
    public const double OpenOutMs = 900;

    /// <summary>
    /// The stretch of the axis one frame is looking at: how many positions it holds,
    /// where its right edge has reached, and where its left one therefore is.
    ///
    /// The three pages that offer a choice of motion used to work this out in their own
    /// renderer, in the same three lines each. A change made to one of them is then a
    /// change that has to be made to all three, or the pages quietly disagree about what
    /// a motion is — and the frames keep looking right, because each page agrees with
    /// itself. So it lives here, beside the pacing it is read off.
    /// </summary>
    /// <param name="scroll">Whether the frame is scrolling rather than growing.</param>
    /// <param name="window">How many positions the scrolling window holds.</param>
    /// <param name="span">How many positions the whole range has.</param>
    /// <param name="reached">
    /// How far the animation has come along the axis. Fractional, because the point
    /// arriving now is part of the way into place.
    /// </param>
    /// <param name="t">The frame's time, in milliseconds.</param>
    public (double Count, double Head, double First) Window(
        bool scroll, int window, int span, double reached, double t)
    {
        // Growing is a window as long as the range, which is why the two motions share
        // every line of drawing that follows this.
        if (!scroll)
        {
            return (span, reached, 0);
        }

        // The window as the motion runs it: `held` positions, its right edge as far
        // forward as the animation has come but never short of a full window — which is
        // what keeps the opening frames from being three points stretched across the
        // frame. The right edge leads the arrival by the part of the arriving point that
        // has come through, so the window is already sliding while that point is still
        // growing into place: a roll rather than a step per day.
        var held = Math.Min(Math.Max(2, window), span);
        var edge = Math.Max(reached, held - 1);

        // The closing stretch opens the window out. Its left edge walks back to the
        // start of the range and its right one settles on the range's last position, so
        // the frame the animation ends on is the whole span rather than the last few
        // years of it. Scrolling answers "what did it look like at the time"; the frame
        // a video stops on answers "what did the whole stretch look like", and stopping
        // on a window answers only the first of those.
        var wide = Easing.Ramp(t, FinaleStartMs, OpenOutMs);

        var head = edge + ((span - 1 - edge) * wide);
        var first = (edge - held + 1) * (1 - wide);

        // Count is read off the two edges rather than interpolated alongside them. The
        // three have to agree — `Count == Head - First + 1` — because a point is placed
        // by its position between them: a count that drifted would push the last point
        // past the plot's right edge while the window was opening, and by the time the
        // window had finished opening the frame would look normal again with nothing
        // left to say what had happened.
        return (head - first + 1, head, first);
    }

    /// <summary>
    /// A round axis step at or above <c>max / ticks</c>, and the top of the axis as a
    /// whole multiple of it.
    ///
    /// Rounded to 1, 2, 2.5, 5 or 10 times a power of ten, because those are the
    /// intervals people read without doing arithmetic. An axis labelled in steps of
    /// 1,732 is accurate and useless.
    ///
    /// Public because the per-stock page scales each of its two panels independently —
    /// one step for the whole frame would mean the two panels' grids disagreed with
    /// their own data, which reads as one of them being wrong.
    /// </summary>
    public static (double Step, double Top) NiceScale(double max, int ticks)
    {
        if (max <= 0)
        {
            return (1, 1);
        }

        var raw = max / ticks;
        var magnitude = Math.Pow(10, Math.Floor(Math.Log10(raw)));
        var n = raw / magnitude;

        var step = (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * magnitude;

        return (step, Math.Ceiling(max / step) * step);
    }
}

/// <summary>
/// The easing curves the animation uses, and the reason there are two.
/// </summary>
public static class Easing
{
    /// <summary>
    /// Overshoots slightly and settles back, which is what gives a bar its flick as it
    /// arrives.
    ///
    /// The overshoot is deliberately gentler than the textbook figure — 1.1 against the
    /// usual 1.70158. With a hundred bars rising at once a strong overshoot reads as
    /// wobble rather than as snap.
    /// </summary>
    public static double OutBack(double x)
    {
        const double C1 = 1.1;
        const double C3 = C1 + 1;

        return 1 + (C3 * Math.Pow(x - 1, 3)) + (C1 * Math.Pow(x - 1, 2));
    }

    /// <summary>
    /// Decelerates without overshooting, for anything monotonic.
    ///
    /// A cumulative total must never appear to go backwards: <see cref="OutBack"/> on a
    /// running total draws it exceeding its own final value and then retreating, which
    /// looks like the data being corrected rather than like an animation.
    /// </summary>
    public static double OutCubic(double x) => 1 - Math.Pow(1 - x, 3);

    /// <summary>Progress through a window, clamped — the shape every fade here uses.</summary>
    public static double Ramp(double t, double from, double span) =>
        span <= 0 ? (t >= from ? 1 : 0) : Math.Clamp((t - from) / span, 0, 1);
}
