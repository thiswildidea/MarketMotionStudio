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
/// One or more holdings, drawn as lines on one axis: the flat capital that went in once, and
/// what the shares it bought are worth, which is the whole story — every rise and fall on this
/// chart is the price's doing, nothing was added and nothing removed.
///
/// The space between the capital and the value is filled, warm while the holding is ahead and
/// cool while it is behind, the same convention as the plan page. That fill is a **single
/// holding's** picture: it is a statement about one line's distance from one other, and six
/// overlapping fills are a mud that says nothing about any of them. A comparison frame leaves it
/// out and lets the lines speak, which is also why the legend shrinks to the capital alone —
/// with more than one holding every curve is named where a reader is already looking, at its own
/// leading end.
///
/// **Each holding's figure rides its own line.** With one holding that is an addition to what
/// this frame always said — the headline in the middle is still the return, and the label at the
/// end of the line is the money it comes to. With several, the labels are the only thing that can
/// say which curve is which *and* how far ahead it is at the moment being shown, so the headline
/// moves to the leader's own figure: a single percentage in the middle of a six-curve frame would
/// have to pick one holding to be about, and picking the first would make the frame a statement
/// about the order the list happened to be in.
///
/// **Two motions, over one span.** <see cref="PositionMotion.Grow"/> lays the whole range across
/// the frame and fills it; <see cref="PositionMotion.Scroll"/> keeps a window of fixed length and
/// walks it forward. Both are the same arithmetic — grow is a window as long as the range — and
/// that is deliberate, because everything else here (the labels, the headline, the closing cards)
/// reads off the picture and must not have two versions.
///
/// The one thing they do *not* share is the vertical scale. A candle chart re-scales to what its
/// window holds, because a hundred bars of one stock is a different set of prices. This chart's
/// axis is one number for the whole range in both motions: the capital line is a constant, and an
/// axis that re-fitted itself as the window slid would make the flat line wander while nothing
/// about the holding had changed.
///
/// Stateless with respect to time per <c>one-render-path.mdc</c>: every frame comes
/// from <see cref="FrameContext.Progress"/> alone.
/// </summary>
public sealed class PositionRenderer : IFrameRenderer
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

    /// <summary>A holding that is ahead. The market's own convention: gains in red.</summary>
    private static readonly Color Gain = Palette.Emphasis;

    /// <summary>A holding that is behind. Cool, deliberately not the bar ramp's blue — a loss
    /// should read as absence of gain, not as a different measurement.</summary>
    private static readonly Color Loss = Rgb(0x34, 0xD3, 0x99);

    // ---- the end label ------------------------------------------------------------------
    //
    // A rounded box riding each line's leading end, carrying the holding's name and what it is
    // worth over what went in, at the moment being drawn. Sized in frame pixels like everything
    // else here, so a preview and an export of a different format put it in the same place.

    /// <summary>
    /// How far the label's **left** edge stays clear of the point it belongs to. The label
    /// rides ahead of the line rather than over it; <see cref="LabelColumn"/> is where the
    /// room for that comes from.
    /// </summary>
    private const double LabelGap = 12;

    /// <summary>How far the widest label stays clear of the frame's own right edge.</summary>
    private const double LabelEdgePad = 12;

    /// <summary>Its own padding, and the room two stacked labels keep between them.</summary>
    private const double LabelPadX = 14;

    private const double LabelPadY = 8;

    private const double LabelBetween = 8;

    /// <summary>The label's type size. Smaller than a card's value and larger than its caption.</summary>
    private const double LabelSize = 22;

    /// <summary>
    /// How thick the label's outline is, and why it is not the hairline the cards use.
    ///
    /// A label sits on top of a line of its own colour, so the outline is the only thing
    /// separating the two — and these frames are watched as video, at whatever size the player
    /// happens to be. At a hairline the box reads as a smudge of the curve it is over.
    /// </summary>
    private const double LabelEdge = 3;

    private readonly PositionBoard _board;

    private readonly AnimationPlan _plan;

    /// <summary>How the picture advances; see the class note.</summary>
    private readonly PositionMotion _motion;

    /// <summary>
    /// How many axis positions the scrolling window holds. Read by the scrolling motion alone —
    /// the growing one is a window as long as the whole range.
    /// </summary>
    private readonly int _window;

    private readonly (double Step, double Top) _scale;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all; hiding it hands its row back.</summary>
    public bool ShowTitle { get; set; } = true;

    /// <summary>
    /// Resource key for the venue's currency, set by the page from its market profile —
    /// the renderer reads no global settings, because a frame's contents should come
    /// from what it was handed, not from what the app happens to be set to.
    /// </summary>
    public string CurrencyKey { get; set; } = "DcaCurrencyCny";

    public PositionRenderer(PositionBoard board, AnimationPlan plan, PositionMotion motion, int window)
    {
        _board = board;
        _plan = plan;
        _motion = motion;

        // Two is the least that still draws a line. A window longer than the range is not
        // wrong — it simply leaves nothing to scroll, and the frame grows instead of rolling.
        _window = Math.Max(2, window);

        // One axis for every line: they are the same quantity in the same currency, and
        // the whole point of the picture is the distance between them.
        _scale = AnimationPlan.NiceScale(Math.Max(board.Peak, 0.0001) * 1.08, 5);
    }

    /// <summary>
    /// What the frame is showing at the moment being drawn: the axis position the animation has
    /// reached, and each holding's value there.
    ///
    /// The values are the **eased** ones, the same numbers the lines were drawn from, because the
    /// headline and the end labels are read off the picture rather than off the data — a figure
    /// that disagreed with the line beside it would be worse than either on its own. A holding
    /// that has not arrived yet is <see cref="double.NaN"/>, which is also how a holding that
    /// listed after the range began reads on the frames before its own first day.
    /// </summary>
    private sealed record Plot(int Index, double[] Values);

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        context.Backdrop.Fill(session, context, Palette.Background);

        var plot = DrawPlot(session, context, t);

        DrawStats(session, context, t);
        DrawHeader(session, context, t, plot);
        DrawProgress(session, context, t);
    }

    // ---- plot -----------------------------------------------------------------------

    /// <summary>
    /// The capital line, one line per holding, their end labels; reports the axis position the
    /// animation has reached and each holding's value there.
    /// </summary>
    private Plot DrawPlot(CanvasDrawingSession session, FrameContext context, double t)
    {
        var n = _board.Dates.Count;
        var top = context.HeaderRow(PlotTopFraction, ShowTitle);
        var bottom = context.BaselineAbove(CreditGap);
        var span = bottom - top;
        var mx = context.ChartLeft;

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

                Ink.RightMiddle(session, DcaRenderer.Money(v), mx - context.Px(12), y, gridFormat, Palette.AxisLabel, introA);
            }
        }

        // Which axis positions have arrived, and how far each arriving one has come.
        //
        // The arriving point eases in *from the previous point's level*, not from the baseline.
        // Bars grow from zero because a bar is a column standing on the axis; a line's newest
        // segment would otherwise plunge from the previous close to the floor and climb back, a
        // crack that reads as a crash — glaring in a paused frame, a permanent dent at the
        // leading edge in playback.
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

            // Nothing has arrived, so nothing is on the frame: an empty window and no labels.
            DrawXLabels(session, context, t, bottom, plotW, introA, n, 0, -1);

            return new Plot(-1, new double[_board.Tracks.Count]);
        }

        var eased = new double[moving + 1];

        for (var i = 0; i <= moving; i++)
        {
            eased[i] = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));
        }

        // The window: how many axis positions it holds, where its right edge has reached, and
        // where its left one therefore is. Growing is the same arithmetic with a window as long
        // as the range, which is why the two motions share every line of drawing below — and a
        // scrolling one opens out into that same whole range as the frame closes. How, and why,
        // is in `AnimationPlan.Window`, shared with the two other pages offering this choice.
        //
        // The right edge leads the arrival by the part of the arriving point that has come
        // through, so the window is already sliding while that point is still growing into
        // place — a roll rather than a step per day.
        var (count, head, first) = _plan.Window(
            _motion is PositionMotion.Scroll, _window, n, moving + eased[moving], t);

        // Where the window's left edge falls, rounded **up**: a point to the left of it lands
        // off the plot, over the axis labels, and the curve has to start at the chart's edge.
        var left = Math.Max(0, (int)Math.Ceiling(first));

        double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

        // The capital, which is one number for the whole board and therefore one line. A window
        // that opens inside the range starts already at the capital — the line has been at that
        // level since the first purchase, and easing it up again would draw a second one.
        var capitalFrom = Math.Max(0, left);
        var capitalLine = new List<(double X, double Y)>(Math.Max(0, moving - capitalFrom) + 1);
        var level = capitalFrom == 0 ? 0 : _board.Capital;

        for (var i = capitalFrom; i <= moving; i++)
        {
            level = i == 0
                ? _board.Capital * eased[i]
                : level + ((_board.Capital - level) * eased[i]);

            capitalLine.Add((Across(i), bottom - (level / _scale.Top * span)));
        }

        // Each holding's own line. Only its own stretch of the axis is drawn: an instrument
        // that listed in 2020 has nothing to say about 2015, and a flat line along the capital
        // there would be a claim that it did.
        var lines = new List<((double X, double Y)[] Points, Color Colour, string Name, double Profit)>(_board.Tracks.Count);

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];

            if (track.First > moving)
            {
                continue;
            }

            var last = Math.Min(moving, track.Last);

            // The window's left edge cuts a line that is already running, and a holding the
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
                    // The board's own first day has no level to come from, so the line rises
                    // from the axis — there is no segment yet, so nothing can crack.
                    value = track.Value[at] * p;
                }
                else if (at == track.First)
                {
                    // A holding that joins the board partway has no earlier level of its own,
                    // so it comes in at its own cost — which is exactly where the capital line
                    // already is drawn, so the join is invisible. Rising from the axis instead
                    // would draw years of nothing and then a vertical climb, a crash backwards.
                    value = _board.Capital + ((track.Value[at] - _board.Capital) * p);
                }
                else
                {
                    var previous = track.Value[at - 1];
                    value = previous + ((track.Value[at] - previous) * p);
                }

                points[at - begin] = (Across(at), bottom - (value / _scale.Top * span));
            }

            lines.Add((points, Palette.Track(i), track.Name, value - _board.Capital));
        }

        // The fill is a single holding's picture — see the class note.
        if (!_board.Comparing && lines.Count > 0)
        {
            DrawFill(session, lines[0].Points, capitalLine, Gain, Loss, introA);
        }

        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

        DrawPolyline(session, context, capitalLine, Palette.Moving, style, introA);

        foreach (var line in lines)
        {
            DrawPolyline(session, context, [.. line.Points], line.Colour, style, introA);
        }

        // The end dots: where each holding stands right now. On that holding's **own** line,
        // not on whichever of the two happens to be higher — the dot is what the label is
        // anchored to, and a label that sat up at the capital line while its curve ran along the
        // bottom would be a label about nothing on the frame.
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

        // The values the headline reads: each holding's level at the moment being shown, or the
        // last level it had for a holding whose data ended before the animation got there. A
        // holding that has not started yet is `NaN`, which loses every comparison and so is
        // never the leader — the same thing "not on the frame yet" means everywhere else here.
        var values = new double[_board.Tracks.Count];

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];

            values[i] = track.First > moving ? double.NaN : track.Value[Math.Min(moving, track.Last)];
        }

        return new Plot(moving, values);
    }

    /// <summary>The space between a holding's line and the capital, coloured by which is on top.</summary>
    private static void DrawFill(
        CanvasDrawingSession session,
        (double X, double Y)[] value, List<(double X, double Y)> capital,
        Color gain, Color loss, double opacity)
    {
        // Both ends of both runs are the same axis positions, so the ring alternates cleanly.
        var count = Math.Min(value.Length, capital.Count);

        if (count < 2)
        {
            return;
        }

        var colour = value[count - 1].Y <= capital[count - 1].Y ? loss : gain;

        var ring = new Vector2[(count * 2) + 1];

        for (var i = 0; i < count; i++)
        {
            ring[i] = new Vector2((float)value[i].X, (float)value[i].Y);
        }

        for (var i = count - 1; i >= 0; i--)
        {
            ring[count + (count - 1 - i)] = new Vector2((float)capital[i].X, (float)capital[i].Y);
        }

        // Close along the left edge so the fill is a closed region, not a bow-tie when
        // the lines cross.
        ring[^1] = ring[0];

        using var geometry = CanvasGeometry.CreatePolygon(session, ring);

        session.FillGeometry(geometry, Ink.Fade(colour, 0.14 * opacity));
    }

    private static void DrawPolyline(
        CanvasDrawingSession session, FrameContext context,
        List<(double X, double Y)> points,
        Color colour, CanvasStrokeStyle shared, double opacity)
    {
        if (points.Count < 2)
        {
            return;
        }

        var shape = new Vector2[points.Count];

        for (var i = 0; i < points.Count; i++)
        {
            shape[i] = new Vector2((float)points[i].X, (float)points[i].Y);
        }

        using var geometry = Polyline(session, shape);

        session.DrawGeometry(geometry, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(3), shared);
    }

    /// <summary>
    /// How much of the frame's right-hand side the end labels need, in frame pixels — the
    /// amount the plot gives up so that a label can ride ahead of its own line without
    /// running off the edge.
    ///
    /// Measured from the **final** amounts rather than from this frame's, so the column is the
    /// same width on every frame. A column that grew with the figures would narrow the plot
    /// while the labels were still moving along it, and the lines would slide sideways as they
    /// were being read.
    ///
    /// The right margin already keeps a band empty for the last value, so the plot gives up
    /// only what that margin cannot cover — and never more than a fixed share of its own
    /// width, because past that point a longer name is being answered by shrinking the
    /// picture, which is the wrong end to take it from. When the cap does bite, the labels
    /// give way instead: see <see cref="DrawLabels"/>.
    /// </summary>
    private double LabelColumn(CanvasDrawingSession session, FrameContext context)
    {
        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var widest = 0d;

        // Every holding on the board, not just the ones on this frame: the column has to be
        // the same width before a holding has arrived as after it, or the whole plot would
        // shift the day its line starts.
        foreach (var track in _board.Tracks)
        {
            widest = Math.Max(
                widest,
                LabelWidth(session, context, nameFormat, valueFormat, track.Name, track.Profit));
        }

        var need = widest + context.Px(LabelGap + LabelEdgePad);

        return Math.Clamp(need - context.Margins.Right, 0, context.ChartWidth * 0.45);
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
        var money = Sign(profit) + DcaRenderer.Money(Math.Abs(profit));

        return Ink.Advance(session, name + " ", nameFormat)
               + Ink.Advance(session, money, valueFormat)
               + context.Px(LabelPadX * 2);
    }

    /// <summary>
    /// The name and the figure, riding each line's leading end.
    ///
    /// Placed in one pass and drawn in another, because the boxes have to be kept apart from each
    /// other and that cannot be decided one at a time. Two holdings that ended the day a fraction
    /// apart put their labels in the same place, and the one drawn second covers the first — a
    /// frame with the right number of labels on it and one of them missing. They are pushed down
    /// the frame in the order they came out, which is stable between frames and between runs, and
    /// the whole stack is then slid back inside the plot so a label near the top is not clipped.
    ///
    /// Each one sits **ahead of** its own line's leading end, in the column the plot left for it.
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
            var (points, _, name, profit) = lines[i];

            var width = LabelWidth(session, context, nameFormat, valueFormat, name, profit);

            // The label rides **ahead of** the point it belongs to, in the column the plot was
            // shortened to leave for it: by the end of the animation that column is past the
            // plot's last one, so a label never covers the line it is about.
            //
            // Its right edge is the one that has to stay inside the frame, and it is the one
            // that gives way — measured to the **frame's** edge, not the plot's: the band the
            // right margin keeps empty is where these labels live. A long name with a large
            // amount, and the side margins pushed out, can leave the column narrower than the
            // widest label, and then the label slides back over the point rather than off the
            // edge of the picture.
            var left = Math.Min(
                anchors[i].X + context.Px(LabelGap),
                context.Width - context.Px(LabelEdgePad) - width);

            boxes.Add(new Rect(Math.Max(context.ChartLeft, left), anchors[i].Y, width, height));
        }

        // Push apart, top to bottom. The order is by where the labels would have gone, and it is
        // kept: a label pushed past its neighbour never overtakes it.
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

            var money = Sign(profit) + DcaRenderer.Money(Math.Abs(profit));

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

        var mx = context.ChartLeft;
        var y = top - context.Px(24);
        var x = mx;
        var swatch = context.Px(34);

        using var format = Ink.Format(context.Px(21));

        // With one holding, what each line is — the same pair this has always shown. With
        // several, only the capital: every curve is named by the label riding its own end, at
        // the place the eye already is, and eight names in a row above the plot would be a
        // legend longer than the chart it describes.
        var entries = _board.Comparing
            ? new[] { (Palette.Moving, "PositionLegendCapital") }
            : [(Gain, "DcaLegendValue"), (Palette.Moving, "PositionLegendCapital")];

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
        CanvasDrawingSession session, FrameContext context, double t, double bottom, double plotW,
        double introA, double count, double first, double head)
    {
        var n = _board.Dates.Count;
        var mx = context.ChartLeft;

        // About five labels across the window in view — the window, not the whole span. A
        // scrolling chart of a decade has to have its dates read off the sixty days on screen,
        // and the every-hundred-and-fortieth-day rule that suits the whole range leaves that
        // window with none at all.
        //
        // The step is taken over the window's length **rounded**, because how far apart
        // labels go is a whole-number question; the placing below still uses `count`,
        // which is fractional while a scrolling window is opening out.
        var whole = Math.Max(1, (int)Math.Round(count));

        var every = Math.Max(1, whole / 5);
        if (whole % every == 0 && whole / every > 5)
        {
            every = Math.Max(1, (whole / 6) + 1);
        }

        // A year label when the holding spans years, year-and-month when it spans less —
        // twelve "2024-06" stamps on a decade-long holding is noise nobody reads.
        var longSpan = _board.End.DayNumber - _board.Start.DayNumber > 365 * 3;

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < n; i += every)
        {
            // The stamps keep their days rather than their slots: a label is placed where its
            // own date falls, so the row slides with the window instead of being dealt out
            // again each frame — which is also why the step is taken over the whole axis.
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
            var text = longSpan ? day.Year.ToString(CultureInfo.InvariantCulture) : day.ToString("yyyy-MM", CultureInfo.InvariantCulture);
            var x = mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

            Ink.Centred(session, text, x, bottom + context.Px(28), format, Palette.DateLabel, a);
        }
    }

    // ---- header ---------------------------------------------------------------------

    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t, Plot plot)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : DefaultTitle();

        if (ShowTitle)
        {
            var titleSize = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(titleSize, bold: true))
            {
                Ink.Centred(session, title, cx, Row(context, 0.155), format, Palette.Title, a);
            }
        }

        using var small = Ink.Format(context.Px(25));

        // What the holdings are: when they were bought, for how much, of what, in whose
        // currency. One date for all of them, because they are all bought on the board's own
        // first trading day — except the ones that listed later, whose own line starts on their
        // first day and says so by where it starts.
        var heldLine = _board.Comparing
            ? Strings.Format(
                "PositionCompareSubtitle",
                DcaRenderer.Money(_board.Capital),
                Strings.Get(CurrencyKey),
                Iso(_board.Start))
            : Strings.Format(
                "PositionSubtitleLine",
                Iso(_board.Start),
                DcaRenderer.Money(_board.Capital),
                Strings.Get(CurrencyKey),
                _board.Tracks[0].Name);

        Ink.Centred(session, heldLine, cx, Row(context, 0.19), small, Palette.Muted, a);

        // The span, with the days held as the figure the eye stops on.
        var days = (_board.End.DayNumber - _board.Start.DayNumber).ToString("#,##0", CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session,
                Strings.Format("PositionRangeLine", Iso(_board.Start), Iso(_board.End), days),
                days,
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
            // The middle of the air between the holding's range line and the running figure
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

        // The headline: with one holding, what it is worth over what went in, read off the
        // moment being shown — its colour follows the sign of what is displayed, so a holding
        // crossing from loss to gain changes the colour of its own number. With several, the
        // one furthest ahead and the money it has made, because a percentage cannot be about
        // six things at once.
        var leader = -1;
        var best = double.NegativeInfinity;

        for (var i = 0; i < plot.Values.Length; i++)
        {
            // `NaN` is a holding that has not arrived; a comparison of it with anything is
            // false, so it never wins — which is what "not on the frame yet" should mean.
            if (plot.Values[i] > best)
            {
                best = plot.Values[i];
                leader = i;
            }
        }

        if (leader < 0)
        {
            return;
        }

        string text;
        Color colour;
        string label;

        if (_board.Comparing)
        {
            var profit = plot.Values[leader] - _board.Capital;

            text = Sign(profit) + DcaRenderer.Money(Math.Abs(profit));
            colour = profit >= 0 ? Gain : Loss;
            label = Strings.Format("PositionLeaderLine", _board.Tracks[leader].Name);
        }
        else
        {
            var ret = _board.Capital > 0 ? ((plot.Values[leader] / _board.Capital) - 1) * 100 : 0;

            text = (ret >= 0 ? "+" : string.Empty) + ret.ToString("0.0", CultureInfo.InvariantCulture) + "%";
            colour = ret >= 0 ? Gain : Loss;
            label = Strings.Get("DcaReturnLabel");
        }

        using (var bigFormat = Ink.Format(context.Px(128), bold: true))
        {
            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, colour));

            Ink.Centred(session, text, cx, Row(context, 0.327), bigFormat, colour, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, label, cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    /// <summary>“持仓收益：中国平安” — what the frame says when no title was typed.</summary>
    private string DefaultTitle() => Strings.Format("PositionDefaultTitle", _board.Tracks[0].Name);

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
            DrawTrackCards(session, context, a, left, gap, y, cardHeight, valueFormat);

            DrawCredit(session, context, a);

            return;
        }

        // One holding: the four figures that describe it. 期末市值 and 投入本金 are its two
        // levels, 历史净收益 their difference, and 最大回撤 what it cost to get there — the
        // drawdown is shown as the negative it is a percentage of, not as a magnitude with a
        // minus painted on, so that "-31.2%" next to "+143.7%" lets the two signs carry the
        // story.
        var track = _board.Tracks[0];
        var cards = new[]
        {
            (Strings.Get("PositionCardValue"), DcaRenderer.Money(track.FinalValue), Palette.CardValue),
            (Strings.Get("PositionCardCapital"), DcaRenderer.Money(_board.Capital), Palette.CardValue),
            (Strings.Get("DcaCardProfit"), Sign(track.Profit) + DcaRenderer.Money(Math.Abs(track.Profit)),
                track.Profit >= 0 ? Gain : Loss),
            (Strings.Get("PositionCardDrawdown"),
                (-track.MaxDrawdownPct).ToString("0.0", CultureInfo.InvariantCulture) + "%", Loss),
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
    /// A comparison's closing row: one card per holding, in the colour of its own line.
    ///
    /// The four single-holding cards answer "what did this cost me and what did it cost me along
    /// the way", over two levels, their difference and a drawdown. None of those is a comparison:
    /// the capital is the same on every card, and one drawdown among six holdings cannot be the
    /// frame's closing figure. So the row becomes the six answers to the question the page was
    /// actually asked — who made how much — and the money figure repeats the label riding each
    /// line, which is what makes it checkable at a glance.
    /// </summary>
    private void DrawTrackCards(
        CanvasDrawingSession session, FrameContext context, double a,
        double left, double gap, double y, double cardHeight,
        CanvasTextFormat valueFormat)
    {
        var tracks = _board.Tracks;
        var cardWidth = (context.ChartWidth - (gap * (tracks.Count - 1))) / tracks.Count;

        using var returnFormat = Ink.Format(context.Px(24));

        for (var i = 0; i < tracks.Count; i++)
        {
            var track = tracks[i];
            var x = left + (i * (cardWidth + gap));
            var box = new Rect(x, y, cardWidth, cardHeight);
            var radius = (float)context.Px(14);
            var ink = Palette.Track(i);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, a));
            session.DrawRoundedRectangle(box, radius, radius, Ink.Fade(ink, 0.75 * a), (float)context.Px(1.5));

            // A company name in English is wider than a card at six columns, and a name that
            // runs past its own border reads as a broken layout rather than as a long name.
            var nameSize = Ink.FitSize(session, track.Name, context.Px(22), cardWidth - context.Px(20), bold: false);

            using (var fitted = Ink.Format(nameSize))
            {
                Ink.Centred(session, track.Name, x + (cardWidth / 2), y + context.Px(40), fitted, Palette.Muted, a);
            }

            Ink.Centred(
                session,
                Sign(track.Profit) + DcaRenderer.Money(Math.Abs(track.Profit)),
                x + (cardWidth / 2), y + context.Px(80), valueFormat, ink, a);

            Ink.Centred(
                session,
                (track.ReturnPercent >= 0 ? "+" : string.Empty)
                    + track.ReturnPercent.ToString("0.0", CultureInfo.InvariantCulture) + "%",
                x + (cardWidth / 2), y + context.Px(114), returnFormat, Palette.Muted, a);
        }
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

    private double Row(FrameContext context, double fraction) => context.HeaderRow(fraction, ShowTitle);

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
