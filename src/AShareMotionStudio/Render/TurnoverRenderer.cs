using System.Globalization;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Windows.Foundation;

namespace AShareMotionStudio.Render;

/// <summary>
/// Everything the two whole-market forms share: the background, the title block with its
/// running total, the four closing statistic cards, the credit and the progress bar.
///
/// The forms differ only in how the days themselves are drawn — as bars racing along a time
/// axis, or as calendar cells lighting up month by month — so that is the one abstract member.
/// Both are ports of `ashare_turnover_studio.html`, which has exactly this shape: a shared
/// `drawHeader` / `drawStats` / `drawProgress` and a branch in `renderFrame` on the chosen view.
///
/// Stateless with respect to time, per `one-render-path.mdc`: every frame comes from
/// <see cref="FrameContext.Progress"/> alone.
/// </summary>
public abstract class TurnoverRenderer(TurnoverSeries series, AnimationPlan plan, Metric metric)
    : IFrameRenderer
{
    /// <summary>
    /// Distance from the chart baseline down to the credit, in baseline pixels. The date labels
    /// and the four statistic cards live in this band, and both forms reserve the same amount so
    /// that switching between them does not move the lower stack.
    /// </summary>
    public const double CreditGap = 278;

    /// <summary>Distance from the credit up to the top of the statistic cards.</summary>
    private const double CardsAboveCredit = 192;

    /// <summary>
    /// Where the plot area starts, as a fraction of frame height.
    ///
    /// A fraction rather than a measurement below the title block, which is how the source does
    /// it, and the two are not interchangeable: the title block ends with a 128-pixel running
    /// total positioned at 0.354, so the plot begins just under it at 0.377. Stacking row heights
    /// instead would make the gap drift whenever a row's font changed.
    ///
    /// Read through <see cref="Row"/>, never multiplied out directly — the user's top margin
    /// shifts the header block and the plot together, and a hidden title lifts both by one row;
    /// a renderer that multiplied here would leave the plot behind when either happened.
    /// </summary>
    protected const double PlotTopFraction = 0.377;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Whether the title row is drawn at all.
    ///
    /// Off is a supported choice, not an error state: the whole point of the switch is a
    /// frame with just the number on it. What hiding does is hand the title's row back —
    /// every row below shifts <em>up</em> by exactly <see cref="FrameContext.TitleRowHeight"/>
    /// through <see cref="Row"/>, the bottom margin holds the lower edge still, so the plot
    /// grows by one row and unchecking restores the previous layout exactly.
    /// </summary>
    public bool ShowTitle { get; set; } = true;

    /// <summary>
    /// A header row of this indicator's layout, stated as a fraction of frame height the way the
    /// source HTML stated it: the top margin's shift plus the title row's absence, in one place.
    ///
    /// Delegates to <see cref="FrameContext.HeaderRow"/> so both indicator pages apply the same
    /// two adjustments by the same arithmetic — a renderer that multiplied the fraction itself
    /// would leave the plot behind when the header moved.
    /// </summary>
    protected double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, ShowTitle);

    protected TurnoverSeries Series => series;

    protected AnimationPlan Plan => plan;

    /// <summary>Which metric this frame is drawing, and everything that follows from it.</summary>
    protected Metric Metric => metric;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * plan.TotalMs;

        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height), Palette.Background);

        // The plot owns everything between the background and the statistics, including its own
        // closing annotations — the two forms mark their extremes differently, one boxing a bar
        // and one boxing a calendar cell.
        var (index, value) = DrawPlot(session, context, t);

        DrawStats(session, context, t);
        DrawHeader(session, context, t, index, value);
        DrawProgress(session, context, t);
    }

    /// <summary>
    /// Draws the days, and says which one the header should be reading out: the one currently
    /// arriving, or the last one that finished.
    /// </summary>
    protected abstract (int Index, double Value) DrawPlot(
        CanvasDrawingSession session, FrameContext context, double t);

    /// <summary>
    /// The four summary cards and the credit, which arrive last.
    /// </summary>
    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var cards = metric.Cards(series);
        var left = context.ChartLeft;
        var gap = context.Px(14);
        var cardWidth = (context.ChartWidth - (gap * 3)) / 4;
        var cardHeight = context.Px(132);
        var y = context.CreditLine - context.Px(CardsAboveCredit);

        using var labelFormat = Ink.Format(context.Px(22));
        using var valueFormat = Ink.Format(context.Px(34), bold: true);

        for (var i = 0; i < cards.Length; i++)
        {
            var x = left + (i * (cardWidth + gap));
            var box = new Rect(x, y, cardWidth, cardHeight);
            var radius = (float)context.Px(14);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, a));
            session.DrawRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardStroke, a), (float)context.Px(1.5));

            Ink.Centred(session, cards[i].Label, x + (cardWidth / 2), y + context.Px(42), labelFormat, Palette.Muted, a);
            Ink.Centred(session, cards[i].Value, x + (cardWidth / 2), y + context.Px(92), valueFormat, Palette.CardValue, a);
        }

        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(
            session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    /// <summary>
    /// The title block: the headline, what is being summed, the range, and the running total as
    /// the animation advances.
    /// </summary>
    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t, int movingIndex, double movingValue)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        // The whole block sits below the top safe area, plus whatever extra room the user's
        // top margin asked for, minus the title row if the title is hidden — every row goes
        // through Row, so the margin and the switch move the block as a unit and neither can
        // change the spacing inside it.
        var title = Title.Length > 0 ? Title : metric.DefaultTitle();

        if (ShowTitle)
        {
            var titleSize = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(titleSize, bold: true))
            {
                Ink.Centred(session, title, cx, Row(context, 0.155), format, Palette.Title, a);
            }
        }

        using var small = Ink.Format(context.Px(25));

        Ink.Centred(session, metric.Subtitle(series), cx, Row(context, 0.187), small, Palette.Muted, a);

        // The count of trading days is the one figure in this line anybody reads, so it is picked
        // out. Located inside the finished sentence rather than assembled from fragments — see
        // Ink.Highlighted for why that matters across languages.
        var count = series.Count.ToString(CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            // ISO, explicitly. Handing a DateOnly to a format string lets the current culture
            // pick, which rendered "6/24/2026" inside an otherwise Chinese frame — and a date in
            // a video is read by people in several locales.
            Ink.Highlighted(
                session,
                Strings.Format("TurnoverDaysLine", Iso(series.Dates[0]), Iso(series.Dates[^1]), count),
                count,
                Palette.Muted, Palette.Emphasis,
                small, strong,
                cx, Row(context, 0.214), a);
        }

        if (movingIndex < 0)
        {
            return;
        }

        using (var dateFormat = Ink.Format(context.Px(34)))
        {
            Ink.Centred(session, Iso(series.Dates[movingIndex]), cx, Row(context, 0.258), dateFormat, Palette.Moving, a);
        }

        // The running figure takes its colour from the value *being displayed* rather than from the
        // day's own, which matters while a bar is still growing: the number and its halo darken and
        // brighten with the bar they belong to instead of jumping to the final hue on frame one.
        var colour = metric.Colour(series, movingIndex);

        using (var bigFormat = Ink.Format(context.Px(128), bold: true))
        {
            var text = metric.Readout(movingValue);

            // Blurs the glyphs themselves, so the halo follows the digits. The number is the
            // largest thing on the frame and changes every frame, which is exactly where a
            // box-shaped approximation showed.
            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, colour));

            Ink.Centred(session, text, cx, Row(context, 0.327), bigFormat, colour, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, metric.Unit(), cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    /// <summary>
    /// A bar along the bottom edge showing how far through the video this frame is.
    ///
    /// Outside every margin on purpose: it is chrome for the viewer, not part of the chart, so it
    /// must not move when the chart is re-laid out.
    /// </summary>
    private void DrawProgress(CanvasDrawingSession session, FrameContext context, double t)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);
        var p = Math.Clamp(t / plan.TotalMs, 0, 1);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        // The ramp is measured across the whole width, not across the filled part, so the colour
        // at a given point is the colour that point will always have. Scaling the gradient to the
        // fill would make the bar change hue as it grew.
        Ink.FillHorizontal(
            session, new Rect(0, y, context.Width * p, height), Palette.ProgressFill, context.Width);
    }

    /// <summary>
    /// Whole 亿元 with comma-grouped thousands. The figures run to five digits and no decimal place
    /// of them is meaningful at this scale.
    /// </summary>
    /// <remarks>
    /// Invariant, not the interface's culture, and that is the source tool's choice rather than an
    /// oversight — it formats with an explicit `toLocaleString('en-US')`. Comma grouping is what
    /// this audience reads on a financial chart, and following the interface language instead would
    /// give "23.807" in German and "23 807" in Russian for the same series. Month and weekday names
    /// *do* follow the interface, because those are words rather than magnitudes.
    /// </remarks>
    public static string Round(double value) =>
        Math.Round(value).ToString("#,##0", CultureInfo.InvariantCulture);

    /// <summary>A date the same way in every locale.</summary>
    public static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
}
