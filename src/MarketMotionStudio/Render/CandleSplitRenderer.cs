using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// Several instruments' moves, one to a panel, stacked.
///
/// The other half of <see cref="CandleRaceRenderer"/>, and the answer to what that one cannot do:
/// a percentage axis shared by every curve is what makes them comparable, and it is also what
/// makes the quiet ones unreadable. An instrument that spent three years inside a two per cent
/// band, drawn against a neighbour that ran thirty, is a straight line — and it is a straight line
/// on the axis where its own shape is the thing the reader came for.
///
/// So each panel gets its own axis, scaled to its own range with zero still inside it, and the
/// panels are stacked in the order the instruments were picked. **The x axis is not duplicated**:
/// the dates belong to the frame, appear once under the bottom panel, and every panel is drawn
/// across the same width, so a moment is at one x on the whole picture and the panels can be read
/// up and down as well as along.
///
/// Which is why the plot gives up one label column for the whole frame rather than one per panel:
/// a per-panel column would make the panels different widths, and the dates under them would then
/// be three different scales with one label row.
///
/// The end label is <see cref="CandleLine.EndLabel"/>, the same box the overlaid frame rides its
/// curves with, clamped to its own panel instead of to the plot. Nothing else about the two
/// layouts differs: the pacing, the window, the scroll, the safe line and the closing cards are
/// one set of decisions, whichever way the instruments are arranged.
/// </summary>
public sealed class CandleSplitRenderer : IFrameRenderer
{
    /// <summary>Distance from the chart's foot down to the credit: the date row, the cards, the credit.</summary>
    public const double CreditGap = TrackCards.CreditGap;

    /// <summary>
    /// Where the panels start, as a fraction of frame height. Back to 0.30 with the header's last
    /// line: it was 0.34 while that line was set at headline size, and a comparison of three
    /// panels has less room per panel than one chart has, not more. See
    /// <see cref="CandleLine.ClockRow"/>.
    /// </summary>
    private const double PlotTopFraction = 0.30;

    /// <summary>
    /// Air between two panels, in baseline pixels.
    ///
    /// Wide enough to hold two things that would otherwise be read as one: the label riding the
    /// foot of the panel above, which is clamped to that panel rather than to the plot, and the
    /// topmost gridline of the one below.
    /// </summary>
    private const double PanelGap = 46;

    /// <summary>
    /// How many ticks a panel's axis is asked for. Fewer than the overlaid frame's four, because a
    /// panel is a third of the height and a scale with seven lines in it is a grid with a curve
    /// lost in it.
    /// </summary>
    private const int PanelTicks = 3;

    /// <summary>A panel's axis figures, smaller than a full-height plot's.</summary>
    private const double PanelAxisSize = 18;

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
    /// Whether the picture may run into the band the host covers with its button rail — the same
    /// choice, made in the same place, as the overlaid frame's.
    /// </param>
    public CandleSplitRenderer(
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
        var mx = context.ChartLeft;

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

        // The window and the easing are the overlaid frame's own, one window for the frame rather
        // than one per panel: three windows rolling at three different positions would be three
        // pictures of three different stretches of time under one row of dates.
        var eased = new double[Math.Max(1, moving + 1)];

        for (var i = 0; i <= moving; i++)
        {
            eased[i] = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));
        }

        // Computed up here rather than where it is drawn from, because the header states the moment
        // the window has rolled to and is drawn before any panel. `-1` before the first point has
        // arrived is not a window; it is the absence of one, and the header is handed a real minute
        // either way.
        var (count, head, first) = moving < 0
            ? ((double)n, -1d, 0d)
            : _plan.Window(_motion is CandleMotion.Scroll, _window, n, moving + eased[moving], t);

        CandleLine.Header(
            session, context, _title, _board, ResolvedTitle(), ShowTitle, _titleLines, t,
            Math.Max(0, head));

        // The instruments the frame is about. The page has already taken the board down to
        // MostPanels where there were more picks than panels; the clamp is here as well so that a
        // renderer handed a wider board draws three panels rather than three panels and a fourth
        // on top of one of them.
        var tracks = _board.Tracks.Take(CandleBoardLoader.MostPanels).ToList();

        if (tracks.Count == 0)
        {
            DrawProgress(session, context, t);

            return;
        }

        var left = Math.Max(0, (int)Math.Ceiling(first));

        // The panels share the height they are given, and the gaps come off it first, so that a
        // frame of two has two tall panels rather than two short ones floating in the middle.
        var span = Math.Max(1, bottom - top);
        var band = (span - (PanelGap * (tracks.Count - 1))) / tracks.Count;
        var pitch = band + PanelGap;

        for (var k = 0; k < tracks.Count; k++)
        {
            var panelTop = top + (k * pitch);
            var panelBottom = panelTop + band;

            DrawPanel(session, context, tracks[k], k, panelTop, panelBottom, mx, plotW,
                count, first, left, moving, eased, introA);
        }

        // Once, under the bottom panel: the axis is the frame's, not a panel's.
        CandleLine.XLabels(session, context, _board, _plan, t, bottom, plotW, introA, count, first, head);

        DrawClosing(session, context, t);
        DrawProgress(session, context, t);
    }

    /// <summary>
    /// One instrument in its own band: its axis, its curve, and the label riding the curve's end.
    /// </summary>
    private void DrawPanel(
        CanvasDrawingSession session, FrameContext context, CandleTrack track, int order,
        double panelTop, double panelBottom, double mx, double plotW,
        double count, double first, int left, int moving, double[] eased,
        double introA)
    {
        var (lo, hi, step) = Bounds(track);
        var span = Math.Max(1, panelBottom - panelTop);

        double Level(double value) => panelBottom - (((value - lo) / (hi - lo)) * span);

        CandleLine.Axis(session, context, lo, hi, step, Level, plotW, introA, PanelAxisSize);

        double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);

        // Nothing of this instrument on the frame yet: before its own first bar the panel holds
        // its axis and no curve, which is what "not listed yet" looks like everywhere else.
        if (moving < track.First)
        {
            return;
        }

        var from = Math.Max(track.First, left);
        var to = Math.Min(moving, track.Last);

        if (to < from)
        {
            return;
        }

        var colour = Palette.Track(order);
        var points = new List<(double X, double Y)>(to - from + 1);
        var value = 0d;

        for (var i = from; i <= to; i++)
        {
            var v = track.Returns[i];

            // The arriving point eases in from the previous one's level, not from zero — see the
            // overlaid frame, where the same line is drawn for the same reason.
            if (i == moving && i > track.First)
            {
                var before = track.Returns[i - 1];

                v = before + ((v - before) * eased[Math.Min(i, eased.Length - 1)]);
            }

            value = v;
            points.Add((Across(i), Level(v)));
        }

        var white = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);
        var drawn = points.ToArray();

        CandleLine.Curve(session, context, drawn, colour, introA);

        var (lx, ly) = (drawn[^1].X, drawn[^1].Y - context.Px(4));

        void Dot(CanvasDrawingSession ds) =>
            ds.FillCircle((float)lx, (float)ly, (float)context.Px(6), white);

        Ink.Glow(session, context.Px(10), 0.9 * introA, Dot);
        Dot(session);

        // Clamped to this panel and not to the plot: a label pushed down out of a panel would land
        // on the one below it, looking like that panel's — the one thing a stack of panels must not
        // let happen.
        CandleLine.EndLabel(
            session, context,
            [(drawn, colour, track.Name, value)],
            [(lx, ly)],
            panelTop, panelBottom, introA, _giveWay);
    }

    /// <summary>
    /// One panel's scale: a round interval covering everything this instrument did, in both
    /// directions, with zero inside it and at least one step either side.
    ///
    /// Its own axis rather than a share of the frame's, which is the whole point of the layout.
    /// The floor of one step keeps an instrument that barely moved from being drawn as a dramatic
    /// climb up a scale of its own minimum and maximum, and zero inside it keeps the picture
    /// honest about which way the move went: a line that hugs the middle of its panel is a move
    /// against its own range, and one that is nowhere near the zero line is a move that happened
    /// before the range began.
    /// </summary>
    private static (double Lo, double Hi, double Step) Bounds(CandleTrack track)
    {
        var reach = Math.Max(Math.Abs(track.Peak), Math.Abs(track.Trough)) * 1.08;
        var (step, _) = AnimationPlan.NiceScale(Math.Max(reach, 0.5), PanelTicks);

        var hi = Math.Max(step, Math.Ceiling(track.Peak / step) * step);
        var lo = Math.Min(-step, Math.Floor(track.Trough / step) * step);

        return (lo, hi, step);
    }

    /// <summary>
    /// What the frame ends on: one card per **panel**, and the credit under them.
    ///
    /// Per panel and not per picked instrument, because the frame is only about the ones it drew —
    /// a card for a track with no panel would be a figure with nothing on the picture to read it
    /// against. The figures are the final ones; see <see cref="CandleRaceRenderer"/>.
    /// </summary>
    private void DrawClosing(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var drawn = _board.Tracks.Take(CandleBoardLoader.MostPanels).ToList();
        var cards = new List<TrackCards.Card>(drawn.Count);

        for (var i = 0; i < drawn.Count; i++)
        {
            var track = drawn[i];
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

    /// <summary>A price difference with its sign always shown, as the percentages beside it have.</summary>
    private static string Amount(double value) =>
        (value >= 0 ? "+" : string.Empty) + CandleLoader.Price(value);

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
    /// What the frame is about: what the user typed, or the instruments' names — the same fallback
    /// the overlaid frame uses, so that switching the layout does not rename the video.
    /// </summary>
    private string ResolvedTitle() =>
        Title.Length > 0 ? Title : string.Join(" / ", _board.Tracks.Select(t => t.Name));
}
