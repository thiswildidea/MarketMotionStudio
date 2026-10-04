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
/// One instrument's candles, drawn as a vertical chart: the price panel with its
/// moving averages, a volume panel under it, and the range's figures arriving at
/// the end.
///
/// The same bars are drawn four ways. They are one choice about the picture rather
/// than four series, which is why switching between them re-fetches nothing: the
/// candle body, the open-high-low-close bar, the closing line and the filled area
/// all read the same closes and differ only in what they make of them.
///
/// Two motions, and they answer different questions. Growing lays the whole range
/// out and ends on the finished chart — "what did these three years look like".
/// Scrolling holds a window and walks it forward — "what did it look like at the
/// time" — which is the only way a long range keeps a candle wide enough to read,
/// and the reason the window is a control rather than a constant.
///
/// Stateless with respect to time per <c>one-render-path.mdc</c>: every frame comes
/// from <see cref="FrameContext.Progress"/> alone.
/// </summary>
public sealed class CandleRenderer : IFrameRenderer
{
    /// <summary>
    /// Distance from the chart's lower edge down to the credit, in baseline pixels.
    /// Deeper than the other pages' because this one reserves two bands in it: the
    /// volume panel and, below that, the four statistic cards.
    /// </summary>
    public const double CreditGap = 430;

    /// <summary>Where the price panel starts, as a fraction of frame height.</summary>
    private const double PlotTopFraction = 0.385;

    // The header's rows, as fractions of frame height, named so the gaps between
    // them can be read as the numbers they are.
    //
    // They are not evenly spaced, because what stands in each one is not the same
    // height. Everything here is positioned by its baseline, and the headline is a
    // 112-pixel line sitting on its own: the row above it has to clear the top of
    // those digits, which is about eighty pixels above the baseline, not the
    // baseline itself. Spaced as a run of equal steps the price row came out four
    // pixels above the top of the digits, and the two read as one line printed over
    // another.
    //
    // And clearing the digits is not enough on its own, because the headline is drawn
    // under a 13-pixel glow that reaches about another twenty-five pixels past them in
    // every direction. A row that merely misses the digits by a few pixels still has
    // the halo sitting in it, which reads the same way: two lines printed over each
    // other. So each gap here is the glow's reach plus a margin — 0.258 and 0.330 are
    // where the price row and the headline clear the halo, and not where they clear
    // the ink.

    /// <summary>Instrument and period, the largest line in the block.</summary>
    private const double TitleRow = 0.155;

    /// <summary>The code and the period again, in the source's own spelling.</summary>
    private const double SubtitleRow = 0.19;

    /// <summary>Open, high, low and close of that candle, on one line.</summary>
    private const double QuotesRow = 0.258;

    // How far the ink of a line reaches past its own baseline, in baseline pixels. The
    // three lines of this header are not the same kind of text, so their ink is not the
    // same shape, and the row placed between them has to be placed against the ink.
    //
    // Both of the extremes belong to CJK and to neither of the baselines: the subtitle
    // ends in "日K", whose glyphs hang about four pixels under the baseline they sit on;
    // the price row opens with "开", whose glyphs stand about twenty-two pixels up, some
    // three above where the figures beside it reach. Neither the hang nor the extra
    // height is anywhere in the baselines, and both of them are in the gap.

    /// <summary>Under the subtitle's baseline, where its CJK hangs.</summary>
    private const double SubtitleInkBelow = 4;

    /// <summary>Above the price row's baseline, where its CJK labels stand.</summary>
    private const double QuoteInkAbove = 22;

    /// <summary>Above the date's baseline, where figures of that size reach.</summary>
    private const double DateInkAbove = 25;

    /// <summary>Below it — the date is a run of figures and has nothing that hangs.</summary>
    private const double DateInkBelow = 0;

    /// <summary>
    /// The date of the candle being shown: its ink centred in the air between the
    /// subtitle above it and the four prices below.
    ///
    /// The only row here placed by its neighbours rather than by ink it has to clear,
    /// because it belongs to neither of them — it labels nothing and is labelled by
    /// nothing. Given a number of its own it came out 92 pixels under the subtitle and
    /// 38 above the prices: far enough from the first to look adrift, close enough to
    /// the second to read as a line of them. Derived rather than written down, so that
    /// moving either neighbour carries it along.
    ///
    /// Note that this is *not* the midpoint of the two baselines, which is 0.224 and
    /// three pixels higher: the ink either side of the date is not symmetrical about
    /// those baselines, for the reason above. Centring the baselines leaves 37 pixels of
    /// air above the date and 45 below, which is what was noticed; air is what the eye
    /// reads, so air is what gets matched.
    ///
    /// Written out as arithmetic on its neighbours rather than solved at run time, so it
    /// stays a constant like the rest of the block: equal air comes to the two baselines
    /// plus a correction for the ink that hangs off them, over twice the frame height.
    /// </summary>
    private const double DateRow =
        (((SubtitleRow + QuotesRow) * VideoFormat.BaselineHeight)
            + SubtitleInkBelow - QuoteInkAbove + DateInkAbove + DateInkBelow)
        / (2 * VideoFormat.BaselineHeight);

    /// <summary>The headline: how far that candle moved.</summary>
    private const double MoveRow = 0.330;

    /// <summary>What the headline is, under it — "change", "return".</summary>
    private const double MoveLabelRow = 0.360;

    /// <summary>Gap between the price panel's foot and the top of the volume panel.</summary>
    private const double VolumeGap = 66;

    /// <summary>How tall the volume panel is. Given back to the price panel when it is off.</summary>
    private const double VolumeHeight = 110;

    /// <summary>How far the price panel grows when there is no volume panel under it.</summary>
    private const double VolumeReclaimed = VolumeGap + VolumeHeight;

    /// <summary>Distance from the credit up to the top of the statistic cards.</summary>
    private const double CardsAboveCredit = 192;

    /// <summary>A close at or above its open. The market's own convention: gains in red.</summary>
    private static readonly Color Up = Rgb(0xEF, 0x44, 0x44);

    /// <summary>A close below its open. Cool, and not the averages' blue — a fall should
    /// read as absence of a rise, not as a different measurement.</summary>
    private static readonly Color Down = Rgb(0x22, 0xC5, 0x5E);

    /// <summary>The three averages, warm to cool in the order they are read: five first.</summary>
    private static readonly Color Ma5 = Rgb(0xFB, 0xBF, 0x24);

    private static readonly Color Ma10 = Rgb(0x60, 0xA5, 0xFA);

    private static readonly Color Ma20 = Rgb(0xA8, 0x55, 0xF7);

    private readonly CandleSeries _series;

    private readonly AnimationPlan _plan;

    private readonly CandleStyle _style;

    private readonly CandleMotion _motion;

    /// <summary>How many candles a scrolling window holds.</summary>
    private readonly int _window;

    private readonly bool _showAverages;

    private readonly bool _showVolume;

    /// <summary>The three averages, aligned with the bars and computed once.</summary>
    private readonly double?[][] _averages;

    /// <summary>
    /// Where each bar sits along the axis, as a fraction of the session's own clock — or
    /// null when the bars carry no clock at all.
    ///
    /// 09:30 is nought and 15:00 is one, so the morning session fills the first third of
    /// the frame, the afternoon the last third, and the ninety minutes between them stand
    /// empty. That gap is the point: an intraday chart whose bars were spaced evenly
    /// would put the 11:30 close next to the 13:00 open and read as one continuous
    /// three-hour move, when two hours of trading and an hour and a half of nothing
    /// happened. Nothing on a daily, weekly or monthly chart changes — those bars are
    /// evenly spaced, as they always were.
    /// </summary>
    private readonly double[]? _stamps;

    /// <summary>The lengths the averages are taken over, in the order they are drawn.</summary>
    private static readonly int[] AverageLengths = [5, 10, 20];

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all; hiding it hands its row back.</summary>
    public bool ShowTitle { get; set; } = true;

    public CandleRenderer(
        CandleSeries series, AnimationPlan plan, CandleStyle style, CandleMotion motion,
        int window, bool showAverages, bool showVolume)
    {
        _series = series;
        _plan = plan;
        _style = style;
        _motion = motion;
        _window = Math.Max(5, window);
        _showAverages = showAverages;
        _showVolume = showVolume;

        _averages = [.. AverageLengths.Select(series.Average)];
        _stamps = Stamps(series.Bars);
    }

    /// <summary>
    /// The session's first and last minute, as minutes past midnight: 09:30 and 15:00 on
    /// the mainland venues, which are the only ones with minute bars at all.
    /// </summary>
    private const int OpeningMinute = (9 * 60) + 30;

    private const int ClosingMinute = 15 * 60;

    /// <summary>
    /// Each bar's place on the clock axis, or null for a series with no clocks.
    ///
    /// Null rather than a spread of evenly spaced fractions, so that the callers read
    /// "these bars are laid out by their order" from the same thing they read the
    /// fractions from. A series with the clock on some bars and not on others is a series
    /// this chart cannot place, and answering null for it keeps every bar in the order
    /// they came rather than dropping the unplaced ones into the gap.
    /// </summary>
    private static double[]? Stamps(IReadOnlyList<TencentKline.CandleBar> bars)
    {
        var span = ClosingMinute - OpeningMinute;
        var stamps = new double[bars.Count];

        for (var i = 0; i < bars.Count; i++)
        {
            var clock = bars[i].Clock;

            if (clock.Length != 4 ||
                !int.TryParse(clock[..2], NumberStyles.Integer, CultureInfo.InvariantCulture, out var hour) ||
                !int.TryParse(clock[2..], NumberStyles.Integer, CultureInfo.InvariantCulture, out var minute))
            {
                return null;
            }

            stamps[i] = Math.Clamp((((hour * 60) + minute) - OpeningMinute) / (double)span, 0, 1);
        }

        return stamps;
    }

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        context.Backdrop.Fill(session, context, Palette.Background);

        var view = View(context, t);

        DrawPriceGrid(session, context, view);

        if (_showVolume)
        {
            DrawVolume(session, context, view);
        }

        DrawPrice(session, context, view);

        if (_showAverages)
        {
            DrawAverages(session, context, view);
        }

        DrawLunch(session, context, view);
        DrawXLabels(session, context, view);
        DrawLegend(session, context, view);
        DrawHeader(session, context, view);
        DrawStats(session, context, t);
        DrawProgress(session, context, t);
    }

    // ---- the frame's own arithmetic ---------------------------------------------

    /// <summary>
    /// What this frame is showing: which candles, where they sit, and over what
    /// range of prices.
    ///
    /// Worked out once and handed to every part of the drawing, because the scale
    /// is the one thing they all have to agree on — an axis computed twice is two
    /// axes, and candles drawn against a second one sit somewhere the labels do not
    /// describe.
    /// </summary>
    private sealed record Frame(
        double First, double Head, double Count,
        double Low, double High, double VolumePeak,
        int Arrived, double Growth, int From, int To,
        double Top, double Bottom, double Left, double Width);

    private Frame View(FrameContext context, double t)
    {
        var n = _series.Count;
        var bars = _series.Bars;

        // Which candle has arrived, and how far the arriving one has come. The
        // arrival is eased without overshoot: a body that exceeds its own close and
        // settles back reads as the price being corrected.
        var arrived = -1;
        var growth = 0.0;

        for (var i = 0; i < n; i++)
        {
            var start = _plan.IntroMs + (i * _plan.StaggerMs);

            if (t <= start)
            {
                break;
            }

            arrived = i;
            growth = Easing.OutCubic(Easing.Ramp(t, start, _plan.BarMs));
        }

        var reach = arrived < 0 ? -1 : arrived + growth;

        var count = _motion is CandleMotion.Scroll ? Math.Min(_window, n) : n;
        var head = _motion is CandleMotion.Scroll && reach >= 0 ? Math.Max(reach, count - 1) : reach;
        var first = _motion is CandleMotion.Scroll ? head - (count - 1) : 0;

        var from = Math.Clamp((int)Math.Floor(first), 0, n - 1);
        var to = Math.Clamp((int)Math.Ceiling(head), -1, n - 1);

        var low = double.MaxValue;
        var high = double.MinValue;
        var volume = 0.0;

        // The scale is taken from the candles in view *in full*, including the one
        // still growing. Taking it from the part drawn so far would make the axis
        // climb as the candle does, and the whole chart would rise under it.
        for (var i = from; i <= to && i >= 0; i++)
        {
            low = Math.Min(low, bars[i].Low);
            high = Math.Max(high, bars[i].High);
            volume = Math.Max(volume, bars[i].Volume);
        }

        if (to < from)
        {
            low = high = 0;
        }

        if (high - low < 1e-9)
        {
            var around = Math.Max(high, 1) * 0.01;
            low -= around;
            high += around;
        }

        var pad = (high - low) * 0.08;

        low -= pad;
        high += pad;

        var bottom = context.BaselineAbove(CreditGap) +
            (_showVolume ? 0 : context.Px(VolumeReclaimed));

        return new Frame(
            first, head, count,
            low, high, volume,
            arrived, growth, from, to,
            context.HeaderRow(PlotTopFraction, ShowTitle), bottom,
            context.ChartLeft, context.ChartWidth);
    }

    /// <summary>
    /// Where candle <paramref name="i"/> sits horizontally.
    ///
    /// By its place in the session when the bars carry a clock, by its place in the
    /// series otherwise; see <see cref="_stamps"/>. Either way the window in view is
    /// stretched across the whole width, so a scrolling chart of the last hour fills
    /// the frame the way a scrolling chart of the last sixty days does.
    /// </summary>
    private double X(Frame view, int i) => _stamps is null
        ? view.Left + (view.Width * (i - view.First) / Math.Max(1, view.Count - 1))
        : Where(view, _stamps[i]);

    /// <summary>Where a place on the clock axis falls, over the stretch of it in view.</summary>
    private double Where(Frame view, double stamp)
    {
        var from = At(view, view.First);
        var span = Math.Max(1e-6, At(view, view.First + view.Count - 1) - from);

        return view.Left + (view.Width * ((stamp - from) / span));
    }

    /// <summary>
    /// The clock axis at a possibly fractional bar index.
    ///
    /// Interpolated, because the head of a growing or scrolling chart sits partway
    /// between two bars and the window's edges are measured against it.
    /// </summary>
    private double At(Frame view, double index)
    {
        var last = _stamps!.Length - 1;
        var low = (int)Math.Clamp(Math.Floor(index), 0, last);
        var high = (int)Math.Clamp(Math.Ceiling(index), 0, last);

        return _stamps[low] + ((_stamps[high] - _stamps[low]) * (index - low));
    }

    /// <summary>Where price <paramref name="value"/> sits vertically in the price panel.</summary>
    private double Y(Frame view, double value) =>
        view.Bottom - (((value - view.Low) / (view.High - view.Low)) * PriceHeight(view));

    private double PriceHeight(Frame view) => Math.Max(1, view.Bottom - view.Top);

    /// <summary>How far through its own arrival candle <paramref name="i"/> is.</summary>
    private double Growth(Frame view, int i) =>
        i < view.Arrived ? 1 : i == view.Arrived ? view.Growth : 0;

    // ---- the price panel ---------------------------------------------------------

    private void DrawPriceGrid(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var introduction = Easing.Ramp(context.Progress * _plan.TotalMs, 0, 1000);
        var line = (float)Math.Max(1, context.Px(1));

        using var format = Ink.Format(context.Px(20));

        // Five lines, the top and bottom of the panel among them. Evenly spaced
        // between the panel's own extremes rather than on a round step: a price
        // range like 86.4–104.2 has no round step worth labelling, and forcing one
        // leaves the top of the chart empty.
        for (var step = 0; step <= 4; step++)
        {
            var value = view.Low + (((view.High - view.Low) * step) / 4);
            var y = Y(view, value);

            session.DrawLine(
                new Vector2((float)view.Left, (float)y),
                new Vector2((float)(view.Left + (view.Width * introduction)), (float)y),
                Palette.Grid, line);

            Ink.RightMiddle(session, CandleLoader.Axis(value), view.Left - context.Px(12), y,
                format, Palette.AxisLabel, introduction);
        }
    }

    private void DrawPrice(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        if (view.To < view.From)
        {
            return;
        }

        var slot = view.Width / Math.Max(1, view.Count - 1);
        var body = Math.Max(context.Px(1.4), slot * 0.62);
        var wick = Math.Max(context.Px(1), body * 0.16);

        switch (_style)
        {
            case CandleStyle.Line:
            case CandleStyle.Area:
                DrawClosingCurve(session, context, view);
                break;

            default:
                for (var i = view.From; i <= view.To; i++)
                {
                    var p = Growth(view, i);

                    if (p <= 0)
                    {
                        continue;
                    }

                    if (_style is CandleStyle.Candles)
                    {
                        DrawCandle(session, context, view, i, p, body, wick);
                    }
                    else
                    {
                        DrawBar(session, context, view, i, p, body);
                    }
                }

                break;
        }
    }

    /// <summary>
    /// One candle, growing out of its own open.
    ///
    /// The body opens at the open and closes at the close; the wick reaches out from
    /// the open towards the high and the low. Growing from the open rather than from
    /// the axis is what makes the four prices one thing: a body that rose from the
    /// floor would spend its first frames describing a price the instrument was
    /// never at.
    /// </summary>
    private void DrawCandle(
        CanvasDrawingSession session, FrameContext context, Frame view,
        int i, double p, double body, double wick)
    {
        var bar = _series.Bars[i];
        var x = (float)X(view, i);
        var rising = bar.Close >= bar.Open;
        var colour = rising ? Up : Down;

        var open = bar.Open;
        var close = open + ((bar.Close - open) * p);
        var high = open + ((bar.High - open) * p);
        var low = open - ((open - bar.Low) * p);

        var top = (float)Math.Min(Y(view, high), Y(view, low));
        var foot = (float)Math.Max(Y(view, high), Y(view, low));

        session.DrawLine(
            new Vector2(x, top), new Vector2(x, foot),
            Ink.Fade(colour, 0.9), (float)wick);

        var yOpen = (float)Y(view, open);
        var yClose = (float)Y(view, close);
        var box = new Rect(
            x - (body / 2),
            Math.Min(yOpen, yClose),
            body,
            Math.Max(context.Px(1), Math.Abs(yClose - yOpen)));

        session.FillRectangle(box, Ink.Fade(colour, 0.95));
        session.DrawRectangle(box, Ink.Fade(colour, 0.55), (float)Math.Max(1, context.Px(0.8)));
    }

    /// <summary>
    /// The same four prices as a bar: the high-low line with the open ticking left
    /// and the close ticking right.
    /// </summary>
    private void DrawBar(
        CanvasDrawingSession session, FrameContext context, Frame view, int i, double p, double body)
    {
        var bar = _series.Bars[i];
        var x = (float)X(view, i);
        var rising = bar.Close >= bar.Open;
        var colour = rising ? Up : Down;
        var stroke = (float)Math.Max(context.Px(1), body * 0.16);
        var tick = (float)(body * 0.42);

        var open = bar.Open;
        var close = open + ((bar.Close - open) * p);
        var high = open + ((bar.High - open) * p);
        var low = open - ((open - bar.Low) * p);

        var top = (float)Math.Min(Y(view, high), Y(view, low));
        var foot = (float)Math.Max(Y(view, high), Y(view, low));

        session.DrawLine(new Vector2(x, top), new Vector2(x, foot), Ink.Fade(colour, 0.92), stroke);

        session.DrawLine(
            new Vector2(x - tick, (float)Y(view, open)), new Vector2(x, (float)Y(view, open)),
            Ink.Fade(colour, 0.92), stroke);

        session.DrawLine(
            new Vector2(x, (float)Y(view, close)), new Vector2(x + tick, (float)Y(view, close)),
            Ink.Fade(colour, 0.92), stroke);
    }

    /// <summary>
    /// The closes, joined — and filled down to the panel's foot in the area style.
    ///
    /// The arriving point comes *from the previous close*, not from the axis. A line
    /// whose newest segment plunged to the floor and climbed back is a crack in the
    /// leading edge: glaring in a paused frame, a permanent dent in playback.
    /// </summary>
    private void DrawClosingCurve(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var bars = _series.Bars;
        var points = new List<Vector2>();

        for (var i = view.From; i <= view.To; i++)
        {
            var p = Growth(view, i);
            var close = bars[i].Close;

            if (i == view.Arrived && i > 0)
            {
                var previous = bars[i - 1].Close;
                close = previous + ((close - previous) * p);
            }
            else if (i > view.Arrived)
            {
                break;
            }

            points.Add(new Vector2((float)X(view, i), (float)Y(view, close)));
        }

        if (points.Count < 2)
        {
            return;
        }

        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };
        using var geometry = Polyline(session, [.. points]);

        if (_style is CandleStyle.Area)
        {
            var ring = new Vector2[points.Count + 2];

            for (var i = 0; i < points.Count; i++)
            {
                ring[i] = points[i];
            }

            ring[points.Count] = new Vector2(points[^1].X, (float)view.Bottom);
            ring[points.Count + 1] = new Vector2(points[0].X, (float)view.Bottom);

            using var filled = CanvasGeometry.CreatePolygon(session, ring);

            session.FillGeometry(filled, Ink.Fade(Palette.Moving, 0.16));
        }

        session.DrawGeometry(geometry, Ink.Fade(Palette.Moving, 0.95), (float)context.Px(3), style);
    }

    /// <summary>
    /// The moving averages, over the candles in view.
    ///
    /// Each follows the same rule as the closing line: an arriving point grows out
    /// of the average's own previous value, because an average is a line too and a
    /// dent in it is as visible as one in the price.
    /// </summary>
    private void DrawAverages(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var colours = new[] { Ma5, Ma10, Ma20 };

        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

        for (var a = 0; a < _averages.Length; a++)
        {
            var average = _averages[a];
            var points = new List<Vector2>();

            for (var i = view.From; i <= view.To; i++)
            {
                if (average[i] is not { } value)
                {
                    continue;
                }

                if (i == view.Arrived && i > 0 && average[i - 1] is { } previous)
                {
                    value = previous + ((value - previous) * view.Growth);
                }
                else if (i > view.Arrived)
                {
                    break;
                }

                points.Add(new Vector2((float)X(view, i), (float)Y(view, value)));
            }

            if (points.Count < 2)
            {
                continue;
            }

            using var geometry = Polyline(session, [.. points]);

            session.DrawGeometry(geometry, Ink.Fade(colours[a], 0.9), (float)context.Px(2), style);
        }
    }

    // ---- the volume panel --------------------------------------------------------

    private void DrawVolume(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var introduction = Easing.Ramp(context.Progress * _plan.TotalMs, 0, 1000);

        var top = view.Bottom + context.Px(VolumeGap);
        var height = context.Px(VolumeHeight);
        var foot = top + height;
        var peak = Math.Max(1, view.VolumePeak * 1.08);

        session.DrawLine(
            new Vector2((float)view.Left, (float)foot),
            new Vector2((float)(view.Left + (view.Width * introduction)), (float)foot),
            Palette.Grid, (float)Math.Max(1, context.Px(1)));

        using var format = Ink.Format(context.Px(19));

        Ink.RightMiddle(session, Strings.Get("StockPanelVolume"), view.Left - context.Px(12),
            top + (height / 2), format, Palette.AxisLabel, introduction);

        if (view.To < view.From)
        {
            return;
        }

        var slot = view.Width / Math.Max(1, view.Count - 1);
        var body = Math.Max(context.Px(1.4), slot * 0.62);

        for (var i = view.From; i <= view.To; i++)
        {
            var p = Growth(view, i);

            if (p <= 0)
            {
                continue;
            }

            var bar = _series.Bars[i];
            var x = X(view, i);
            var risen = (bar.Volume / peak) * height * p;
            var colour = bar.Close >= bar.Open ? Up : Down;

            session.FillRectangle(
                new Rect(x - (body / 2), foot - risen, body, Math.Max(context.Px(1), risen)),
                Ink.Fade(colour, 0.55));
        }
    }

    // ---- labels ------------------------------------------------------------------

    private void DrawXLabels(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        if (view.To < view.From)
        {
            return;
        }

        var shown = view.To - view.From + 1;
        var every = Math.Max(1, (int)Math.Ceiling(shown / 5.0));

        using var format = Ink.Format(context.Px(19));

        var y = view.Bottom + context.Px(28);

        for (var i = view.From; i <= view.To; i++)
        {
            if ((i - view.From) % every != 0)
            {
                continue;
            }

            Ink.Centred(session, CandleLoader.Label(_series.Bars[i], _series.Period),
                X(view, i), y, format, Palette.DateLabel, 1);
        }
    }

    /// <summary>
    /// The lunch break, drawn as the gap it is.
    ///
    /// A line rather than a filled band, and only on a series whose bars carry a clock:
    /// on every other period the axis is a line of dates and there is nothing between
    /// them to mark. The label is the same word the turnover page's intraday curve puts
    /// on its noon line, because it is the same fact.
    /// </summary>
    private void DrawLunch(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        if (_stamps is null)
        {
            return;
        }

        var resumed = -1;

        for (var i = 1; i < _series.Bars.Count; i++)
        {
            if (string.CompareOrdinal(_series.Bars[i].Clock, "1300") >= 0 &&
                string.CompareOrdinal(_series.Bars[i - 1].Clock, "1300") < 0)
            {
                resumed = i;
                break;
            }
        }

        if (resumed < 0)
        {
            return;
        }

        var x = (float)Where(view, (At(view, resumed - 1) + At(view, resumed)) / 2);

        session.DrawLine(
            new Vector2(x, (float)view.Top),
            new Vector2(x, (float)view.Bottom),
            Ink.Fade(Palette.Grid, 0.9), (float)Math.Max(1, context.Px(1.5)));

        using var format = Ink.Format(context.Px(19));

        Ink.Centred(session, Strings.Get("TurnoverIntradayNoon"), x, view.Top + context.Px(26),
            format, Palette.AxisLabel, 1);
    }

    /// <summary>
    /// What the colours are, above the panel: the averages when they are drawn, and
    /// the two directions of a candle when candles are.
    /// </summary>
    private void DrawLegend(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var introduction = Easing.Ramp(context.Progress * _plan.TotalMs, 0, 1000);

        if (introduction <= 0)
        {
            return;
        }

        var entries = new List<(Color Colour, string Text)>();

        if (_showAverages)
        {
            var colours = new[] { Ma5, Ma10, Ma20 };

            for (var a = 0; a < AverageLengths.Length; a++)
            {
                entries.Add((colours[a], "MA" + AverageLengths[a].ToString(CultureInfo.InvariantCulture)));
            }
        }
        else if (_style is CandleStyle.Candles or CandleStyle.Bars)
        {
            // The same two words the matrix page's monthly column uses, because they
            // are the same two facts: a candle whose close is above its open, and one
            // whose close is below it. Its own pair of keys would have to be written
            // fourteen times to say what is already said.
            entries.Add((Up, Strings.Get("ReturnStatUp")));
            entries.Add((Down, Strings.Get("ReturnStatDown")));
        }
        else
        {
            entries.Add((Palette.Moving, Strings.Get("CandleLegendClose")));
        }

        var x = view.Left;
        var y = view.Top - context.Px(24);
        var swatch = context.Px(34);

        using var format = Ink.Format(context.Px(21));

        foreach (var (colour, text) in entries)
        {
            session.DrawLine(
                new Vector2((float)x, (float)y), new Vector2((float)(x + swatch), (float)y),
                Ink.Fade(colour, 0.95 * introduction), (float)context.Px(4));

            var width = Ink.Measure(session, text, format);

            Ink.Left(session, text, x + swatch + context.Px(10), y + context.Px(7),
                format, Palette.Muted, introduction);

            x += swatch + context.Px(10) + width + context.Px(34);
        }
    }

    // ---- the frame's header ------------------------------------------------------

    private void DrawHeader(CanvasDrawingSession session, FrameContext context, Frame view)
    {
        var t = context.Progress * _plan.TotalMs;
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;
        var period = Strings.Get(CandleLoader.NameKey(_series.Period));

        if (ShowTitle)
        {
            var title = Title.Length > 0
                ? Title
                : Strings.Format("CandleDefaultTitle", _series.Name, period);

            var size = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(size, bold: true))
            {
                Ink.Centred(session, title, cx, Row(context, TitleRow), format, Palette.Title, a);
            }
        }

        using var small = Ink.Format(context.Px(25));

        Ink.Centred(session, Strings.Format("CandleSubtitleLine", _series.Code.ToUpperInvariant(), period),
            cx, Row(context, SubtitleRow), small, Palette.Muted, a);

        var index = Math.Clamp(view.Arrived, 0, _series.Count - 1);
        var bar = _series.Bars[index];

        using (var dateFormat = Ink.Format(context.Px(34)))
        {
            Ink.Centred(session, CandleLoader.Iso(bar.Date), cx, Row(context, DateRow),
                dateFormat, Palette.Moving, a);
        }

        DrawQuotes(session, context, bar, cx, a);

        // The move of the candle being shown, over the one before it. The first has
        // nothing before it, so it is measured against its own open — which is the
        // same thing on the only candle that has no yesterday.
        var before = index > 0 ? _series.Bars[index - 1].Close : bar.Open;
        var move = before > 0 ? ((bar.Close / before) - 1) * 100 : 0;
        var text = (move >= 0 ? "+" : string.Empty) + move.ToString("0.00", CultureInfo.InvariantCulture) + "%";
        var colour = move >= 0 ? Up : Down;

        using (var bigFormat = Ink.Format(context.Px(112), bold: true))
        {
            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, MoveRow), bigFormat, colour));

            Ink.Centred(session, text, cx, Row(context, MoveRow), bigFormat, colour, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, Strings.Format("CandleMoveLabel", period), cx, Row(context, MoveLabelRow),
            unitFormat, Palette.Muted, a);
    }

    /// <summary>
    /// The four prices of the candle being shown, in one line: label dim, figure in
    /// the colour of what the candle did.
    /// </summary>
    private void DrawQuotes(
        CanvasDrawingSession session, FrameContext context, TencentKline.CandleBar bar,
        double cx, double opacity)
    {
        var colour = bar.Close >= bar.Open ? Up : Down;

        using var labelFormat = Ink.Format(context.Px(25));
        using var valueFormat = Ink.Format(context.Px(27), bold: true);

        var runs = new List<(string, Color, CanvasTextFormat)>();

        void Pair(string key, double value, Color ink)
        {
            runs.Add((Strings.Get(key) + " ", Palette.Muted, labelFormat));
            runs.Add((CandleLoader.Price(value) + "  ", ink, valueFormat));
        }

        Pair("CandleOpen", bar.Open, colour);
        Pair("StockHighLabel", bar.High, colour);
        Pair("StockLowLabel", bar.Low, colour);
        Pair("CandleClose", bar.Close, colour);

        // The trailing separator inside the last run is measured with it, which
        // would push the line off-centre by its width; trimmed instead.
        var last = runs[^1];
        runs[^1] = (last.Item1.TrimEnd(), last.Item2, last.Item3);

        Ink.Runs(session, runs, cx, Row(context, QuotesRow), opacity);
    }

    // ---- the range's figures -----------------------------------------------------

    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var culture = CultureInfo.InvariantCulture;
        var rising = _series.RangeReturn >= 0;

        var cards = new[]
        {
            (Strings.Get("CandleCardRange"),
                ((_series.RangeReturn >= 0 ? "+" : string.Empty) +
                 _series.RangeReturn.ToString("0.0", culture) + "%"),
                rising ? Up : Down),
            (Strings.Get("StockHighLabel"), CandleLoader.Price(_series.High), Palette.CardValue),
            (Strings.Get("StockLowLabel"), CandleLoader.Price(_series.Low), Palette.CardValue),
            (Strings.Get("CandleCardAmplitude"), _series.Amplitude.ToString("0.0", culture) + "%",
                Palette.CardValue),
        };

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

            Ink.Centred(session, cards[i].Item1, x + (cardWidth / 2), y + context.Px(42),
                labelFormat, Palette.Muted, a);
            Ink.Centred(session, cards[i].Item2, x + (cardWidth / 2), y + context.Px(92),
                valueFormat, cards[i].Item3, a);
        }

        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    private void DrawProgress(CanvasDrawingSession session, FrameContext context, double t)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);
        var p = Math.Clamp(t / _plan.TotalMs, 0, 1);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(session, new Rect(0, y, context.Width * p, height),
            Palette.ProgressFill, context.Width);
    }

    private double Row(FrameContext context, double fraction) => context.HeaderRow(fraction, ShowTitle);

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
