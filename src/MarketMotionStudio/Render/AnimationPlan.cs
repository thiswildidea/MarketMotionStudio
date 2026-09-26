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
