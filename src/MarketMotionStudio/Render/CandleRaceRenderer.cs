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
/// Several instruments' candles on one frame, drawn as cumulative percentages so that
/// instruments of different prices can be read against each other.
///
/// This is the shape the single-instrument chart cannot take. Ten years of a share at
/// 1,600 beside ten years of an index at 3,800 is not two lines on one axis, it is one
/// line against the top of the frame and one flat against the bottom of it — a picture
/// of two price *levels*, whose vertical distance at any date means nothing. Percentages
/// are the only unit both can be drawn in, and the frame says so on its axis.
///
/// **Each instrument is named where a reader is already looking.** A legend above the
/// plot would have six names in a row for six curves, and the reader's eye is at the
/// moving end of the line, not in the corner — so the name rides its own curve's leading
/// end together with the figure it is ahead or behind by. That is also what makes the
/// labels the only possible answer to "which of these is which": six colours and a
/// legend asks the reader to hold a mapping in their head while the picture moves.
///
/// The percentage on a label is the curve's own at the moment being drawn, not its final
/// one — a label that disagreed with the line beside it would be worse than either.
/// </summary>
public sealed class CandleRaceRenderer : IFrameRenderer
{
    /// <summary>Distance from the chart baseline down to the credit: the date row alone.</summary>
    public const double CreditGap = 150;

    /// <summary>Where the plot area starts, as a fraction of frame height.</summary>
    private const double PlotTopFraction = 0.30;

    /// <summary>The subtitle — which instruments, on what period — under the title.</summary>
    private const double SubtitleRow = 0.20;

    // ---- the end label ------------------------------------------------------------------
    //
    // A rounded box riding each curve's leading end, carrying the instrument's name and how
    // far ahead or behind it is. The same furniture the holdings board uses, down to the
    // measurements: a reader who has watched one of these frames has already learned where
    // to look on the other.

    private const double LabelGap = 12;

    private const double LabelEdgePad = 12;

    private const double LabelPadX = 14;

    private const double LabelPadY = 8;

    private const double LabelBetween = 8;

    private const double LabelSize = 22;

    private const double LabelEdge = 3;

    private readonly CandleBoard _board;

    private readonly AnimationPlan _plan;

    private readonly CandleMotion _motion;

    private readonly int _window;

    private readonly bool _crossSafeRight;

    private readonly TitleBlock _title = new(62);

    /// <summary>How much of the host's button rail this frame keeps clear, set once per frame.</summary>
    private double _giveWay = 1;

    private int _titleLines;

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <param name="crossSafeRight">
    /// Whether the picture may run into the band the host covers with its button rail; the
    /// same choice, and the same reason for it being a fraction rather than a flag, as the
    /// three pages that offer it. Off here by default: a comparison's labels are wider than
    /// one instrument's, having a name in each, so this frame is the one that most needs the
    /// room it gives up.
    /// </param>
    public CandleRaceRenderer(
        CandleBoard board, AnimationPlan plan, CandleMotion motion, int window,
        bool crossSafeRight = false)
    {
        _board = board;
        _plan = plan;
        _motion = motion;
        _crossSafeRight = crossSafeRight;

        // Two is the least that still draws a line.
        _window = Math.Max(2, window);
    }

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        _titleLines = _title.For(session, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session, context, Palette.Background);

        var top = context.HeaderRow(PlotTopFraction, _titleLines);
        var bottom = context.BaselineAbove(CreditGap);
        var span = bottom - top;
        var mx = context.ChartLeft;

        // Measured once, here, and read by everything that follows: the plot's width and the
        // labels' right edge are two answers to one question.
        _giveWay = GiveWay(t);

        var plotW = Math.Max(1, context.ChartWidth - LabelColumn(session, context));
        var introA = Easing.Ramp(t, 0, 1000);

        DrawHeader(session, context, t);

        var (lo, hi, step) = Bounds();

        double Level(double value) => bottom - (((value - lo) / (hi - lo)) * span);

        DrawGrid(session, context, lo, hi, step, Level, plotW, introA);

        var n = _board.Count;
        var moving = -1;

        for (var i = 0; i < n; i++)
        {
            if (t <= _plan.IntroMs + (i * _plan.StaggerMs))
            {
                break;
            }

            moving = i;
        }

        if (moving < 0)
        {
            DrawXLabels(session, context, t, bottom, plotW, introA, n, 0, -1);
            DrawProgress(session, context, t);

            return;
        }

        var eased = new double[moving + 1];

        for (var i = 0; i <= moving; i++)
        {
            eased[i] = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));
        }

        // The window: shared with the two pages offering the same choice, so that a motion
        // means the same thing everywhere it is offered.
        var (count, head, first) = _plan.Window(
            _motion is CandleMotion.Scroll, _window, n, moving + eased[moving], t);

        // Where the window's left edge falls, rounded **up**: a point to the left of it lands
        // off the plot, over the axis labels, and the curve has to start at the chart's edge.
        var left = Math.Max(0, (int)Math.Ceiling(first));

        double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

        var lines = new List<((double X, double Y)[] Points, Color Colour, string Name, double Value)>();
        var anchors = new List<(double X, double Y)>();

        for (var k = 0; k < _board.Tracks.Count; k++)
        {
            var track = _board.Tracks[k];

            // Not on the frame yet: an instrument whose own history starts later than the
            // moment being drawn has no line, and no label either — the same thing "not
            // listed yet" means everywhere else in the app.
            if (track.First > moving)
            {
                continue;
            }

            var from = Math.Max(track.First, left);
            var to = Math.Min(moving, track.Last);

            if (to < from)
            {
                continue;
            }

            var colour = Palette.Track(k);
            var points = new List<(double X, double Y)>(to - from + 1);
            var value = 0d;

            for (var i = from; i <= to; i++)
            {
                var v = track.Returns[i];

                // The arriving point eases in *from the previous one's level*, not from zero.
                // A point that grew out of the baseline would draw a plunge and a climb at the
                // leading edge of every curve, on every frame of the closing stretch.
                if (i == moving && i > track.First)
                {
                    var before = track.Returns[i - 1];

                    v = before + ((v - before) * eased[i]);
                }

                value = v;
                points.Add((Across(i), Level(v)));
            }

            var white = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);
            var drawn = points.ToArray();

            if (drawn.Length >= 2)
            {
                DrawPolyline(session, context, drawn, colour, introA);
            }

            var (lx, ly) = (drawn[^1].X, drawn[^1].Y - context.Px(4));

            anchors.Add((lx, ly));

            void Dot(CanvasDrawingSession ds) =>
                ds.FillCircle((float)lx, (float)ly, (float)context.Px(6), white);

            Ink.Glow(session, context.Px(10), 0.9 * introA, Dot);
            Dot(session);

            lines.Add((drawn, colour, track.Name, value));
        }

        DrawLabels(session, context, lines, anchors, top, bottom, introA);
        DrawXLabels(session, context, t, bottom, plotW, introA, count, first, head);
        DrawProgress(session, context, t);
    }

    // ---- axis -----------------------------------------------------------------------

    /// <summary>
    /// The axis's bottom, top and step: a round interval covering every curve in both
    /// directions, with zero strictly inside it.
    ///
    /// Symmetric in reach rather than in extent: an axis stretched to the worst curve in
    /// each direction would put a board of six risers' zero line two thirds down the frame,
    /// and the eye reads that as the picture being about the one that fell.
    /// </summary>
    private (double Lo, double Hi, double Step) Bounds()
    {
        var reach = Math.Max(Math.Abs(_board.Peak), Math.Abs(_board.Trough)) * 1.08;
        var (step, _) = AnimationPlan.NiceScale(Math.Max(reach, 0.5), 4);

        var hi = Math.Max(step, Math.Ceiling(_board.Peak / step) * step);
        var lo = Math.Min(-step, Math.Floor(_board.Trough / step) * step);

        return (lo, hi, step);
    }

    private void DrawGrid(
        CanvasDrawingSession session, FrameContext context,
        double lo, double hi, double step, Func<double, double> level,
        double plotW, double opacity)
    {
        var mx = context.ChartLeft;
        var line = (float)Math.Max(1, context.Px(1));

        using var format = Ink.Format(context.Px(20));

        for (var v = lo; v <= hi + 1e-9; v += step)
        {
            var y = level(v);
            var zero = Math.Abs(v) < 1e-9;

            session.DrawLine(
                new Vector2((float)mx, (float)y),
                new Vector2((float)(mx + (plotW * opacity)), (float)y),
                zero ? Palette.AxisLabel : Palette.Grid,
                zero ? Math.Max((float)context.Px(2), line) : line);

            Ink.RightMiddle(
                session, Percent(v), mx - context.Px(12), y,
                format, zero ? Palette.Muted : Palette.AxisLabel, opacity);
        }
    }

    /// <summary>A percentage the same way in every locale, with its sign always shown.</summary>
    private static string Percent(double value) =>
        (value >= 0 ? "+" : "-") + Math.Abs(value).ToString("0.##", CultureInfo.InvariantCulture) + "%";

    // ---- the labels -----------------------------------------------------------------

    /// <summary>
    /// How much of the frame's right-hand side the end labels need: the amount the plot
    /// gives up so a label can ride ahead of its own curve and come to rest short of the
    /// band the host's interface covers.
    ///
    /// Measured from the **final** percentages rather than from this frame's, so the column
    /// is the same width on every frame — one that grew with the figures would narrow the
    /// plot while the labels were still moving along it.
    /// </summary>
    private double LabelColumn(CanvasDrawingSession session, FrameContext context)
    {
        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var widest = 0d;

        foreach (var track in _board.Tracks)
        {
            widest = Math.Max(
                widest,
                LabelWidth(session, context, nameFormat, valueFormat, track.Name, track.Final));
        }

        var need = context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad), _giveWay);

        return Math.Clamp(need, 0, context.ChartWidth * 0.45);
    }

    private static double LabelWidth(
        CanvasDrawingSession session, FrameContext context,
        CanvasTextFormat nameFormat, CanvasTextFormat valueFormat,
        string name, double value)
    {
        return Ink.Advance(session, name + " ", nameFormat)
               + Ink.Advance(session, Percent(value), valueFormat)
               + context.Px(LabelPadX * 2);
    }

    /// <summary>
    /// The name and the figure, riding each curve's leading end.
    ///
    /// Placed in one pass and drawn in another, because the boxes have to be kept apart
    /// from each other and that cannot be decided one at a time: two instruments that ended
    /// the range a fraction apart put their labels in the same place, and the one drawn
    /// second covers the first — a frame with the right number of labels on it and one of
    /// them missing.
    /// </summary>
    private void DrawLabels(
        CanvasDrawingSession session, FrameContext context,
        List<((double X, double Y)[] Points, Color Colour, string Name, double Value)> lines,
        List<(double X, double Y)> anchors,
        double top, double bottom, double opacity)
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
                context.SafeRight(_giveWay) - context.Px(LabelEdgePad) - width);

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

    // ---- the rest of the frame ------------------------------------------------------

    private void DrawXLabels(
        CanvasDrawingSession session, FrameContext context, double t, double bottom, double plotW,
        double introA, double count, double first, double head)
    {
        var n = _board.Count;
        var mx = context.ChartLeft;

        var whole = Math.Max(1, (int)Math.Round(count));

        var every = Math.Max(1, whole / 5);
        if (whole % every == 0 && whole / every > 5)
        {
            every = Math.Max(1, (whole / 6) + 1);
        }

        // A year across a span of years, a year-and-month across less; on a single session
        // it is the clock, which is what that axis counts in.
        var years = _board.End.DayNumber - _board.Start.DayNumber > 365 * 3;

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < n; i += every)
        {
            if (i < first || i > head)
            {
                continue;
            }

            var a = Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), 450) * introA;
            if (a <= 0)
            {
                continue;
            }

            var stamp = _board.Stamps[i];
            var text = _board.Intraday ? stamp : years ? stamp[..4] : stamp[..7];
            var x = mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

            Ink.Centred(session, text, x, bottom + context.Px(28), format, Palette.DateLabel, a);
        }
    }

    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = ResolvedTitle();

        _title.Draw(session, context, title, _title.For(session, title, context, ShowTitle), Palette.Title, a);

        using var small = Ink.Format(context.Px(25));

        // Which instruments, on what period — the same line the single-instrument frame
        // draws, with the code replaced by the ones being compared. Capped at three and
        // counted past that, because six upper-case codes under a title is a second title.
        var codes = _board.Tracks.Select(track => track.Code.ToUpperInvariant()).Take(3).ToList();

        if (_board.Tracks.Count > codes.Count)
        {
            codes.Add("+" + (_board.Tracks.Count - codes.Count).ToString(CultureInfo.InvariantCulture));
        }

        Ink.Centred(
            session,
            Strings.Format("CandleSubtitleLine",
                string.Join(" / ", codes),
                Strings.Get(CandleLoader.NameKey(_board.Period))),
            cx, Row(context, SubtitleRow), small, Palette.Muted, a);
    }

    private void DrawProgress(CanvasDrawingSession session, FrameContext context, double t)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);
        var p = Math.Clamp(t / _plan.TotalMs, 0, 1);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session, new Rect(0, y, context.Width * p, height), Palette.ProgressFill, context.Width);
    }

    /// <summary>
    /// How much of the host's button rail the frame now being drawn keeps clear: the same
    /// fraction, and the same reason for it being a fraction rather than a flag, as the
    /// three pages that offer the choice — a scrolling frame is a window while it rolls and
    /// only becomes the whole range as it opens out at the end, and the reservation has to
    /// open with it.
    /// </summary>
    private double GiveWay(double t)
    {
        if (!_crossSafeRight)
        {
            return 1;
        }

        return _motion is CandleMotion.Scroll
            ? 1 - Easing.Ramp(t, _plan.FinaleStartMs, AnimationPlan.OpenOutMs)
            : 0;
    }

    private static void DrawPolyline(
        CanvasDrawingSession session, FrameContext context,
        (double X, double Y)[] points, Color colour, double opacity)
    {
        var shape = new Vector2[points.Length];

        for (var i = 0; i < points.Length; i++)
        {
            shape[i] = new Vector2((float)points[i].X, (float)points[i].Y);
        }

        using var geometry = Polyline(session, shape);

        session.DrawGeometry(geometry, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(3));
    }

    private double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, _titleLines);

    /// <summary>
    /// What the frame is about: what the user typed, or the instruments' names. One place,
    /// because the text measured at the top of <see cref="Draw"/> and the text drawn in the
    /// header have to be the same string.
    /// </summary>
    private string ResolvedTitle() =>
        Title.Length > 0 ? Title : string.Join(" / ", _board.Tracks.Select(t => t.Name));

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
