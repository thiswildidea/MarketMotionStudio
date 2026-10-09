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
    /// <summary>
    /// Distance from the chart baseline down to the credit, in baseline pixels: the date row, the
    /// cards, and the credit under them.
    ///
    /// The two distances <see cref="TrackCards"/> states, and the same total the
    /// single-instrument chart reserves, so that the two pictures this one page draws end on the
    /// same furniture in the same place. It used to be 150 — the date row alone — because this
    /// frame had nothing else to say at the bottom, and a comparison that ends without its
    /// figures is half a frame.
    /// </summary>
    public const double CreditGap = TrackCards.CreditGap;

    /// <summary>
    /// Where the plot area starts, as a fraction of frame height.
    ///
    /// It was 0.30, measured against a header whose last line was 22 px. That line is now the
    /// frame's headline figure at <see cref="CandleLine.MomentSize"/> — the same 128 the frames
    /// that state one figure state it at — so the plot starts lower by the air a 128-pixel line
    /// takes. The plot gives up 0.04 of the frame and the header stops drawing through itself;
    /// see <see cref="CandleLine.MomentRow"/>.
    /// </summary>
    private const double PlotTopFraction = 0.34;

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
        _giveWay = CandleLine.GiveWay(t, _plan, _motion, _crossSafeRight);

        var plotW = Math.Max(1, context.ChartWidth - CandleLine.LabelColumn(
            session, context, [.. _board.Tracks.Select(track => (track.Name, track.Final))], _giveWay));
        var introA = Easing.Ramp(t, 0, 1000);

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

        var eased = new double[Math.Max(1, moving + 1)];

        for (var i = 0; i <= moving; i++)
        {
            eased[i] = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));
        }

        // The window: shared with the two pages offering the same choice, so that a motion
        // means the same thing everywhere it is offered.
        //
        // Computed up here rather than where it is drawn from, because the header states the moment
        // the window has rolled to and is drawn before the plot. `-1` before the first point has
        // arrived is not a window; it is the absence of one, and the header is handed a real minute
        // either way.
        var (count, head, first) = moving < 0
            ? ((double)n, -1d, 0d)
            : _plan.Window(_motion is CandleMotion.Scroll, _window, n, moving + eased[moving], t);

        CandleLine.Header(
            session, context, _title, _board, ResolvedTitle(), ShowTitle, _titleLines, t,
            Math.Max(0, head));

        var (lo, hi, step) = Bounds();

        double Level(double value) => bottom - (((value - lo) / (hi - lo)) * span);

        CandleLine.Axis(session, context, lo, hi, step, Level, plotW, introA);

        if (moving < 0)
        {
            CandleLine.XLabels(session, context, _board, _plan, t, bottom, plotW, introA, n, 0, -1);
            DrawClosing(session, context, t);
            DrawProgress(session, context, t);

            return;
        }

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
                CandleLine.Curve(session, context, drawn, colour, introA);
            }

            var (lx, ly) = (drawn[^1].X, drawn[^1].Y - context.Px(4));

            anchors.Add((lx, ly));

            void Dot(CanvasDrawingSession ds) =>
                ds.FillCircle((float)lx, (float)ly, (float)context.Px(6), white);

            Ink.Glow(session, context.Px(10), 0.9 * introA, Dot);
            Dot(session);

            lines.Add((drawn, colour, track.Name, value));
        }

        CandleLine.EndLabel(session, context, lines, anchors, top, bottom, introA, _giveWay);
        CandleLine.XLabels(session, context, _board, _plan, t, bottom, plotW, introA, count, first, head);
        DrawClosing(session, context, t);
        DrawProgress(session, context, t);
    }

    /// <summary>
    /// What the frame ends on: one card per instrument, and the credit under them.
    ///
    /// The figures on the cards are the **final** ones — <see cref="CandleTrack.Final"/> over
    /// <see cref="CandleTrack.Baseline"/> — and deliberately not this frame's, which is the
    /// opposite of the rule the labels riding the curves obey. A label is a reading of the moment
    /// being drawn and has to agree with the line beside it; a closing card is the answer to "so
    /// how did they finish", and one that was still moving while the range opened out would be
    /// the one figure on the frame a viewer could not write down.
    ///
    /// The amount under the percentage is what that percentage is of: the same figure the axis
    /// and the candles on the single-instrument chart are quoted in, so that "-0.79%" and the
    /// index points it moved by appear together rather than on two different pages.
    /// </summary>
    private void DrawClosing(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = ClosingOpacity(t);

        if (a <= 0)
        {
            return;
        }

        var cards = new List<TrackCards.Card>(_board.Tracks.Count);

        for (var i = 0; i < _board.Tracks.Count; i++)
        {
            var track = _board.Tracks[i];
            var ink = Palette.Track(i);

            cards.Add(new TrackCards.Card(
                track.Name,
                Ink.Fade(ink, 0.55),
                ink,
                CandleLine.Percent(track.Final),
                Amount(track.Baseline * track.Final / 100)));
        }

        TrackCards.Draw(session, context, cards, a, _giveWay);

        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    /// <summary>
    /// How much of the closing row has arrived: the credit and the cards come in together, a
    /// little after the last curve's label has settled, the way every other frame's figures do.
    /// </summary>
    private double ClosingOpacity(double t) => Easing.Ramp(t, _plan.FinaleStartMs + 1900, 900);

    /// <summary>A price difference with its sign always shown, as the percentages beside it have.</summary>
    private static string Amount(double value) =>
        (value >= 0 ? "+" : string.Empty) + CandleLoader.Price(value);

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

    // ---- the rest of the frame ------------------------------------------------------

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
    /// What the frame is about: what the user typed, or the instruments' names. One place,
    /// because the text measured at the top of <see cref="Draw"/> and the text drawn in the
    /// header have to be the same string.
    /// </summary>
    private string ResolvedTitle() =>
        Title.Length > 0 ? Title : string.Join(" / ", _board.Tracks.Select(t => t.Name));
}
