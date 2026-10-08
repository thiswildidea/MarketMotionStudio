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
/// A plan's accumulation, drawn as two lines on one axis: what has been paid in,
/// and what the shares bought with it are worth.
///
/// The gap between the two lines *is* the result — a plan is the one indicator where
/// the interesting quantity is a difference rather than a level — so the space
/// between them is filled, warm while the plan is ahead and cool while it is
/// behind, and the headline figure is the ratio between them rather than either
/// level alone.
///
/// **Several plans on one axis** change what the frame can say. Six filled bands is
/// a picture of nothing, so the fill is one plan's alone; six paid-in lines are one
/// thick line, because buying the same amount on the same cadence from the same day
/// makes them the same staircase — so there is one, and it is the one that has paid
/// in the most (see <see cref="DcaBoard.Reference"/>). What is left is six value
/// lines, each with its own colour and its own figure at its leading end, and the
/// headline becomes *whose plan did best*, which is the question a comparison asks.
///
/// **Two motions, over one span.** <see cref="DcaMotion.Grow"/> lays the whole range
/// down at once; <see cref="DcaMotion.Scroll"/> holds a window of a chosen number of
/// trading days and walks it from the start of the range to its end. A decade of
/// daily marks grown across one frame leaves a three-month wobble two pixels wide.
///
/// The one thing a window does *not* move is the vertical scale. A candle chart
/// re-fits its price axis to whatever its window holds because a hundred bars of one
/// stock is a different set of prices; here the two levels are the plan's own, the
/// axis is one scale for the whole range in both motions, and re-fitting it as the
/// window slid would make the distance between the lines — the only figure on the
/// frame — change width while nothing about the plan had changed.
///
/// Stateless with respect to time per <c>one-render-path.mdc</c>: every frame comes
/// from <see cref="FrameContext.Progress"/> alone.
/// </summary>
public sealed class DcaRenderer : IFrameRenderer
{
    /// <summary>
    /// Distance from the chart baseline down to the credit, in baseline pixels. The date
    /// labels and the four statistic cards live in this band, the same reservation the
    /// whole-market forms make.
    /// </summary>
    public const double CreditGap = 278;

    /// <summary>Distance from the credit up to the top of the statistic cards.</summary>
    private const double CardsAboveCredit = 192;

    /// <summary>Where the plot area starts, as a fraction of frame height.</summary>
    private const double PlotTopFraction = 0.395;

    /// <summary>
    /// How far the end label sits to the right of the point it names. The label rides ahead
    /// of the line rather than over it; <see cref="LabelColumn"/> is where the room for that
    /// comes from.
    /// </summary>
    private const double LabelGap = 12;

    /// <summary>How far the widest label stays clear of the frame's own right edge.</summary>
    private const double LabelEdgePad = 12;

    private const double LabelPadX = 14;

    private const double LabelPadY = 8;

    /// <summary>Air between two end labels that ended up wanting the same row.</summary>
    private const double LabelBetween = 8;

    private const double LabelSize = 22;

    /// <summary>
    /// The end label's outline. A hairline over a curve of its own colour disappears
    /// where the two cross, which is exactly where the label is.
    /// </summary>
    private const double LabelEdge = 3;

    /// <summary>A plan that is ahead. The market's own convention: gains in red.</summary>
    private static readonly Color Gain = Palette.Emphasis;

    /// <summary>A plan that is behind. Cool, deliberately not the bar ramp's blue — a loss
    /// should read as absence of gain, not as a different measurement.</summary>
    private static readonly Color Loss = Rgb(0x34, 0xD3, 0x99);

    private readonly DcaBoard _board;

    private readonly AnimationPlan _plan;

    private readonly DcaMotion _motion;

    private readonly int _window;

    /// <summary>
    /// Whether the picture may run into the band the host covers with its button rail.
    /// A constructor argument and not a property: the board and the motion are, and a
    /// setting the renderer read back off a mutable property would arrive as the default
    /// on the frame that mattered — with every control still looking right.
    /// </summary>
    private readonly bool _crossSafeRight;

    private readonly (double Step, double Top) _scale;

    /// <summary>
    /// How much of that band the frame now being drawn keeps clear: 1 all of it, 0 none.
    /// Set once per frame, before anything measures the plot, because the plot's width and
    /// the labels' right edge have to be answers to the same question — a column measured
    /// against one and a label gathered to the other would disagree about where the line
    /// ends. See <see cref="GiveWay"/>.
    /// </summary>
    private double _giveWay = 1;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all; hiding it hands its row back.</summary>
    public bool ShowTitle { get; set; } = true;

    /// <summary>The wrapped headline.</summary>
    private readonly TitleBlock _title = new(62);

    /// <summary>
    /// How many lines the title took on the frame being drawn — what the plot's top edge and
    /// every header row below it are moved by. Set once at the top of <see cref="Draw"/>.
    /// </summary>
    private int _titleLines;

    /// <summary>
    /// Resource key for the venue's currency, set by the page from its market profile —
    /// the renderer reads no global settings, because a frame's contents should come
    /// from what it was handed, not from what the app happens to be set to.
    /// </summary>
    public string CurrencyKey { get; set; } = "DcaCurrencyCny";

    /// <param name="crossSafeRight">
    /// Whether the picture may run into the band the host covers with its button rail. Off,
    /// the plot stops short of it and the labels come to rest on its near side; on, the plot
    /// is as wide as the frame and the labels ride to the frame's own edge — which is what
    /// the page looked like before the band was measured, and what a frame meant for a
    /// surface with no such rail wants. Scrolling keeps clear until it opens out, because
    /// until then it is a window rather than the whole range; see <see cref="GiveWay"/>.
    /// </param>
    public DcaRenderer(
        DcaBoard board, AnimationPlan plan, DcaMotion motion, int window, bool crossSafeRight = false)
    {
        _board = board;
        _plan = plan;
        _motion = motion;
        _crossSafeRight = crossSafeRight;

        // Two is the shortest span that can still be drawn as a line.
        _window = Math.Max(2, window);

        // One axis for both lines: they are the same quantity in the same currency, and
        // the whole point of the picture is the distance between them.
        _scale = AnimationPlan.NiceScale(Math.Max(board.Peak, 0.0001) * 1.08, 5);
    }

    /// <summary>What the header reads off the frame: the moment, and where each plan stood.</summary>
    private sealed record Plot(int Index, double[] Values, double[] Paid);

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        // Before the plot: its top edge is placed by the bottom of the header block, which is
        // placed by how many lines the title took.
        _titleLines = _title.For(session, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session, context, Palette.Background);

        var plot = DrawPlot(session, context, t);

        DrawStats(session, context, t);
        DrawHeader(session, context, t, plot);
        DrawProgress(session, context, t);
    }

    // ---- plot -----------------------------------------------------------------------

    private Plot DrawPlot(CanvasDrawingSession session, FrameContext context, double t)
    {
        var n = _board.Dates.Count;
        var top = context.HeaderRow(PlotTopFraction, _titleLines);
        var bottom = context.BaselineAbove(CreditGap);
        var span = bottom - top;
        var mx = context.ChartLeft;

        // Measured once, here, and read by everything that follows: the plot's width and the
        // labels' right edge are two answers to one question, and a frame that answered it
        // twice would draw a line ending somewhere other than where its label is waiting.
        _giveWay = GiveWay(t);

        // The plot stops short of the right edge by the width of the labels' column, so that a
        // label can ride ahead of its own line without ever leaving the frame. Only the data
        // area gives way — the title, the cards and the progress bar still run the full width.
        var plotW = Math.Max(1, context.ChartWidth - LabelColumn(session, context));

        var introA = Easing.Ramp(t, 0, 1000);

        // Grid and its labels, growing in with everything else.
        using (var gridFormat = Ink.Format(context.Px(20)))
        {
            var line = (float)Math.Max(1, context.Px(1));

            for (var v = 0.0; v <= _scale.Top + 1e-9; v += _scale.Step)
            {
                var y = bottom - ((v / _scale.Top) * span);

                session.DrawLine(
                    new Vector2((float)mx, (float)y),
                    new Vector2((float)(mx + (plotW * introA)), (float)y),
                    Palette.Grid, line);

                Ink.RightMiddle(session, Money(v), mx - context.Px(12), y, gridFormat, Palette.AxisLabel, introA);
            }
        }

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
            DrawLegend(session, context, top, introA);

            // Nothing has arrived, so nothing is on the frame: an empty window, no labels.
            DrawXLabels(session, context, t, bottom, plotW, introA, n, 0, -1);

            return new Plot(-1, new double[_board.Tracks.Count], new double[_board.Tracks.Count]);
        }

        // Which points have arrived, and how far the arriving one has come. The lines
        // are cumulative, so growth eases without overshoot — a total that exceeds its
        // own final value and retreats reads as the data being corrected.
        //
        // The arriving point eases in *from the previous point's level*, not from the
        // baseline — see PositionRenderer for why: a line whose newest segment dives to
        // the floor and back reads as a crash, not as an arrival.
        var eased = new double[moving + 1];

        for (var i = 0; i <= moving; i++)
        {
            eased[i] = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));
        }

        // The window: how many axis positions it holds, where its right edge has reached,
        // and where its left one therefore is. Growing is the same arithmetic with a window
        // as long as the range, which is why the two motions share every line of drawing
        // below — and a scrolling one opens out into that same whole range as the frame
        // closes. How, and why, is in `AnimationPlan.Window`, shared with the two other
        // pages offering this choice.
        var (count, head, first) = _plan.Window(
            _motion is DcaMotion.Scroll, _window, n, moving + eased[moving], t);

        // Where the window's left edge falls, rounded **up**: a point to the left of it
        // lands off the plot, over the axis labels, and the curve has to start at the
        // chart's edge.
        var left = Math.Max(0, (int)Math.Ceiling(first));

        double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

        // ---- what has been paid in: one line for the board --------------------------
        //
        // The plan is one cadence and one amount, so the staircase is the board's, not one
        // per instrument — see `DcaBoard.Reference` for which of them is drawn. A window
        // that opens inside the range starts already at the level paid in by then: the
        // line has been at that height since the first buy, and easing it up again would
        // draw a second climb.
        var reference = _board.Tracks[_board.Reference];
        var paidLine = new List<(double X, double Y)>();
        var paidFrom = Math.Max(reference.First, left);
        var paidLevel = left == 0 ? 0d : reference.Invested[Math.Min(left, reference.Last)];

        for (var i = paidFrom; i <= moving; i++)
        {
            var target = reference.Invested[Math.Min(i, reference.Last)];

            paidLevel = i == 0 ? target * eased[i] : paidLevel + ((target - paidLevel) * eased[i]);

            paidLine.Add((Across(i), bottom - (paidLevel / _scale.Top * span)));
        }

        // ---- each plan's value line -------------------------------------------------
        var lines = new List<((double X, double Y)[] Points, Color Colour, string Name, double Profit)>(_board.Tracks.Count);

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];

            if (track.First > moving)
            {
                continue;
            }

            var last = Math.Min(moving, track.Last);

            // The window's left edge cuts a line that is already running, and a plan the
            // window has not reached yet has nothing on this frame at all.
            var begin = Math.Max(track.First, left);

            if (last < begin)
            {
                continue;
            }

            var points = new (double X, double Y)[last - begin + 1];
            var value = 0d;

            for (var at = begin; at <= last; at++)
            {
                var p = eased[at];

                if (at == 0)
                {
                    // The board's own first day has no level to come from, so the line
                    // rises from the axis — there is no segment yet, so nothing can crack.
                    value = track.Value[at] * p;
                }
                else if (at == track.First)
                {
                    // A plan that joins the board partway has no earlier level of its own,
                    // so it comes in at what it has paid in — which is exactly where the
                    // paid-in line already is, so the join is invisible. Rising from the
                    // axis instead would draw years of nothing and then a vertical climb.
                    value = track.Invested[at] + ((track.Value[at] - track.Invested[at]) * p);
                }
                else
                {
                    var previous = track.Value[at - 1];
                    value = previous + ((track.Value[at] - previous) * p);
                }

                points[at - begin] = (Across(at), bottom - (value / _scale.Top * span));
            }

            lines.Add((points, Palette.Track(i), track.Name,
                value - reference.Invested[Math.Min(last, reference.Last)]));
        }

        // The fill is one plan's picture — six bands on top of one another is a picture
        // of nothing. See the class note.
        if (!_board.Comparing && lines.Count > 0 && paidLine.Count > 1)
        {
            DrawFill(session, lines[0].Points, paidLine, introA);
        }

        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

        // **Which side of the value lines the paid-in line goes on depends on how many
        // there are.** One plan: the paid-in line first, because the two of them are the
        // picture and the value line is the one worth reading on top — the amber still
        // shows under it the whole way down. Several: the paid-in line **last**, because
        // every plan spends the same money at the same cadence, so for most of the span
        // they are all within a pixel or two of what they put in, and six lines drawn over
        // the reference erase it exactly where the reader looks for it. Measured on the
        // frame, tenths of the plot's columns holding any amber: one plan gives
        // [21,26,25,25,26,26,20,26,26,27] — never breaks. Six gave [12,0,3,11,28,28,8,0,5,4]
        // under the lines: nothing at all across the second and third tenths, so the line
        // appeared out of nowhere a third of the way along. On top it gives
        // [28,23,28,27,28,28,21,0,5,4], and it reads as what it is — the line every plan
        // grew out of. (The last three tenths are the six capsules stacked from the plot's
        // right edge back to x≈995, which cover every line the same way.)
        if (!_board.Comparing)
        {
            DrawPolyline(session, context, paidLine, Palette.Moving, style, introA);
        }

        foreach (var line in lines)
        {
            DrawPolyline(session, context, [.. line.Points], line.Colour, style, introA);
        }

        if (_board.Comparing)
        {
            DrawPolyline(session, context, paidLine, Palette.Moving, style, introA);
        }

        // The end dots: where each plan stands right now, on **its own** value line —
        // not on whichever of the two lines happens to be higher. The dot is what the
        // label is anchored to, and a label sitting up at the paid-in line while its
        // curve ran along the bottom would be a label about nothing on the frame.
        var white = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

        var anchors = new List<(double X, double Y)>();

        foreach (var line in lines)
        {
            var (lx, ly) = (line.Points[^1].X, line.Points[^1].Y - context.Px(4));

            anchors.Add((lx, ly));

            void Dot(CanvasDrawingSession ds) =>
                ds.FillCircle((float)lx, (float)ly, (float)context.Px(6), white);

            Ink.Glow(session, context.Px(10), 0.9 * introA, Dot);
            Dot(session);
        }

        DrawLabels(session, context, lines, anchors, top, bottom, introA);
        DrawLegend(session, context, top, introA);
        DrawXLabels(session, context, t, bottom, plotW, introA, count, first, head);

        // The values the headline reads: each plan's two levels at the moment being shown.
        // A plan that has not started yet is `NaN`, which loses every comparison and so is
        // never the leader — the same thing "not on the frame yet" means everywhere else.
        var values = new double[_board.Tracks.Count];
        var paid = new double[_board.Tracks.Count];

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];
            var at = Math.Min(moving, track.Last);

            values[i] = track.First > moving || at < track.First
                ? double.NaN
                : track.Value[at];

            paid[i] = track.First > moving || at < track.First
                ? double.NaN
                : track.Invested[at];
        }

        return new Plot(moving, values, paid);
    }

    /// <summary>
    /// The space between the two lines, coloured by which one is on top — warm while the
    /// plan is worth more than was put in, cool while it is worth less.
    ///
    /// The read is by **height on the frame**, not by the two numbers: a value line above
    /// the paid-in line is a plan that is ahead, and a fill coloured the other way round
    /// is a frame arguing with its own headline.
    /// </summary>
    private static void DrawFill(
        CanvasDrawingSession session,
        (double X, double Y)[] value,
        List<(double X, double Y)> paid,
        double opacity)
    {
        if (value.Length < 2 || paid.Count < 2)
        {
            return;
        }

        // The shorter of the two decides: the band is only drawn where both exist.
        var span = Math.Min(value.Length, paid.Count);
        var colour = value[span - 1].Y <= paid[span - 1].Y ? Gain : Loss;

        var ring = new Vector2[(span * 2) + 1];

        for (var i = 0; i < span; i++)
        {
            ring[i] = new Vector2((float)value[i].X, (float)value[i].Y);
        }

        for (var i = span - 1; i >= 0; i--)
        {
            ring[span + (span - 1 - i)] = new Vector2((float)paid[i].X, (float)paid[i].Y);
        }

        // Close along the left edge so the fill is a closed region, not a bow-tie when
        // the lines cross.
        ring[^1] = ring[0];

        using var geometry = CanvasGeometry.CreatePolygon(session, ring);

        session.FillGeometry(geometry, Ink.Fade(colour, 0.14 * opacity));
    }

    private static void DrawPolyline(
        CanvasDrawingSession session, FrameContext context,
        List<(double X, double Y)> points, Color colour, CanvasStrokeStyle shared, double opacity)
    {
        if (points.Count < 2)
        {
            return;
        }

        var path = new Vector2[points.Count];

        for (var i = 0; i < points.Count; i++)
        {
            path[i] = new Vector2((float)points[i].X, (float)points[i].Y);
        }

        using var geometry = Polyline(session, path);

        session.DrawGeometry(geometry, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(3), shared);
    }

    /// <summary>
    /// How much of the frame's right-hand side the end labels need, in frame pixels — the
    /// amount the plot gives up so that a label can ride ahead of its own line and come to
    /// rest short of the band the host's own interface covers, rather than short of the
    /// frame's edge.
    ///
    /// Measured from the **final** amounts rather than from this frame's, so the column is the
    /// same width on every frame. A column that grew with the figures would narrow the plot
    /// while the labels were still moving along it, and the lines would slide sideways as they
    /// were being read.
    ///
    /// The right margin keeps part of the band empty and the plot gives up only what that
    /// margin cannot cover — see <see cref="FrameContext.RightLabelColumn"/>, which owns the
    /// arithmetic now that three pages depend on it — and never more than a fixed share of
    /// its own width, because past that point a longer name is being answered by shrinking
    /// the picture, which is the wrong end to take it from. When the cap does bite, the
    /// labels give way instead: see <see cref="DrawLabels"/>.
    /// </summary>
    /// <summary>
    /// How much of the host's button rail the frame now being drawn keeps clear.
    ///
    /// Not a flag but a fraction, because scrolling needs the values between the two ends.
    /// It spends the closing stretch opening its window out into the whole range, and the
    /// frame a video stops on is then the whole range — the same picture growing draws from
    /// its first frame on. A frame allowed to use the band therefore has to *become* that
    /// picture rather than switch to it: the reservation shrinks across the same ramp the
    /// window opens on, and reaches nothing exactly when the window has finished opening.
    /// Until the ramp starts, a scrolling frame is still a window, and it keeps clear like
    /// one — its labels sit as far right as a window's do.
    /// </summary>
    private double GiveWay(double t)
    {
        if (!_crossSafeRight)
        {
            return 1;
        }

        return _motion is DcaMotion.Scroll
            ? 1 - Easing.Ramp(t, _plan.FinaleStartMs, AnimationPlan.OpenOutMs)
            : 0;
    }

    private double LabelColumn(CanvasDrawingSession session, FrameContext context)
    {
        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var widest = 0d;

        // Every plan on the board, not just the ones on this frame: the column has to be the
        // same width before a plan has arrived as after it, or the whole plot would shift the
        // day its line starts.
        foreach (var track in _board.Tracks)
        {
            widest = Math.Max(
                widest,
                LabelWidth(session, context, nameFormat, valueFormat, track.Name, FinalProfit(track)));
        }

        var need = context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad), _giveWay);

        return Math.Clamp(need, 0, context.ChartWidth * 0.45);
    }

    /// <summary>
    /// What this plan's label comes to once the animation has finished — the same arithmetic
    /// the line's own label uses when it gets there: the plan's final value over what the
    /// reference plan had paid in by then. Asked here so that the room reserved for the
    /// widest label is reserved against the figures that actually end up on the frame.
    /// </summary>
    private double FinalProfit(DcaTrack track)
    {
        var reference = _board.Tracks[_board.Reference];

        return track.Value[track.Last] - reference.Invested[Math.Min(track.Last, reference.Last)];
    }

    /// <summary>
    /// How wide one label is — the name and the money, measured in the two faces they are
    /// drawn in rather than guessed from a character count, because the amount changes width
    /// as it grows and the name can be anything the directory returns.
    ///
    /// Shared by the column that makes room for the widest label and by the drawing of each
    /// one, so the two cannot disagree about how much room that is.
    /// </summary>
    private static double LabelWidth(
        CanvasDrawingSession session, FrameContext context,
        CanvasTextFormat nameFormat, CanvasTextFormat valueFormat,
        string name, double profit)
    {
        var money = Sign(profit) + Money(Math.Abs(profit));

        return Ink.Advance(session, name + " ", nameFormat)
               + Ink.Advance(session, money, valueFormat)
               + context.Px(LabelPadX * 2);
    }

    /// <summary>
    /// The name and the money, riding each line's leading end.
    ///
    /// Placed in one pass and drawn in another, because the boxes have to be kept apart
    /// from each other and that cannot be decided one at a time. Two plans that ended the
    /// day a fraction apart put their labels in the same place, and the one drawn second
    /// covers the first — a frame with the right number of labels on it and one of them
    /// missing. They are pushed down the frame in the order they came out, which is stable
    /// between frames and between runs, and the whole stack is then slid back inside the
    /// plot so a label near the top is not clipped.
    ///
    /// Each one sits **ahead of** its own line's leading end, in the column the plot left for it.
    ///
    /// Drawn for one plan as much as for six: the figure is what the page is for, and a
    /// frame that only labelled a comparison would be refusing to answer the question it
    /// was asked about a single instrument.
    /// </summary>
    private void DrawLabels(
        CanvasDrawingSession session, FrameContext context,
        List<((double X, double Y)[] Points, Color Colour, string Name, double Profit)> lines,
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
            var (_, _, name, profit) = lines[i];

            var width = LabelWidth(session, context, nameFormat, valueFormat, name, profit);

            // The label rides **ahead of** the point it belongs to, in the column the plot was
            // shortened to leave for it: by the end of the animation that column is past the
            // plot's last one, so a label never covers the line it is about.
            //
            // Its right edge is the one that gives way, and it gives way to the **safe line**
            // rather than to the frame's edge: past that line is the band the platform covers
            // with its avatar and its comment button, and a 9:16 video whose figure is readable
            // in the editor and hidden on the phone it was made for is the failure this exists
            // to prevent. A long name with a large amount, and the side margins pushed out, can
            // leave the column narrower than the widest label, and then the label slides back
            // over the point rather than into the rail.
            //
            // `GiveWay` is what turns that line back into the frame's own edge on a page
            // allowed to use the band — wholly, on a frame that fills the span, and by
            // however much the window has opened out on one that is still opening.
            var left = Math.Min(
                anchors[i].X + context.Px(LabelGap),
                context.SafeRight(_giveWay) - context.Px(LabelEdgePad) - width);

            boxes.Add(new Rect(Math.Max(context.ChartLeft, left), anchors[i].Y, width, height));
        }

        // Push apart, top to bottom. The order is by where the labels would have gone, and
        // it is kept: a label pushed past its neighbour never overtakes it.
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
            var (_, colour, name, profit) = lines[i];
            var box = new Rect(boxes[i].X, centres[i] - (height / 2), boxes[i].Width, height);
            var radius = (float)(height / 2);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, 0.92 * opacity));
            session.DrawRoundedRectangle(box, radius, radius, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(LabelEdge));

            var money = Sign(profit) + Money(Math.Abs(profit));

            Ink.Runs(
                session,
                [
                    (name + " ", Palette.Muted, nameFormat),
                    (money, colour, valueFormat),
                ],
                box.X + (box.Width / 2),
                box.Y + (height / 2) + (size * 0.36),
                opacity);
        }
    }

    /// <summary>What each line is, drawn where a reader looks first: above the plot's left end.</summary>
    private void DrawLegend(CanvasDrawingSession session, FrameContext context, double top, double opacity)
    {
        if (opacity <= 0)
        {
            return;
        }

        // A comparison names its value lines at their own leading ends, so the legend
        // would be six names said twice — it keeps the one line no label belongs to.
        var entries = _board.Comparing
            ? new[] { (Palette.Moving, "DcaLegendInvested") }
            : new[] { (Gain, "DcaLegendValue"), (Palette.Moving, "DcaLegendInvested") };

        var y = top - context.Px(24);
        var x = context.ChartLeft;
        var swatch = context.Px(34);

        using var format = Ink.Format(context.Px(21));

        foreach (var (colour, key) in entries)
        {
            session.DrawLine(
                new Vector2((float)x, (float)y), new Vector2((float)(x + swatch), (float)y),
                Ink.Fade(colour, 0.95 * opacity), (float)context.Px(4));

            var text = Strings.Get(key);
            var width = Ink.Measure(session, text, format);

            Ink.Left(session, text, x + swatch + context.Px(10), y + context.Px(7), format, Palette.Muted, opacity);

            x += swatch + context.Px(10) + width + context.Px(40);
        }
    }

    /// <summary>A handful of dates under the plot, fading in as the line reaches them.</summary>
    /// <param name="plotW">
    /// The plot's width, handed in rather than read off the context: the dates have to sit
    /// under the columns they name, and the plot is narrower than the chart by the labels'
    /// column (see <see cref="LabelColumn"/>). Measured in one place, used in two.
    /// </param>
    private void DrawXLabels(
        CanvasDrawingSession session, FrameContext context, double t,
        double bottom, double plotW, double introA, double count, double first, double head)
    {
        var n = _board.Dates.Count;
        var mx = context.ChartLeft;

        // How many positions the window holds, rounded, because the question the step
        // answers — how far apart the labels go — is a whole-number one. The placing
        // below still uses `count` itself, which is fractional while a scrolling window
        // is opening out.
        var whole = Math.Max(1, (int)Math.Round(count));

        var every = Math.Max(1, whole / 5);
        if (whole % every == 0 && whole / every > 5)
        {
            every = Math.Max(1, (whole / 6) + 1);
        }

        // A year label when the plan spans years, year-and-month when it spans less —
        // twelve "2024-06" stamps on a decade-long plan is noise nobody reads.
        var longSpan = _board.End.DayNumber - _board.Start.DayNumber > 365 * 3;

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < n; i += every)
        {
            // A tick outside the window would be dated off the side of the frame.
            if (i < first || i > head)
            {
                continue;
            }

            var a = Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), 450) * introA;
            if (a <= 0)
            {
                continue;
            }

            var day = _board.Dates[i];
            var text = longSpan
                ? day.Year.ToString(CultureInfo.InvariantCulture)
                : day.ToString("yyyy-MM", CultureInfo.InvariantCulture);

            Ink.Centred(
                session, text,
                mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0),
                bottom + context.Px(28), format, Palette.DateLabel, a);
        }
    }

    // ---- header ---------------------------------------------------------------------

    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t, Plot plot)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = ResolvedTitle();

        _title.Draw(session, context, title, _title.For(session, title, context, ShowTitle), Palette.Title, a);

        using var small = Ink.Format(context.Px(25));

        // What the plan is: the fixed amount, how often, into what, in whose currency.
        var frequency = _board.Frequency switch
        {
            DcaFrequency.Weekly => Strings.Get("DcaFreqWeekly"),
            DcaFrequency.Monthly => Strings.Get("DcaFreqMonthly"),
            _ => Strings.Get("DcaFreqDaily"),
        };

        var money = _board.Amount.ToString("0", CultureInfo.InvariantCulture);
        var unit = Strings.Get(CurrencyKey);

        var planLine = _board.Comparing
            ? Strings.Format("DcaCompareSubtitle", frequency, money, unit,
                _board.Tracks.Count.ToString(CultureInfo.InvariantCulture), Iso(_board.Start))
            : Strings.Format("DcaSubtitleLine", frequency, money, unit, _board.Tracks[0].Name);

        Ink.Centred(session, planLine, cx, Row(context, 0.19), small, Palette.Muted, a);

        // The span, with the count of buys as the figure the eye stops on.
        var buys = _board.Buys.ToString("#,##0", CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session,
                Strings.Format("DcaRangeLine", Iso(_board.Start), Iso(_board.End), buys),
                buys,
                Palette.Muted, Palette.Emphasis,
                small, strong,
                cx, Row(context, 0.218), a);
        }

        if (plot.Index < 0)
        {
            return;
        }

        using (var dateFormat = Ink.Format(context.Px(34)))
        {
            // The middle of the air between the plan's range line and the running figure
            // below, measured to their ink rather than to their baselines: the figure is
            // 128 pixels where the range line is 25, so half way between two baselines is
            // not half way between two lines.
            //
            //     range line's foot  0.218 * 1920 + 0.06 * 25  = 420.1
            //     figure's top       0.327 * 1920 - 0.72 * 128 = 535.7
            //     the date is 0.72 * 34 = 24.5 tall
            //
            // and (535.7 + 420.1 + 24.5) / 2 = 490.1, which is 0.2553 of the frame. At the
            // 0.262 it used to be the date had 58 pixels of air above it and 33 below.
            Ink.Centred(session, Iso(_board.Dates[plot.Index]), cx, Row(context, 0.2553), dateFormat, Palette.Moving, a);
        }

        // The headline: what the plan has returned over what was paid in, read off the
        // moment being shown. Its colour follows the sign of what is displayed, so a
        // plan crossing from loss to gain changes the colour of its own number.
        //
        // With several, it is **the best of them and its name** — and the best is chosen by
        // return, not by profit, because that is the one figure a comparison of plans can
        // put side by side: an instrument listed later paid in less, so a smaller profit
        // on it is not a worse plan.
        var leader = -1;
        var best = double.NegativeInfinity;

        for (var i = 0; i < plot.Values.Length; i++)
        {
            if (plot.Paid[i] <= 0)
            {
                continue;
            }

            // `NaN` is a plan that has not arrived; a comparison of it with anything is
            // false, so it never wins — which is what "not on the frame yet" should mean.
            var ret = (plot.Values[i] / plot.Paid[i]) - 1;

            if (ret > best)
            {
                best = ret;
                leader = i;
            }
        }

        if (leader < 0)
        {
            return;
        }

        var shown = best * 100;
        var text = (shown >= 0 ? "+" : string.Empty) + shown.ToString("0.0", CultureInfo.InvariantCulture) + "%";
        var colour = shown >= 0 ? Gain : Loss;

        var label = _board.Comparing
            ? Strings.Format("DcaLeaderLine", _board.Tracks[leader].Name)
            : Strings.Get("DcaReturnLabel");

        using (var bigFormat = Ink.Format(context.Px(128), bold: true))
        {
            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, colour));

            Ink.Centred(session, text, cx, Row(context, 0.327), bigFormat, colour, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, label, cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    /// <summary>“定投计划：沪深300ETF” — what the frame says when no title was typed.</summary>
    private string DefaultTitle() => Strings.Format("DcaDefaultTitle", _board.Tracks[0].Name);

    // ---- closing --------------------------------------------------------------------

    /// <summary>The summary cards and the credit, which arrive last.</summary>
    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var left = context.ChartLeft;
        var gap = context.Px(14);
        var cardHeight = context.Px(132);
        var y = context.CreditLine - context.Px(CardsAboveCredit);

        using var labelFormat = Ink.Format(context.Px(22));
        using var valueFormat = Ink.Format(context.Px(34), bold: true);

        if (_board.Comparing)
        {
            DrawTrackCards(session, context, a);

            DrawCredit(session, context, a);

            return;
        }

        // One plan: the four figures that describe it. 期末市值 and 投入本金 are its two
        // levels, 历史净收益 their difference, and 买入次数 what the discipline cost in
        // presses — the one figure here that is about the plan rather than the price.
        var track = _board.Tracks[0];
        var cards = new[]
        {
            (Strings.Get("DcaCardValue"), Money(track.FinalValue), Palette.CardValue),
            (Strings.Get("DcaCardInvested"), Money(track.FinalInvested), Palette.CardValue),
            (Strings.Get("DcaCardProfit"), Sign(track.Profit) + Money(Math.Abs(track.Profit)),
                track.Profit >= 0 ? Gain : Loss),
            (Strings.Get("DcaCardBuys"), track.Buys.ToString("#,##0", CultureInfo.InvariantCulture), Palette.CardValue),
        };

        var cardWidth = (context.ChartWidth - (gap * 3)) / 4;

        for (var i = 0; i < cards.Length; i++)
        {
            var x = left + (i * (cardWidth + gap));
            var box = new Rect(x, y, cardWidth, cardHeight);
            var radius = (float)context.Px(14);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, a));
            session.DrawRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardStroke, a), (float)context.Px(1.5));

            Ink.Centred(session, cards[i].Item1, x + (cardWidth / 2), y + context.Px(42), labelFormat, Palette.Muted, a);
            Ink.Centred(session, cards[i].Item2, x + (cardWidth / 2), y + context.Px(92), valueFormat, cards[i].Item3, a);
        }

        DrawCredit(session, context, a);
    }

    /// <summary>
    /// A comparison's closing row: one card per plan, in the colour of its own line.
    ///
    /// The four single-plan cards answer "what did this cost me and what did it come to".
    /// None of those is a comparison: the amount and the cadence are the same on every card,
    /// and one count of buys among six plans cannot be the frame's closing figure. So the row
    /// becomes the six answers to the question the page was actually asked — whose plan did
    /// best, and by how much money — and the money figure repeats the label riding each line,
    /// which is what makes it checkable at a glance.
    ///
    /// The return is on the card as well as the money, because the two disagree whenever the
    /// plans did not start together: one that listed later paid in less, and a smaller profit
    /// on it is not a worse plan.
    ///
    /// The row itself is <see cref="TrackCards"/>, the same one the holdings board and both of the
    /// candle board's layouts end on. What a card says is this page's business; what it looks like
    /// is not.
    /// </summary>
    private void DrawTrackCards(CanvasDrawingSession session, FrameContext context, double a)
    {
        var cards = new List<TrackCards.Card>(_board.Tracks.Count);

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];

            cards.Add(new TrackCards.Card(
                track.Name,
                Palette.Muted,
                Palette.Track(i),
                Sign(track.Profit) + Money(Math.Abs(track.Profit)),
                (track.ReturnPercent >= 0 ? "+" : string.Empty)
                    + track.ReturnPercent.ToString("0.0", CultureInfo.InvariantCulture) + "%"));
        }

        TrackCards.Draw(session, context, cards, a, _giveWay);
    }

    private static void DrawCredit(CanvasDrawingSession session, FrameContext context, double a)
    {
        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(
            session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    /// <summary>The bottom bar showing how far through the video this frame is.</summary>
    private void DrawProgress(CanvasDrawingSession session, FrameContext context, double t)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);
        var p = Math.Clamp(t / _plan.TotalMs, 0, 1);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session, new Rect(0, y, context.Width * p, height), Palette.ProgressFill, context.Width);
    }

    private double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, _titleLines);

    /// <summary>
    /// The headline this frame draws: what the user typed, or the default naming the plans. One
    /// place, because the text measured at the top of <see cref="Draw"/> and the text drawn in the
    /// header have to be the same string.
    /// </summary>
    private string ResolvedTitle() => Title.Length > 0 ? Title : DefaultTitle();

    // ---- formatting -----------------------------------------------------------------

    /// <summary>
    /// An amount of the venue's currency. CJK readers get it in 万 of that currency,
    /// because that is the unit every figure on a Chinese chart is read in; everybody
    /// else gets thousands and millions, which is theirs. One helper because the cards,
    /// the axis and the fill all have to agree or the picture contradicts itself.
    /// </summary>
    public static string Money(double value)
    {
        var wan = Strings.Get("DcaWanUnit");

        if (wan.Length > 0 && value >= 10_000)
        {
            var scaled = value / 10_000;
            var decimals = scaled >= 100 ? 0 : scaled >= 10 ? 1 : 2;

            return scaled.ToString(decimals == 0 ? "#,##0" : "0." + new string('#', decimals), CultureInfo.InvariantCulture) + wan;
        }

        return value switch
        {
            >= 1_000_000 => (value / 1_000_000).ToString("0.##", CultureInfo.InvariantCulture) + "M",
            >= 10_000 => (value / 1_000).ToString("0.#", CultureInfo.InvariantCulture) + "K",
            _ => value.ToString("#,##0", CultureInfo.InvariantCulture),
        };
    }

    private static string Sign(double value) => value >= 0 ? "+" : "-";

    /// <summary>A date the same way in every locale.</summary>
    public static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);

    /// <summary>A path through the points, open at both ends.</summary>
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
