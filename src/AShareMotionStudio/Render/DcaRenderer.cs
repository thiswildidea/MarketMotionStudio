using System.Globalization;
using System.Numerics;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Windows.Foundation;
using Windows.UI;

namespace AShareMotionStudio.Render;

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

    /// <summary>A plan that is ahead. The market's own convention: gains in red.</summary>
    private static readonly Color Gain = Palette.Emphasis;

    /// <summary>A plan that is behind. Cool, deliberately not the bar ramp's blue — a loss
    /// should read as absence of gain, not as a different measurement.</summary>
    private static readonly Color Loss = Rgb(0x34, 0xD3, 0x99);

    private readonly DcaSeries _series;

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

    public DcaRenderer(DcaSeries series, AnimationPlan plan)
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

        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height), Palette.Background);

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
    private (int Index, DcaPoint Point) DrawPlot(CanvasDrawingSession session, FrameContext context, double t)
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

                Ink.RightMiddle(session, Money(v), mx - context.Px(12), y, gridFormat, Palette.AxisLabel, introA);
            }
        }

        // Which points have arrived, and how far the arriving one has grown. The lines
        // are cumulative, so growth eases without overshoot — a total that exceeds its
        // own final value and retreats reads as the data being corrected.
        var points = _series.Points;
        var visible = new List<(double X, double YValue, double YInvested)>(n);

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

            visible.Add((x, bottom - (mark.Value * p / _scale.Top * span), bottom - (mark.Invested * p / _scale.Top * span)));
        }

        var movingIndex = visible.Count - 1;

        if (visible.Count > 1)
        {
            DrawFill(session, visible, bottom, introA);

            using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

            DrawLine(session, context, visible, p => p.YValue, Gain, style, introA);
            DrawLine(session, context, visible, p => p.YInvested, Palette.Moving, style, introA);

            // The end dot: where the plan stands right now.
            var (lx, ly) = (visible[^1].X, Math.Min(visible[^1].YValue, visible[^1].YInvested) - context.Px(4));
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
        CanvasDrawingSession session, List<(double X, double YValue, double YInvested)> visible,
        double bottom, double opacity)
    {
        var last = visible[^1];
        var colour = last.YValue <= last.YInvested ? Loss : Gain;

        var ring = new Vector2[(visible.Count * 2) + 1];

        for (var i = 0; i < visible.Count; i++)
        {
            ring[i] = new Vector2((float)visible[i].X, (float)visible[i].YValue);
        }

        for (var i = visible.Count - 1; i >= 0; i--)
        {
            ring[visible.Count + (visible.Count - 1 - i)] = new Vector2((float)visible[i].X, (float)visible[i].YInvested);
        }

        // Close along the left edge so the fill is a closed region, not a bow-tie when
        // the lines cross.
        ring[^1] = ring[0];

        using var geometry = CanvasGeometry.CreatePolygon(session, ring);

        session.FillGeometry(geometry, Ink.Fade(colour, 0.14 * opacity));
    }

    private static void DrawLine(
        CanvasDrawingSession session, FrameContext context,
        List<(double X, double YValue, double YInvested)> visible,
        Func<(double X, double YValue, double YInvested), double> y,
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

        foreach (var (colour, key) in new[] { (Gain, "DcaLegendValue"), (Palette.Moving, "DcaLegendInvested") })
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

        // A year label when the plan spans years, year-and-month when it spans less —
        // twelve "2024-06" stamps on a decade-long plan is noise nobody reads.
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
        CanvasDrawingSession session, FrameContext context, double t, int movingIndex, DcaPoint point)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : Strings.Format("DcaDefaultTitle", _series.Name);

        if (ShowTitle)
        {
            var titleSize = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(titleSize, bold: true))
            {
                Ink.Centred(session, title, cx, Row(context, 0.155), format, Palette.Title, a);
            }
        }

        using var small = Ink.Format(context.Px(25));

        // What the plan is: the fixed amount, how often, into what, in whose currency.
        var frequency = _series.Frequency switch
        {
            DcaFrequency.Weekly => Strings.Get("DcaFreqWeekly"),
            DcaFrequency.Monthly => Strings.Get("DcaFreqMonthly"),
            _ => Strings.Get("DcaFreqDaily"),
        };

        var planLine = Strings.Format(
            "DcaSubtitleLine",
            frequency,
            _series.Amount.ToString("0", CultureInfo.InvariantCulture),
            Strings.Get(CurrencyKey),
            _series.Name);

        Ink.Centred(session, planLine, cx, Row(context, 0.19), small, Palette.Muted, a);

        // The span, with the count of buys as the figure the eye stops on.
        var buys = _series.Buys.ToString("#,##0", CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session,
                Strings.Format("DcaRangeLine", Iso(_series.Start), Iso(_series.End), buys),
                buys,
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
            Ink.Centred(session, Iso(point.Date), cx, Row(context, 0.262), dateFormat, Palette.Moving, a);
        }

        // The headline: what the plan has returned over what was paid in, read off the
        // moment being shown. Its colour follows the sign of what is displayed, so a
        // plan crossing from loss to gain changes the colour of its own number.
        var ret = point.Invested > 0 ? ((point.Value / point.Invested) - 1) * 100 : 0;
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

        var cards = new[]
        {
            (Strings.Get("DcaCardValue"), Money(_series.FinalValue), Palette.CardValue),
            (Strings.Get("DcaCardInvested"), Money(_series.FinalInvested), Palette.CardValue),
            (Strings.Get("DcaCardProfit"), Sign(_series.Profit) + Money(Math.Abs(_series.Profit)),
                _series.Profit >= 0 ? Gain : Loss),
            (Strings.Get("DcaCardBuys"), _series.Buys.ToString("#,##0", CultureInfo.InvariantCulture), Palette.CardValue),
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
