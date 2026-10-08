using System.Globalization;
using System.Numerics;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// What both multi-instrument candle frames are drawn with: the percentage axis, the curve, and
/// the label riding its leading end.
///
/// Here rather than in either of them because they are two layouts of one picture, and the
/// furniture is not what a layout decides. <see cref="CandleRaceRenderer"/> puts every curve on
/// one axis; <see cref="CandleSplitRenderer"/> gives each its own panel and its own axis, and
/// draws this same label once per panel. A second copy of the label arithmetic would be a second
/// place its collision rule could be got wrong, and the two frames would drift apart while each
/// still looked right on its own — the drift `one-render-path.mdc` exists to prevent.
/// </summary>
public static class CandleLine
{
    /// <summary>What separates a label from the point it rides.</summary>
    public const double LabelGap = 12;

    /// <summary>How far inside the safe line a label stops, so its edge is not on the line.</summary>
    public const double LabelEdgePad = 12;

    /// <summary>Padding inside a label, left and right.</summary>
    public const double LabelPadX = 14;

    /// <summary>Padding above and below the text.</summary>
    public const double LabelPadY = 8;

    /// <summary>The least air between two labels stacked one above the other.</summary>
    public const double LabelBetween = 8;

    /// <summary>The label's own text size, in baseline pixels.</summary>
    public const double LabelSize = 22;

    /// <summary>How thick a label's border is.</summary>
    public const double LabelEdge = 3;

    /// <summary>
    /// The subtitle's row — which instruments, on what period — as a fraction of frame height,
    /// counted from the top of the frame and moved by the title block like every row under it.
    /// </summary>
    public const double SubtitleRow = 0.20;

    /// <summary>
    /// The title and the line under it, which both layouts draw the same way: the codes saying
    /// what is being compared, and the period.
    ///
    /// Capped at three codes and counted past that, because six upper-case codes under a title is
    /// a second title. The apart layout never reaches the cap — <see cref="CandleBoardLoader.MostPanels"/>
    /// is three — and passes through the same line rather than having one of its own.
    /// </summary>
    public static void Header(
        CanvasDrawingSession session, FrameContext context, TitleBlock title,
        CandleBoard board, string resolved, bool showTitle, int titleLines, double t)
    {
        var a = Easing.Ramp(t, 0, 1000);

        title.Draw(session, context, resolved, title.For(session, resolved, context, showTitle), Palette.Title, a);

        using var small = Ink.Format(context.Px(25));

        var codes = board.Tracks.Select(track => track.Code.ToUpperInvariant()).Take(3).ToList();

        if (board.Tracks.Count > codes.Count)
        {
            codes.Add("+" + (board.Tracks.Count - codes.Count).ToString(CultureInfo.InvariantCulture));
        }

        Ink.Centred(
            session,
            Strings.Format("CandleSubtitleLine",
                string.Join(" / ", codes),
                Strings.Get(CandleLoader.NameKey(board.Period))),
            context.Width / 2, context.HeaderRow(SubtitleRow, titleLines), small, Palette.Muted, a);
    }

    /// <summary>
    /// How much of the host's button rail the frame now being drawn keeps clear: the same fraction,
    /// and the same reason for it being a fraction rather than a flag, as the three pages that offer
    /// the choice — a scrolling frame is a window while it rolls and only becomes the whole range as
    /// it opens out at the end, and the reservation has to open with it.
    /// </summary>
    public static double GiveWay(double t, AnimationPlan plan, CandleMotion motion, bool crossSafeRight)
    {
        if (!crossSafeRight)
        {
            return 1;
        }

        return motion is CandleMotion.Scroll
            ? 1 - Easing.Ramp(t, plan.FinaleStartMs, AnimationPlan.OpenOutMs)
            : 0;
    }

    /// <summary>
    /// A percentage the same way in every locale, with its sign always shown.
    ///
    /// Always signed because the sign is the measurement — a board of figures that each have to
    /// be read for direction is a board read twice, and the inside of a comparison is the worst
    /// place to make a reader do it.
    /// </summary>
    public static string Percent(double value) =>
        (value >= 0 ? "+" : "-") + Math.Abs(value).ToString("0.##", CultureInfo.InvariantCulture) + "%";

    /// <summary>
    /// The axis: a horizontal line per step, with its figure just left of the plot.
    ///
    /// The zero line is the one that matters and is drawn as such — brighter, thicker, and
    /// labelled in the muted tone rather than in the axis tone, so that the line the whole
    /// comparison is read against is the line the eye lands on.
    /// </summary>
    /// <param name="level">A value's y, in frame pixels — the panel's own scale, not the frame's.</param>
    /// <param name="size">The axis figures' size: the one axis of a comparison, or a smaller one in each panel.</param>
    /// <param name="width">
    /// How far the lines reach — the axis of a comparison stops short of its label column, a
    /// panel's runs the panel's own width.
    /// </param>
    public static void Axis(
        CanvasDrawingSession session, FrameContext context,
        double lo, double hi, double step, Func<double, double> level,
        double width, double opacity, double size = 20)
    {
        var mx = context.ChartLeft;
        var line = (float)Math.Max(1, context.Px(1));

        using var format = Ink.Format(context.Px(size));

        for (var v = lo; v <= hi + 1e-9; v += step)
        {
            var y = level(v);
            var zero = Math.Abs(v) < 1e-9;

            session.DrawLine(
                new Vector2((float)mx, (float)y),
                new Vector2((float)(mx + (width * opacity)), (float)y),
                zero ? Palette.AxisLabel : Palette.Grid,
                zero ? Math.Max((float)context.Px(2), line) : line);

            Ink.RightMiddle(
                session, Percent(v), mx - context.Px(12), y,
                format, zero ? Palette.Muted : Palette.AxisLabel, opacity);
        }
    }

    /// <summary>
    /// The name and the figure, riding each curve's leading end.
    ///
    /// Placed in one pass and drawn in another, because the boxes have to be kept apart from each
    /// other and that cannot be decided one at a time: two instruments that ended the range a
    /// fraction apart put their labels in the same place, and the one drawn second covers the
    /// first — a frame with the right number of labels on it and one of them missing.
    ///
    /// <paramref name="top"/> and <paramref name="bottom"/> are the band the labels have to stay
    /// inside: the frame's own plot for a comparison, one panel's for the split frame, whose
    /// labels must not cross into the panel above or below.
    /// </summary>
    public static void EndLabel(
        CanvasDrawingSession session, FrameContext context,
        IReadOnlyList<((double X, double Y)[] Points, Color Colour, string Name, double Value)> lines,
        IReadOnlyList<(double X, double Y)> anchors,
        double top, double bottom, double opacity, double giveWay)
    {
        if (lines.Count == 0)
        {
            return;
        }

        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var size = context.Px(LabelSize);

        using var probe = new CanvasTextLayout(session, "0", valueFormat, 0, 0);
        var height = probe.LayoutBounds.Height + context.Px(LabelPadY * 2);

        var boxes = new List<Rect>(lines.Count);

        for (var i = 0; i < lines.Count; i++)
        {
            var (_, _, name, value) = lines[i];

            var width = LabelWidth(session, context, nameFormat, valueFormat, name, value);

            // Its right edge is the one that gives way, and it gives way to the **safe
            // line** rather than to the frame's edge: past that line is the band the
            // platform covers with its avatar and its comment button.
            var left = Math.Min(
                anchors[i].X + context.Px(LabelGap),
                context.SafeRight(giveWay) - context.Px(LabelEdgePad) - width);

            boxes.Add(new Rect(Math.Max(context.ChartLeft, left), anchors[i].Y, width, height));
        }

        var order = Enumerable.Range(0, boxes.Count).OrderBy(i => boxes[i].Y).ToArray();
        var centres = boxes.Select(b => b.Y).ToArray();
        var gap = context.Px(LabelBetween);

        for (var j = 1; j < order.Length; j++)
        {
            var previous = order[j - 1];
            var here = order[j];

            if (centres[here] < centres[previous] + height + gap)
            {
                centres[here] = centres[previous] + height + gap;
            }
        }

        if (order.Length > 0)
        {
            var lowest = centres[order[^1]] + (height / 2);

            if (lowest > bottom)
            {
                var shift = lowest - bottom;

                for (var i = 0; i < centres.Length; i++)
                {
                    centres[i] -= shift;
                }

                var highest = centres[order[0]] - (height / 2);

                if (highest < top)
                {
                    var push = top - highest;

                    for (var i = 0; i < centres.Length; i++)
                    {
                        centres[i] += push;
                    }
                }
            }
        }

        for (var i = 0; i < boxes.Count; i++)
        {
            var (_, colour, name, value) = lines[i];
            var box = new Rect(boxes[i].X, centres[i] - (height / 2), boxes[i].Width, height);
            var radius = (float)(height / 2);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, 0.92 * opacity));
            session.DrawRoundedRectangle(box, radius, radius, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(LabelEdge));

            Ink.Runs(
                session,
                [
                    (name + " ", Palette.Muted, nameFormat),
                    (Percent(value), colour, valueFormat),
                ],
                box.X + (box.Width / 2),
                box.Y + (height / 2) + (size * 0.36),
                opacity);
        }
    }

    /// <summary>How wide a label would be, in the face it is drawn in.</summary>
    public static double LabelWidth(
        CanvasDrawingSession session, FrameContext context,
        CanvasTextFormat nameFormat, CanvasTextFormat valueFormat,
        string name, double value)
    {
        return Ink.Advance(session, name + " ", nameFormat)
               + Ink.Advance(session, Percent(value), valueFormat)
               + context.Px(LabelPadX * 2);
    }

    /// <summary>
    /// How much of the frame's right-hand side the end labels need: the amount the plot gives up
    /// so a label can ride ahead of its own curve and come to rest short of the band the host's
    /// interface covers.
    ///
    /// Measured from the **final** percentages rather than from this frame's, so the column is the
    /// same width on every frame — one that grew with the figures would narrow the plot while the
    /// labels were still moving along it. And measured across *all* the labels, which is what makes
    /// the apart frame's panels line up: one column for the whole frame means one plot width, and a
    /// date that is at one x in the top panel is at the same x in the bottom one.
    /// </summary>
    /// <param name="labels">Every label that will be drawn, as its name and its final figure.</param>
    /// <param name="giveWay">How much of the host's button rail the frame keeps clear.</param>
    public static double LabelColumn(
        CanvasDrawingSession session, FrameContext context,
        IReadOnlyList<(string Name, double Value)> labels, double giveWay)
    {
        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var widest = 0d;

        foreach (var label in labels)
        {
            widest = Math.Max(
                widest, LabelWidth(session, context, nameFormat, valueFormat, label.Name, label.Value));
        }

        var need = context.RightLabelColumn(
            widest, context.Px(LabelGap + LabelEdgePad), giveWay);

        return Math.Clamp(need, 0, context.ChartWidth * 0.45);
    }

    /// <summary>
    /// The date row under the plot: one label per few points, arriving with the point it belongs
    /// to rather than with the frame.
    ///
    /// Drawn once per frame, under the **bottom** panel in the apart layout, because the axis it
    /// labels is shared: three panels each carrying the same dates would be the same row printed
    /// three times, and two of those rows would sit in the middle of the picture.
    /// </summary>
    public static void XLabels(
        CanvasDrawingSession session, FrameContext context,
        CandleBoard board, AnimationPlan plan, double t, double bottom, double plotW,
        double introA, double count, double first, double head)
    {
        var n = board.Count;
        var mx = context.ChartLeft;

        var whole = Math.Max(1, (int)Math.Round(count));

        var every = Math.Max(1, whole / 5);
        if (whole % every == 0 && whole / every > 5)
        {
            every = Math.Max(1, (whole / 6) + 1);
        }

        // A year across a span of years, a year-and-month across less; on a single session
        // it is the clock, which is what that axis counts in.
        var years = board.End.DayNumber - board.Start.DayNumber > 365 * 3;

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < n; i += every)
        {
            if (i < first || i > head)
            {
                continue;
            }

            var a = Easing.Ramp(t, plan.IntroMs + (i * plan.StaggerMs), 450) * introA;
            if (a <= 0)
            {
                continue;
            }

            var stamp = board.Stamps[i];
            var text = board.Intraday ? stamp : years ? stamp[..4] : stamp[..7];
            var x = mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

            Ink.Centred(session, text, x, bottom + context.Px(28), format, Palette.DateLabel, a);
        }
    }

    /// <summary>One curve, drawn through its points.</summary>
    public static void Curve(
        CanvasDrawingSession session, FrameContext context,
        (double X, double Y)[] points, Color colour, double opacity)
    {
        if (points.Length < 2)
        {
            return;
        }

        var shape = new Vector2[points.Length];

        for (var i = 0; i < points.Length; i++)
        {
            shape[i] = new Vector2((float)points[i].X, (float)points[i].Y);
        }

        using var geometry = Polyline(session, shape);

        session.DrawGeometry(geometry, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(3));
    }

    /// <summary>A path through the points, open at both ends: a curve, not a filled ring.</summary>
    private static CanvasGeometry Polyline(CanvasDrawingSession session, Vector2[] points)
    {
        using var builder = new CanvasPathBuilder(session);

        builder.BeginFigure(points[0]);

        for (var i = 1; i < points.Length; i++)
        {
            builder.AddLine(points[i]);
        }

        builder.EndFigure(CanvasFigureLoop.Open);

        return CanvasGeometry.CreatePath(builder);
    }
}
