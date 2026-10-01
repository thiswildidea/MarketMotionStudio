using System.Globalization;
using System.Numerics;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// A holding, drawn as two lines on one axis: the flat capital that went in once,
/// and what the shares it bought are worth, which is the whole story — every rise
/// and fall on this chart is the price's doing, nothing was added and nothing
/// removed.
///
/// The space between the lines is filled, warm while the holding is ahead and cool
/// while it is behind, the same convention as the plan page; the headline figure is
/// the ratio between them, and the closing cards add the drawdown, because "it
/// ended up X% ahead" and "it was once Y% down" are both true and only one of them
/// is on the line.
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

    private readonly PositionSeries _series;

    private readonly AnimationPlan _plan;

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

    public PositionRenderer(PositionSeries series, AnimationPlan plan)
    {
        _series = series;
        _plan = plan;

        // One axis for both lines: they are the same quantity in the same currency, and
        // the whole point of the picture is the distance between them.
        _scale = AnimationPlan.NiceScale(Math.Max(series.Peak, 0.0001) * 1.08, 5);
    }

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        context.Backdrop.Fill(session, context, Palette.Background);

        var (index, point) = DrawPlot(session, context, t);

        DrawStats(session, context, t);
        DrawHeader(session, context, t, index, point);
        DrawProgress(session, context, t);
    }

    // ---- plot -----------------------------------------------------------------------

    /// <summary>
    /// The two lines, the fill between them and the end dot; reports the point the
    /// header should be reading out.
    /// </summary>
    private (int Index, PositionPoint Point) DrawPlot(CanvasDrawingSession session, FrameContext context, double t)
    {
        var n = _series.Points.Count;
        var top = context.HeaderRow(PlotTopFraction, ShowTitle);
        var bottom = context.BaselineAbove(CreditGap);
        var span = bottom - top;
        var mx = context.ChartLeft;
        var plotW = context.ChartWidth;

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

        // Which points have arrived, and how far the arriving one has come. The value
        // line eases without overshoot — a total that exceeds its own final value and
        // retreats reads as the data being corrected.
        //
        // The arriving point eases in *from the previous point's level*, not from the
        // baseline. Bars grow from zero because a bar is a column standing on the axis;
        // a line's newest segment would otherwise plunge from the previous close to the
        // floor and climb back, a crack that reads as a crash — glaring in a paused
        // frame, a permanent dent at the leading edge in playback.
        var points = _series.Points;
        var visible = new List<(double X, double YValue, double YCapital)>(n);

        for (var i = 0; i < n; i++)
        {
            var start = _plan.IntroMs + (i * _plan.StaggerMs);
            if (t <= start)
            {
                break;
            }

            var p = Easing.OutCubic(Easing.Ramp(t, start, _plan.BarMs));
            var mark = points[i];
            var x = mx + (n > 1 ? plotW * i / (n - 1) : 0);

            double value, capital;

            if (i == 0)
            {
                // The first point has no level to come from, so it rises from the axis —
                // there is no segment yet, so nothing can crack.
                value = mark.Value * p;
                capital = mark.Capital * p;
            }
            else
            {
                var previous = points[i - 1];
                value = previous.Value + ((mark.Value - previous.Value) * p);
                capital = previous.Capital + ((mark.Capital - previous.Capital) * p);
            }

            visible.Add((x, bottom - (value / _scale.Top * span), bottom - (capital / _scale.Top * span)));
        }

        var movingIndex = visible.Count - 1;

        if (visible.Count > 1)
        {
            DrawFill(session, visible, bottom, introA);

            using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

            DrawLine(session, context, visible, p => p.YValue, Gain, style, introA);
            DrawLine(session, context, visible, p => p.YCapital, Palette.Moving, style, introA);

            // The end dot: where the holding stands right now.
            var (lx, ly) = (visible[^1].X, Math.Min(visible[^1].YValue, visible[^1].YCapital) - context.Px(4));
            var white = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

            void Dot(CanvasDrawingSession ds) =>
                ds.FillCircle((float)lx, (float)ly, (float)context.Px(6), white);

            Ink.Glow(session, context.Px(10), 0.9 * introA, Dot);
            Dot(session);
        }

        DrawLegend(session, context, top, introA);
        DrawXLabels(session, context, t, bottom, introA);

        var safe = movingIndex < 0 ? 0 : movingIndex;

        return (movingIndex, points[safe]);
    }

    /// <summary>The space between the two lines, coloured by which one is on top.</summary>
    private void DrawFill(
        CanvasDrawingSession session, List<(double X, double YValue, double YCapital)> visible,
        double bottom, double opacity)
    {
        var last = visible[^1];
        var colour = last.YValue <= last.YCapital ? Loss : Gain;

        var ring = new Vector2[(visible.Count * 2) + 1];

        for (var i = 0; i < visible.Count; i++)
        {
            ring[i] = new Vector2((float)visible[i].X, (float)visible[i].YValue);
        }

        for (var i = visible.Count - 1; i >= 0; i--)
        {
            ring[visible.Count + (visible.Count - 1 - i)] = new Vector2((float)visible[i].X, (float)visible[i].YCapital);
        }

        // Close along the left edge so the fill is a closed region, not a bow-tie when
        // the lines cross.
        ring[^1] = ring[0];

        using var geometry = CanvasGeometry.CreatePolygon(session, ring);

        session.FillGeometry(geometry, Ink.Fade(colour, 0.14 * opacity));
    }

    private static void DrawLine(
        CanvasDrawingSession session, FrameContext context,
        List<(double X, double YValue, double YCapital)> visible,
        Func<(double X, double YValue, double YCapital), double> y,
        Color colour, CanvasStrokeStyle shared, double opacity)
    {
        var points = new Vector2[visible.Count];

        for (var i = 0; i < visible.Count; i++)
        {
            points[i] = new Vector2((float)visible[i].X, (float)y(visible[i]));
        }

        using var geometry = Polyline(session, points);

        session.DrawGeometry(geometry, Ink.Fade(colour, 0.95 * opacity), (float)context.Px(3), shared);
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

        foreach (var (colour, key) in new[] { (Gain, "DcaLegendValue"), (Palette.Moving, "PositionLegendCapital") })
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
    private void DrawXLabels(CanvasDrawingSession session, FrameContext context, double t, double bottom, double introA)
    {
        var n = _series.Points.Count;
        var mx = context.ChartLeft;
        var plotW = context.ChartWidth;

        var every = Math.Max(1, n / 5);
        if (n % every == 0 && n / every > 5)
        {
            every = Math.Max(1, (n / 6) + 1);
        }

        // A year label when the holding spans years, year-and-month when it spans less —
        // twelve "2024-06" stamps on a decade-long holding is noise nobody reads.
        var longSpan = _series.End.DayNumber - _series.Start.DayNumber > 365 * 3;

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < n; i += every)
        {
            var a = Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), 450) * introA;
            if (a <= 0)
            {
                continue;
            }

            var day = _series.Points[i].Date;
            var text = longSpan ? day.Year.ToString(CultureInfo.InvariantCulture) : day.ToString("yyyy-MM", CultureInfo.InvariantCulture);

            Ink.Centred(session, text, mx + (n > 1 ? plotW * i / (n - 1) : 0), bottom + context.Px(28), format, Palette.DateLabel, a);
        }
    }

    // ---- header ---------------------------------------------------------------------

    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t, int movingIndex, PositionPoint point)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : Strings.Format("PositionDefaultTitle", _series.Name);

        if (ShowTitle)
        {
            var titleSize = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(titleSize, bold: true))
            {
                Ink.Centred(session, title, cx, Row(context, 0.155), format, Palette.Title, a);
            }
        }

        using var small = Ink.Format(context.Px(25));

        // What the holding is: when it was bought, for how much, of what, in whose currency.
        var heldLine = Strings.Format(
            "PositionSubtitleLine",
            Iso(_series.Start),
            DcaRenderer.Money(_series.Capital),
            Strings.Get(CurrencyKey),
            _series.Name);

        Ink.Centred(session, heldLine, cx, Row(context, 0.19), small, Palette.Muted, a);

        // The span, with the days held as the figure the eye stops on.
        var days = (_series.End.DayNumber - _series.Start.DayNumber).ToString("#,##0", CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session,
                Strings.Format("PositionRangeLine", Iso(_series.Start), Iso(_series.End), days),
                days,
                Palette.Muted, Palette.Emphasis,
                small, strong,
                cx, Row(context, 0.218), a);
        }

        if (movingIndex < 0)
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
            Ink.Centred(session, Iso(point.Date), cx, Row(context, 0.2553), dateFormat, Palette.Moving, a);
        }

        // The headline: what the holding is worth over what went in, read off the
        // moment being shown. Its colour follows the sign of what is displayed, so a
        // holding crossing from loss to gain changes the colour of its own number.
        var ret = point.Capital > 0 ? ((point.Value / point.Capital) - 1) * 100 : 0;
        var text = (ret >= 0 ? "+" : string.Empty) + ret.ToString("0.0", CultureInfo.InvariantCulture) + "%";
        var colour = ret >= 0 ? Gain : Loss;

        using (var bigFormat = Ink.Format(context.Px(128), bold: true))
        {
            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, colour));

            Ink.Centred(session, text, cx, Row(context, 0.327), bigFormat, colour, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, Strings.Get("DcaReturnLabel"), cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    // ---- closing --------------------------------------------------------------------

    /// <summary>The four summary cards and the credit, which arrive last.</summary>
    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        // The drawdown is shown as the negative it is a percentage of, not as a
        // magnitude with a minus painted on: a card reading "-31.2%" next to "+143.7%"
        // lets the two signs carry the story.
        var cards = new[]
        {
            (Strings.Get("PositionCardValue"), DcaRenderer.Money(_series.FinalValue), Palette.CardValue),
            (Strings.Get("PositionCardCapital"), DcaRenderer.Money(_series.Capital), Palette.CardValue),
            (Strings.Get("DcaCardProfit"), Sign(_series.Profit) + DcaRenderer.Money(Math.Abs(_series.Profit)),
                _series.Profit >= 0 ? Gain : Loss),
            (Strings.Get("PositionCardDrawdown"),
                (-_series.MaxDrawdownPct).ToString("0.0", CultureInfo.InvariantCulture) + "%", Loss),
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

            Ink.Centred(session, cards[i].Item1, x + (cardWidth / 2), y + context.Px(42), labelFormat, Palette.Muted, a);
            Ink.Centred(session, cards[i].Item2, x + (cardWidth / 2), y + context.Px(92), valueFormat, cards[i].Item3, a);
        }

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
