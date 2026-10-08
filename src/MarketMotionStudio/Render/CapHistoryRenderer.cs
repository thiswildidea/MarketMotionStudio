using System.Globalization;
using System.Numerics;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// One instrument's circulating market value and the price it was taken at, as two
/// stacked panels sharing one time axis — the page that answers "how big did this
/// company get, and was that the share price or the share count".
///
/// Two panels rather than two lines in one plot because the two figures do not share
/// a unit. A value in 亿 and a price in 元 can be drawn on one pair of axes only by
/// giving one of them a second, private scale, and a chart whose two lines are held
/// apart by an invisible rescaling invites exactly the comparison this page exists to
/// invite — while making it mean nothing. Two panels put the two shapes side by side
/// on one shared axis, which is the comparison, and let each keep its own labelled
/// scale, which is what makes it honest.
///
/// The geometry is the per-stock page's: panel top at 0.278 of frame height, mid gap
/// at 0.081, 107 baseline pixels between the lower panel's baseline and the credit.
/// Copied rather than re-derived because it was tuned by watching.
///
/// Nothing here names the figures it draws. Every word that describes the data — the
/// panels' names, their units, the word for the period counted in the header —
/// arrives from the page, because a shared renderer that wrote its own would describe
/// the wrong data on whichever page came to share it: the market-cap board once drew
/// twelve months as "12 个交易日" out of a line this class had no business writing.
/// The only strings resolved in here are ones no page's data can change.
///
/// **Each instrument's figure rides its own line**, as a capsule at the point the curve
/// has reached. With one instrument that is an addition to what this frame always said —
/// the big figure over the panel is still the running one, and the capsule says the same
/// number beside the line, so the two cannot disagree. With several, the capsules are
/// the only thing that can say which curve is which *and* where it stands at the moment
/// being shown. What they name is the value **at that moment**, not the value the series
/// ends at: a capsule that reported the last day from the first frame on would be a
/// number the curve had not got anywhere near yet.
/// </summary>
/// <summary>
/// Which reading of the value panel's vertical axis the frame draws.
///
/// <see cref="Absolute"/> is the figure itself, in the venue's own 亿 — what a company
/// was worth, which is what the page was built to show and what lets two lines be read
/// as one being bigger than the other.
///
/// <see cref="Normalized"/> rebases every line to 100 at its own first day, which is
/// the other half of that comparison and the only readable one past a certain spread:
/// put 工商银行's 2.3 万亿 beside 五粮液's roughly 2,700 亿 on one absolute axis and the
/// second is a flat line along the bottom, which reads as "nothing happened" about a company
/// that grew several-fold and then gave most of it back. Rebased, both fill the panel
/// and the question becomes whose value grew faster.
///
/// A constructor argument and never a settable property. The frame's scale, its unit
/// word and how its numbers are written are all decided once, from this, in the
/// constructor — so a page that assigned it after constructing the renderer got the
/// default reading of every one of them and could not tell: the picture was drawn from
/// a switch that had silently not been set, and every control around it still reported
/// exactly what it should. It is passed like a plan for the same reason a motion is.
/// </summary>
public enum CapAxis
{
    /// <summary>The value itself, in 亿 of the venue's own currency.</summary>
    Absolute = 0,

    /// <summary>The value rebased to 100 at the instrument's own first day.</summary>
    Normalized = 1,
}

public sealed class CapHistoryRenderer : IFrameRenderer
{
    /// <summary>Baseline rows between the lower panel's baseline and the credit.</summary>
    private const double CreditGap = 107;

    private const double PanelTopFraction = 0.278;

    private const double PanelMidFraction = 0.081;

    /// <summary>The widest the comparison's label column may get, as a share of the plot.</summary>
    private const double MostLabelShare = 0.45;

    /// <summary>Font size, in baseline rows, of a comparison's end labels.</summary>
    private const double LabelSize = 22;

    /// <summary>Baseline rows between a line's leading end and its label.</summary>
    private const double LabelGap = 16;

    /// <summary>Baseline rows kept clear between the frame's right edge and a label.</summary>
    private const double LabelEdgePad = 10;

    /// <summary>Baseline rows inside a label box, and between two of them.</summary>
    private const double LabelPadX = 10;

    private const double LabelPadY = 6;

    private const double LabelBetween = 8;

    /// <summary>
    /// How thick a capsule's outline is, and why it is not the hairline a card uses: a
    /// capsule sits in front of a curve drawn in its own colour, so the outline is the
    /// only thing keeping the two apart — and these frames are watched as video, at
    /// whatever size the player happens to be.
    /// </summary>
    private const double LabelEdge = 3;

    private readonly CapBoard _board;

    private readonly AnimationPlan _plan;

    private readonly bool _comparing;

    private readonly bool _normalized;

    private readonly (double Step, double Top) _capScale;

    private readonly (double Step, double Top) _priceScale;

    private readonly string[] _labels;

    /// <summary>
    /// Each instrument's value figure for every position of the board's axis, already
    /// read for whatever axis was chosen.
    ///
    /// Taken out of the board once, here. A frame asks for them several times over —
    /// the curve, the mean, each extreme, and once per instrument when comparing — and
    /// a series of a few thousand points rebuilt per question per frame is a few
    /// thousand allocations a second for the length of a video.
    ///
    /// Normalization belongs here rather than in the board it came from. The board is
    /// what the source said; this is one of two ways to look at it, and keeping the
    /// second reading out of the data means a frame cannot be drawn against a figure
    /// that was quietly rewritten before it got here.
    /// </summary>
    private readonly double[][] _caps;

    private readonly double[][] _prices;

    /// <summary>The wrapped headline.</summary>
    private readonly TitleBlock _title = new(64);

    /// <summary>
    /// How many lines the title took on the frame being drawn — what every header row
    /// and the panels' top edge are moved by. Set once at the top of <see cref="Draw"/>.
    /// </summary>
    private int _titleLines;

    public CapHistoryRenderer(CapBoard board, AnimationPlan plan, CapAxis axis = CapAxis.Absolute)
    {
        _board = board;
        _plan = plan;
        _comparing = board.Comparing;
        _normalized = axis is CapAxis.Normalized;

        // Each axis of its own: one step for both would leave one reading's gridlines
        // disagreeing with its own data, which reads as that reading being wrong — and
        // on this page the value and the price are different quantities, so no shared
        // scale exists to be tempted by. Comparing, there is no price panel at all.
        _caps = Display(board, axis, price: false);
        _prices = _comparing ? [] : Display(board, axis, price: true);

        var capPeak = board.Comparing
            ? _caps.Max(v => v.Max())
            : _caps[0].Max();

        _capScale = AnimationPlan.NiceScale(Math.Max(capPeak, 0.0001) * 1.08, 4);
        _priceScale = _comparing
            ? (1, 1)
            : AnimationPlan.NiceScale(Math.Max(_prices[0].Max(), 0.0001) * 1.08, 4);

        _labels = Labels(board);
    }

    /// <summary>
    /// One instrument's figures read for the chosen axis.
    ///
    /// Rebasing divides by the instrument's own first figure rather than by the board's
    /// first day's, because a company that listed halfway through the range has no value
    /// on that day — dividing by the zero the array holds outside the instrument's own
    /// stretch would answer infinity about a listing and nothing at all about the others.
    /// Positions the instrument does not cover stay zero and are still never read.
    /// </summary>
    private static double[][] Display(CapBoard board, CapAxis axis, bool price)
    {
        var tracks = board.Tracks;
        var taken = new double[tracks.Count][];

        for (var i = 0; i < tracks.Count; i++)
        {
            var source = price ? tracks[i].Price : tracks[i].Cap;
            var rebased = new double[source.Count];
            var basis = source[tracks[i].First];

            for (var at = tracks[i].First; at <= tracks[i].Last; at++)
            {
                rebased[at] = axis is CapAxis.Normalized && basis > 0
                    ? source[at] / basis * 100.0
                    : source[at];
            }

            taken[i] = rebased;
        }

        return taken;
    }

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>The venue-prefixed code shown in the header line.</summary>
    public string Code { get; set; } = string.Empty;

    /// <summary>The upper panel's name, from the page. Not resolved here.</summary>
    public string CapWord { get; set; } = string.Empty;

    /// <summary>The upper panel's unit, from the page — 亿元, 亿港元, and so on.</summary>
    public string CapUnitWord { get; set; } = string.Empty;

    /// <summary>The lower panel's name, from the page: 股价, or 成交均价 where a close
    /// is not what the series carries.</summary>
    public string PriceWord { get; set; } = string.Empty;

    /// <summary>The lower panel's unit, from the page.</summary>
    public string PriceUnitWord { get; set; } = string.Empty;

    /// <summary>The word for what the header counts — 个交易日, 个月 — from the page.</summary>
    public string SpanWord { get; set; } = string.Empty;

    /// <summary>The headline this frame draws: what the user typed, or the instrument's name.</summary>
    private string ResolvedTitle() =>
        Title.Length > 0 ? Title : _board.Tracks[0].Name;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        // Before the panels: their top edge is placed against the bottom of the header
        // block, which is placed by how many lines the title took.
        _titleLines = _title.For(session, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session, context, Palette.StockBackground);

        // A comparison gives the whole area to the value panel. Two panels answered
        // "how big did this company get, and was that the price or the share count" —
        // a question about *one* company's two figures. Once several are on the frame
        // the price has nowhere honest to go: 贵州茅台 at 1,258 元 beside 京东方A at 4.2
        // 元 puts the second flat along the bottom, which is a claim about a company
        // rather than about the two axes. So there is one panel and it is twice as tall.
        // Reserved before anything is drawn, and reserved once: the capsules ride ahead
        // of the curve's end, and the room for them has to be the same on the first frame
        // as on the last, or the plot would slide sideways while it was being read. Both
        // of the single page's panels give up the same width, because their capsules are
        // measured from the same instrument and drawn in the same place.
        var column = LabelColumn(session, context);

        var moving = _comparing
            ? DrawComparison(session, context, t, column)
            : DrawPanels(session, context, t, column);

        DrawXLabels(session, context, t, column);
        DrawFooter(session, context, t);
        DrawHeader(session, context, t, moving);
        DrawProgress(session, context);
    }

    /// <summary>
    /// The single instrument's two stacked panels, exactly as this page has always drawn
    /// them: value above, price below, the mean and both extremes named on each.
    /// </summary>
    private int DrawPanels(CanvasDrawingSession session, FrameContext context, double t, double column)
    {
        var moving = DrawPanel(session, context, t, column, isPrice: false);

        DrawPanel(session, context, t, column, isPrice: true);

        return moving;
    }

    /// <summary>The two panels' rectangles. The gap between them is fixed; the bottom
    /// margin decides where the lower one ends and the two share what is left equally.</summary>
    private (double Top, double Bottom) PanelArea(FrameContext context, bool isPrice)
    {
        var top = context.HeaderRow(PanelTopFraction, _titleLines);
        var bottom = context.CreditLine - context.Px(CreditGap);
        var span = (bottom - top - context.Height * PanelMidFraction) / 2;

        return isPrice ? (bottom - span, bottom) : (top, top + span);
    }

    /// <summary>One instrument's two figures as this frame will read them.</summary>
    private double[] Values(bool isPrice) =>
        isPrice ? _prices[0] : _caps[0];

    /// <summary>
    /// The comparison: one value panel, several lines, each named at its own leading end.
    ///
    /// What leaves the frame along with the price panel is the mean and the two extremes
    /// the single page puts on each panel. Those are three numbered marks about one
    /// company's shape; six companies turn them into eighteen numbers over one another,
    /// and a frame nobody can read has not answered anything. The comparison names each
    /// line at its end instead — the same word the line is drawn in — which says which
    /// company is which and where it has got to, and nothing else tries to speak.
    /// </summary>
    private int DrawComparison(CanvasDrawingSession session, FrameContext context, double t, double column)
    {
        var top = context.HeaderRow(PanelTopFraction, _titleLines);
        var bottom = context.CreditLine - context.Px(CreditGap);
        var span = bottom - top;
        var introA = Easing.Ramp(t, 500, 1500);

        if (introA <= 0)
        {
            return -1;
        }

        var n = _labels.Length;

        // The plot stops short of the right edge by the width of the capsules' column, so
        // that one can ride ahead of its own line without ever leaving the frame.
        var mx = context.ChartLeft;
        var plotW = Math.Max(1, context.ChartWidth - column);
        var slot = plotW / Math.Max(1, n);

        DrawGrid(session, context, _capScale, mx, plotW, top, bottom, introA, false);

        // How far along the axis the animation has come. Every line shares it: they are
        // one comparison on one axis, and a frame where one company had reached Tuesday
        // while another was still at January would be two different dates pretending to
        // be one.
        var moving = -1;

        for (var i = 0; i < n; i++)
        {
            if (t <= _plan.IntroMs + (i * _plan.StaggerMs))
            {
                break;
            }

            moving = i;
        }

        var lines = new List<(List<(double X, double Y)> Points, Color Colour)>(_board.Tracks.Count);
        var ends = new List<CapEnd>(_board.Tracks.Count);

        foreach (var index in Enumerable.Range(0, _board.Tracks.Count))
        {
            var track = _board.Tracks[index];
            var values = _caps[index];

            // Nothing before this company's own first day, and nothing beyond the point
            // the animation has reached. A line drawn flat before it listed would be a
            // claim about years it did not exist for.
            if (track.First > moving)
            {
                continue;
            }

            var last = Math.Min(moving, track.Last);
            var points = new List<(double X, double Y)>(last - track.First + 1);

            for (var i = track.First; i <= last; i++)
            {
                // A point joins its line once it has finished rising — the same rule the
                // single panel got, and for the same reason: a curve drawn at a partial
                // height falls from the day before it to the axis inside one slot, which
                // is what a comparison makes six of at once.
                var p = Easing.OutCubic(Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), _plan.BarMs));

                if (p < 1)
                {
                    break;
                }

                points.Add((
                    mx + (slot * i) + (slot / 2),
                    bottom - ((values[i] / _capScale.Top) * span)));
            }

            if (points.Count > 0)
            {
                lines.Add((points, Palette.Track(index)));
            }

            // What its capsule says: the company, and its value **at the moment being
            // shown** — the same instant the header's date names. Every line shares that
            // instant, since they are one comparison on one axis.
            var reached = values[last];

            ends.Add(new CapEnd(
                track.Name,
                Format(reached, false),
                Palette.Track(index),
                mx + (slot * last) + (slot / 2),
                bottom - ((reached / _capScale.Top) * span)));
        }

        foreach (var (points, colour) in lines)
        {
            // Two points are needed for a line to have a direction; one is a dot, and a
            // dot drawn at the day before yesterday's value names nothing.
            if (points.Count > 1)
            {
                DrawLine(session, context, points, colour);
            }
        }

        DrawPanelTitle(session, context, top, false);
        DrawCapsules(session, context, ends, top, bottom, introA);

        return moving;
    }

    /// <summary>One capsule: what it says, and the point on the curve it rides.</summary>
    private sealed record CapEnd(string Name, string Figure, Color Colour, double X, double Y);

    /// <summary>
    /// How much room the capsules need, so the plot can stop short of it — short enough that
    /// they come to rest clear of the band the host's own interface covers, not merely clear
    /// of the frame's edge. The arithmetic is <see cref="FrameContext.RightLabelColumn"/>'s,
    /// shared with the two other pages that ride a label at a line's leading end.
    ///
    /// Measured from the **last** figures rather than from this frame's, so the column is
    /// the same width on every frame. A column that grew with the figures would narrow
    /// the plot while the capsules were still moving along it, and the curves would slide
    /// sideways as they were being read. Measured from every instrument on the board
    /// rather than from the ones this frame has drawn, for the same reason — the column
    /// has to be the same width before a line arrives as after it.
    ///
    /// The single page measures **both** panels' capsules and gives up the larger: they
    /// share one plot width, and a value of 15,724 beside a price of 1,258.62 is not
    /// answered by letting the second one's capsule hang off the frame.
    /// </summary>
    private double LabelColumn(CanvasDrawingSession session, FrameContext context)
    {
        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var widest = 0d;

        for (var index = 0; index < _board.Tracks.Count; index++)
        {
            var track = _board.Tracks[index];

            // Each instrument's own figures, not the last instrument's for all of them:
            // what has to be measured is each capsule's own text.
            widest = Math.Max(widest, LabelWidth(
                session, context, nameFormat, valueFormat,
                track.Name, Format(_caps[index][track.Last], false)));

            if (!_comparing)
            {
                widest = Math.Max(widest, LabelWidth(
                    session, context, nameFormat, valueFormat,
                    track.Name, Format(_prices[index][track.Last], true)));
            }
        }

        var need = context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad));

        return Math.Clamp(need, 0, context.ChartWidth * MostLabelShare);
    }

    /// <summary>
    /// How wide one capsule is — its name and its figure, measured in the two faces they
    /// are drawn in rather than guessed from a character count, because the figure
    /// changes width as it grows and the name can be anything the directory returns.
    ///
    /// Shared by the column that makes room for the widest one and by the drawing of each
    /// one, so the two cannot disagree about how much room that is.
    /// </summary>
    private static double LabelWidth(
        CanvasDrawingSession session, FrameContext context,
        CanvasTextFormat nameFormat, CanvasTextFormat valueFormat,
        string name, string figure)
    {
        return Ink.Advance(session, name + " ", nameFormat)
               + Ink.Advance(session, figure, valueFormat)
               + context.Px(LabelPadX * 2);
    }

    /// <summary>
    /// Each instrument's name and figure, riding its line's leading end.
    ///
    /// Placed in one pass and drawn in another, because keeping the capsules off each
    /// other cannot be decided one at a time: two companies that ended within a hair of
    /// one another ask for the same spot, and whichever is drawn second covers the first —
    /// a frame carrying the right number of capsules with one of them missing. Pushed
    /// apart top to bottom in the order they came out, which is stable between frames and
    /// between runs.
    ///
    /// The same drawing serves the comparison and the single instrument's two panels,
    /// which is why it takes a list: one capsule is the case where the list holds one.
    /// </summary>
    private void DrawCapsules(
        CanvasDrawingSession session, FrameContext context,
        List<CapEnd> ends, double top, double bottom, double opacity)
    {
        if (ends.Count == 0)
        {
            return;
        }

        using var nameFormat = Ink.Format(context.Px(LabelSize));
        using var valueFormat = Ink.Format(context.Px(LabelSize), bold: true);

        var size = context.Px(LabelSize);

        // Measured from the ink rather than from the type size: the box is the text's
        // height plus its padding, and a padding added to a guessed height leaves a
        // capsule that clips its own descenders.
        using var probe = new CanvasTextLayout(session, "0", valueFormat, 0, 0);
        var height = probe.LayoutBounds.Height + context.Px(LabelPadY * 2);

        var boxes = new List<(double X, double Width)>(ends.Count);

        foreach (var end in ends)
        {
            var width = LabelWidth(session, context, nameFormat, valueFormat, end.Name, end.Figure);

            // Its right edge is what gives way, and it gives way to the **safe line** rather
            // than to the frame's edge: past that line is the band the platform covers with
            // its avatar and its comment button. A long name alongside a large figure can
            // leave the column narrower than the capsule, and then it slides back over the
            // line rather than into the rail.
            var left = Math.Min(
                end.X + context.Px(LabelGap),
                context.SafeRight - context.Px(LabelEdgePad) - width);

            boxes.Add((Math.Max(context.ChartLeft, left), width));
        }

        // Pushed apart top to bottom, in the order they were already sorted into, so one
        // nudged off its neighbour never overtakes it.
        var order = Enumerable.Range(0, ends.Count).OrderBy(i => ends[i].Y).ToArray();
        var gap = context.Px(LabelBetween);
        var placed = new double[ends.Count];
        var previous = double.NegativeInfinity;

        foreach (var i in order)
        {
            placed[i] = Math.Max(ends[i].Y, previous + height + gap);
            previous = placed[i];
        }

        // The stack slides back up as one when it ran past the panel's floor. One shift
        // shared by every capsule keeps the distances between them; clamping each on its
        // own would pile however many are left onto the bottom edge in a heap.
        var overshoot = placed[order[^1]] - (bottom - (height / 2));

        if (overshoot > 0)
        {
            for (var i = 0; i < placed.Length; i++)
            {
                placed[i] = Math.Max(top + (height / 2), placed[i] - overshoot);
            }
        }

        for (var i = 0; i < ends.Count; i++)
        {
            var (x, width) = boxes[i];
            var end = ends[i];
            var box = new Rect(x, placed[i] - (height / 2), width, height);

            // Half the height, so the ends are caps rather than arcs: a capsule is one
            // shape at any width, where a fixed radius reads as a rounded box on a short
            // label and a pill on a long one.
            var radius = (float)(height / 2);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, 0.92 * opacity));
            session.DrawRoundedRectangle(
                box, radius, radius, Ink.Fade(end.Colour, 0.95 * opacity), (float)context.Px(LabelEdge));

            Ink.Runs(
                session,
                [
                    (end.Name + " ", Palette.StockMuted, nameFormat),
                    (end.Figure, end.Colour, valueFormat),
                ],
                box.X + (box.Width / 2),
                box.Y + (height / 2) + (size * 0.36),
                opacity);
        }
    }

    /// <summary>
    /// One panel: grid, the curve, its name and unit, the running figure, the capsule at
    /// the curve's leading end, the mean and the two extremes.
    /// </summary>
    /// <returns>The index of the point still in motion, or the last one — what the
    /// header's moving date tracks.</returns>
    private int DrawPanel(
        CanvasDrawingSession session, FrameContext context, double t, double column, bool isPrice)
    {
        var values = Values(isPrice);
        var scale = isPrice ? _priceScale : _capScale;
        var (top, bottom) = PanelArea(context, isPrice);
        var span = bottom - top;
        var colour = isPrice ? Palette.Track(1) : Palette.Track(0);

        var introA = Easing.Ramp(t, 500, 1500);

        if (introA <= 0 || values.Length == 0)
        {
            return -1;
        }

        var mx = context.ChartLeft;
        var plotW = Math.Max(1, context.ChartWidth - column);
        var slot = plotW / Math.Max(1, values.Length);

        DrawGrid(session, context, scale, mx, plotW, top, bottom, introA, isPrice);

        var moving = -1;
        var shown = 0.0;
        var points = new List<(double X, double Y)>();

        // A point joins the curve once it has finished rising, and that is the whole of
        // the fix. Points still on their way in are not drawn at a partial height, and
        // on a *line* that is not a cosmetic choice.
        //
        // A bar may grow out of the axis — the column it fills is the mark, so a partial
        // column is still a column. A curve cannot. Multiplied by its own progress, a
        // point that has just been born sits on the baseline while its finished
        // neighbour sits at the day's value, so the line falls from that value to the
        // axis inside one slot: a vertical rule down the panel, and a run of them along
        // the bottom. Over ten years of 五粮液 about eight points are on their way in at
        // any moment at the default ninety seconds — `AnimationPlan.For` puts a point's
        // own rise at 260 ms and a day's spacing at 30 ms, so eight or so overlap, and
        // shortening the video to thirty seconds widens that to twenty-six — and the
        // leading one is the entire right-hand edge of the curve, which is what the frame
        // showed.
        //
        // Ending the curve at the last finished point instead draws a line that is
        // steadily extended rightwards, which is what the running figure above the panel
        // has always reported too: it names the value it has reached, not some fraction
        // of it. The line does not appear until its second point has settled, since one
        // point is not yet a direction, so the panel spends a growth's worth of opening
        // holding its grid and its number with no curve under them — which reads as a
        // curve about to start, rather than as one already broken.
        for (var i = 0; i < values.Length; i++)
        {
            var start = _plan.IntroMs + (i * _plan.StaggerMs);

            if (t <= start)
            {
                break;
            }

            var p = Easing.OutCubic(Easing.Ramp(t, start, _plan.BarMs));

            if (p < 1)
            {
                // Still arriving: it is what the running figure names, and the point the
                // header's date tracks, but it is not yet part of the curve.
                moving = i;
                shown = values[i];

                continue;
            }

            var x = mx + (slot * i) + (slot / 2);
            var y = bottom - ((values[i] / scale.Top) * span);

            points.Add((x, y));

            moving = i;
            shown = values[i];
        }

        if (points.Count > 1)
        {
            if (!isPrice)
            {
                DrawArea(session, context, top, bottom, points, colour);
            }

            DrawLine(session, context, points, colour);
        }

        DrawPanelTitle(session, context, top, isPrice);

        if (moving >= 0)
        {
            using var format = Ink.Format(context.Px(52), bold: true);

            Ink.Centred(session, Format(shown, isPrice), mx + (plotW / 2), top - context.Px(22),
                format, colour, introA);

            // The same figure again, riding the point the curve has reached, in the same
            // colour. One instrument is where it earns its place: the number over the
            // panel says what the figure is, and the capsule says it again where the eye
            // already is — at the end of the line, which is the thing growing. It is the
            // same number, read off the same moment, so the two cannot disagree.
            DrawCapsules(
                session, context,
                [
                    new CapEnd(
                        _board.Tracks[0].Name,
                        Format(shown, isPrice),
                        colour,
                        mx + (slot * moving) + (slot / 2),
                        bottom - ((shown / scale.Top) * span)),
                ],
                top, bottom, introA);
        }

        DrawAverage(session, context, t, isPrice, scale, top, bottom, plotW);
        DrawMark(session, context, t, isPrice, scale, top, bottom, plotW, high: true);
        DrawMark(session, context, t, isPrice, scale, top, bottom, plotW, high: false);

        return moving;
    }

    /// <summary>Gridlines and their labels, growing in with the same fade the curve arrives under.</summary>
    private void DrawGrid(
        CanvasDrawingSession session, FrameContext context,
        (double Step, double Top) scale,
        double mx, double plotW, double top, double bottom, double introA, bool isPrice)
    {
        using var format = Ink.Format(context.Px(20));
        var line = (float)Math.Max(1, context.Px(1));

        for (var v = 0.0; v <= scale.Top + 1e-9; v += scale.Step)
        {
            var y = bottom - ((v / scale.Top) * (bottom - top));

            session.DrawLine(
                new Vector2((float)mx, (float)y),
                new Vector2((float)(mx + (plotW * introA)), (float)y),
                Palette.Grid,
                line);

            Ink.RightMiddle(session, Format(v, isPrice), mx - context.Px(12), y,
                format, Palette.StockAxisLabel, introA);
        }
    }

    /// <summary>The value panel's fill: a gradient under the curve, so the area the
    /// company's size covered reads as an area.</summary>
    private void DrawArea(
        CanvasDrawingSession session, FrameContext context,
        double top, double bottom, List<(double X, double Y)> points, Color colour)
    {
        var fade = Ink.Fade(colour, 0.06);

        using var fill = new CanvasLinearGradientBrush(
            session,
            [
                new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.45) },
                new CanvasGradientStop { Position = 1f, Color = fade },
            ])
        {
            StartPoint = new Vector2(0, (float)top),
            EndPoint = new Vector2(0, (float)bottom),
        };

        var polygon = new Vector2[points.Count + 2];

        polygon[0] = new((float)points[0].X, (float)bottom);

        for (var i = 0; i < points.Count; i++)
        {
            polygon[i + 1] = new((float)points[i].X, (float)points[i].Y);
        }

        polygon[^1] = new((float)points[^1].X, (float)bottom);

        using (var geometry = CanvasGeometry.CreatePolygon(session, polygon))
        {
            session.FillGeometry(geometry, fill);
        }
    }

    private void DrawLine(
        CanvasDrawingSession session, FrameContext context,
        List<(double X, double Y)> points, Color colour)
    {
        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };
        using var line = Polyline(session, points);

        session.DrawGeometry(line, Ink.Fade(colour, 0.95), (float)context.Px(3.2), style);
        Ink.Glow(session, context.Px(9), 0.85,
            ds => ds.DrawGeometry(line, Ink.Fade(colour, 0.95), (float)context.Px(3.2), style));
    }

    /// <summary>The panel's name and unit, over its top-left corner.</summary>
    private void DrawPanelTitle(CanvasDrawingSession session, FrameContext context, double top, bool isPrice)
    {
        var mx = context.ChartLeft;
        var title = isPrice ? PriceWord : CapWord;
        var unit = isPrice ? PriceUnitWord : CapUnitWord;

        using (var format = Ink.Format(context.Px(30), bold: true))
        {
            Ink.Left(session, title, mx, top - context.Px(26), format, Palette.StockPanelTitle, 1);

            var width = Ink.Measure(session, title, format);

            using var unitFormat = Ink.Format(context.Px(21));

            Ink.Left(session, $"（{unit}）", mx + width + context.Px(58), top - context.Px(26),
                unitFormat, Palette.StockUnit, 1);
        }
    }

    /// <summary>
    /// The mean over the whole stretch — the level the figure spent its time around,
    /// which a peak and a trough alone do not say.
    /// </summary>
    private void DrawAverage(
        CanvasDrawingSession session, FrameContext context, double t, bool isPrice,
        (double Step, double Top) scale, double top, double bottom, double plotW)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs, 1100);
        if (a <= 0)
        {
            return;
        }

        var values = Values(isPrice);
        var mean = values.Average();
        var y = bottom - ((mean / scale.Top) * (bottom - top));
        var mx = context.ChartLeft;

        using (var dashed = new CanvasStrokeStyle { DashStyle = CanvasDashStyle.Dash })
        {
            session.DrawLine(
                new Vector2((float)mx, (float)y),
                new Vector2((float)(mx + (plotW * Easing.OutCubic(a))), (float)y),
                Palette.AverageLine,
                (float)context.Px(1.8),
                dashed);
        }

        if (a > 0.5)
        {
            using var format = Ink.Format(context.Px(21));
            var label = Strings.Format("StockMeanLabel", Format(mean, isPrice));

            Ink.Left(session, label, mx + context.Px(12), y - context.Px(10),
                format, Palette.AverageLabel, (a - 0.5) / 0.5);
        }
    }

    /// <summary>Marks the peak or the trough, in the closing stretch.</summary>
    private void DrawMark(
        CanvasDrawingSession session, FrameContext context, double t, bool isPrice,
        (double Step, double Top) scale, double top, double bottom, double plotW, bool high)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + (high ? 300 : 800), 650);
        if (a <= 0)
        {
            return;
        }

        var values = Values(isPrice);
        var track = _board.Tracks[0];

        var index = isPrice
            ? (high ? track.PricePeakAt : track.PriceTroughAt)
            : (high ? track.CapPeakAt : track.CapTroughAt);

        if (index < 0 || index >= values.Length)
        {
            return;
        }

        var mx = context.ChartLeft;
        var slot = plotW / Math.Max(1, values.Length);
        var x = mx + (slot * index) + (slot / 2);
        var y = bottom - ((values[index] / scale.Top) * (bottom - top));
        var colour = high ? Palette.Moving : Palette.MarkLow;

        session.FillCircle((float)x, (float)y, (float)context.Px(7), colour);

        using var format = Ink.Format(context.Px(21), bold: true);

        // The figure goes in, because on this page the mark alone is not enough to read
        // it: the trough of a ten-year value curve sits within a few pixels of the
        // baseline — 五粮液 bottomed at 853 亿 on 2016-02-29 against 13,097 亿 at its
        // February 2021 peak, 6.5 per cent of the panel's height (measured by
        // tools/probe-caphistory-extremes.py, which replays this page's own cleaning
        // rules) — and a bare dot down there is read as zero rather than as the low
        // point of a series that never came close to it.
        // The mean above it has always printed its number; these now match it. The
        // shared StockHigh/LowLabel keys stay numberless, since CandleRenderer and
        // StockDualRenderer print the figure separately beside them.
        Ink.Centred(
            session,
            Strings.Format(
                high ? "CapHistoryHighMark" : "CapHistoryLowMark", Format(values[index], isPrice)),
            x, y - context.Px(24), format, colour, a);
    }

    /// <summary>X labels under the lower panel, each fading in as its own point arrives.</summary>
    private void DrawXLabels(CanvasDrawingSession session, FrameContext context, double t, double column)
    {
        var (_, bottom) = PanelArea(context, true);
        var mx = context.ChartLeft;
        var slot = Math.Max(1, context.ChartWidth - column) / Math.Max(1, _labels.Length);
        var every = Math.Max(1, (int)Math.Ceiling(_labels.Length / 8.0));

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < _labels.Length; i += every)
        {
            var a = Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), 450);
            if (a <= 0)
            {
                continue;
            }

            Ink.Centred(session, _labels[i], mx + (slot * i) + (slot / 2), bottom + context.Px(28),
                format, Palette.StockDateLabel, a);
        }
    }

    private void DrawFooter(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + 1800, 900);
        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            format, Palette.Credit, a * 0.8);
    }

    /// <summary>
    /// The header block: title, the code-and-range line with the count picked out, and
    /// the date moving through the animation.
    /// </summary>
    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t, int moving)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;
        var iso = CultureInfo.InvariantCulture;
        var title = ResolvedTitle();

        _title.Draw(session, context, title, _title.For(session, title, context, ShowTitle), Palette.Title, a);

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            // The code is named only when there is one company to name. Six codes and
            // six names in this line would push the dates and the count off the frame,
            // and every one of them is already written beside its own line's end.
            List<(string, Color, CanvasTextFormat)> runs = [];

            if (Code.Length > 0)
            {
                runs.Add((Code.ToUpperInvariant() + " · ", Palette.StockMuted, plain));
            }

            runs.Add((
                $"{_board.Start.ToString("yyyy-MM-dd", iso)} {Strings.Get("StockRangeJoiner")} {_board.End.ToString("yyyy-MM-dd", iso)} · ",
                Palette.StockMuted, plain));
            runs.Add((_board.Count.ToString(iso), Palette.Emphasis, strong));
            runs.Add((" " + SpanWord, Palette.StockMuted, plain));

            Ink.Runs(session, runs, cx, context.HeaderRow(0.188, _titleLines), a);
        }

        if (moving >= 0 && moving < _labels.Length)
        {
            using var format = Ink.Format(context.Px(40), bold: true);

            Ink.Centred(session, _labels[moving], cx, context.HeaderRow(0.222, _titleLines),
                format, Palette.Moving, a);
        }
    }

    private static void DrawProgress(CanvasDrawingSession session, FrameContext context)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session,
            new Rect(0, y, context.Width * Math.Clamp(context.Progress, 0, 1), height),
            Palette.StockProgressFill,
            context.Width);
    }

    /// <summary>
    /// The axis labels: months where the stretch is years long, days where it is not.
    ///
    /// A format, not a phrase — nothing here is translated, and both forms are read in
    /// every locale the app ships in.
    /// </summary>
    private static string[] Labels(CapBoard board)
    {
        var byMonth = (board.End.DayNumber - board.Start.DayNumber) > 400;
        var iso = CultureInfo.InvariantCulture;

        return [.. board.Dates.Select(d =>
            byMonth ? d.ToString("yyyy-MM", iso) : d.ToString("MM-dd", iso))];
    }

    /// <summary>
    /// Thousands grouped. The value panel is read in whole 亿 and the price to two —
    /// except on a rebased axis, where the figures cluster around 100 and a whole
    /// number would round two instruments that finished 137.4 and 137.1 to the same
    /// label, which is exactly the comparison the panel exists to draw.
    /// </summary>
    private string Format(double value, bool isPrice) =>
        value.ToString(isPrice ? "N2" : _normalized ? "N1" : "N0", CultureInfo.InvariantCulture);

    private static CanvasGeometry Polyline(
        CanvasDrawingSession session, IReadOnlyList<(double X, double Y)> points)
    {
        using var builder = new CanvasPathBuilder(session);

        builder.BeginFigure((float)points[0].X, (float)points[0].Y);

        for (var i = 1; i < points.Count; i++)
        {
            builder.AddLine((float)points[i].X, (float)points[i].Y);
        }

        builder.EndFigure(CanvasFigureLoop.Open);

        return CanvasGeometry.CreatePath(builder);
    }
}
