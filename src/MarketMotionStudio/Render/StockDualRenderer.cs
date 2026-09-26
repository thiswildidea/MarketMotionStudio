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
/// One stock's volume and turnover rate, as two stacked panels — the port of
/// `stock_dual_studio.html`'s whole render path.
///
/// The two modes arrive as one <see cref="StockPanelSeries"/> and differ by flags rather than by
/// types, because they differ in how the same numbers are drawn: daily rate is bars with a line
/// joining their tops, cumulative rate is an area curve that must never be eased with an
/// overshoot — a running total that exceeds its own final value and retreats reads as the data
/// being corrected, not as animation.
///
/// Every geometry figure here is the source's own: the panel top at 0.278 of frame height, the
/// mid gap at 0.081, 107 baseline pixels between the lower baseline and the credit, the panel
/// scale at peak × 1.08 over four gridlines, the mark delays 300/800 for volume and 550/1050 for
/// rate. They were tuned by watching, which is why they are copied rather than re-derived.
/// </summary>
public sealed class StockDualRenderer : IFrameRenderer
{
    /// <summary>Baseline rows between the lower panel's baseline and the credit.</summary>
    private const double CreditGap = 107;

    private const double PanelTopFraction = 0.278;

    private const double PanelMidFraction = 0.081;

    private readonly StockPanelSeries _series;

    private readonly AnimationPlan _plan;

    private readonly (double Step, double Top) _volScale;

    private readonly (double Step, double Top) _rateScale;

    /// <summary>The title, already resolved: the user's text, or the instrument's name.</summary>
    public StockDualRenderer(StockPanelSeries series, AnimationPlan plan)
    {
        _series = series;
        _plan = plan;

        // Each panel carries its own axis — one step for both would leave one panel's gridlines
        // disagreeing with its own data, which reads as that panel being wrong.
        _volScale = AnimationPlan.NiceScale(Math.Max(series.VolumePeak, 0.0001) * 1.08, 4);
        _rateScale = AnimationPlan.NiceScale(Math.Max(series.RatePeak, 0.0001) * 1.08, 4);
    }

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>The venue-prefixed code shown in the header line.</summary>
    public string Code { get; set; } = string.Empty;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * _plan.TotalMs;

        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height), Palette.StockBackground);

        var moving = DrawPanel(session, context, t, isRate: false);
        DrawPanel(session, context, t, isRate: true);
        DrawXLabels(session, context, t, isRate: false);
        DrawXLabels(session, context, t, isRate: true);
        DrawAverage(session, context, t, isRate: false);
        DrawAverage(session, context, t, isRate: true);
        DrawMark(session, context, t, isRate: false, high: true, delay: 300);
        DrawMark(session, context, t, isRate: false, high: false, delay: 800);
        DrawMark(session, context, t, isRate: true, high: true, delay: 550);
        DrawMark(session, context, t, isRate: true, high: false, delay: 1050);
        DrawFooter(session, context, t);
        DrawHeader(session, context, t, moving);
        DrawProgress(session, context);
    }

    /// <summary>The two panels' rectangles. The gap between them is fixed; the bottom margin
    /// decides where the lower one ends and the two share what is left equally.</summary>
    private (double Top, double Bottom) PanelArea(FrameContext context, bool isRate)
    {
        var top = context.HeaderRow(PanelTopFraction, ShowTitle);
        var bottom = context.CreditLine - context.Px(CreditGap);
        var span = (bottom - top - context.Height * PanelMidFraction) / 2;

        return isRate ? (bottom - span, bottom) : (top, top + span);
    }

    /// <summary>
    /// One panel: grid, bars or area curve, its title, unit and the running figure.
    /// </summary>
    /// <returns>The index of the bar still in motion, or the last one — what the header's moving
    /// date tracks.</returns>
    private int DrawPanel(CanvasDrawingSession session, FrameContext context, double t, bool isRate)
    {
        var values = isRate ? _series.Rates : _series.Volumes;
        var scale = isRate ? _rateScale : _volScale;
        var (top, bottom) = PanelArea(context, isRate);
        var span = bottom - top;

        var introA = Easing.Ramp(t, 500, 1500);
        if (introA <= 0 || values.Count == 0)
        {
            return -1;
        }

        var mx = context.ChartLeft;
        var plotW = context.ChartWidth;
        var slot = plotW / values.Count;
        var barW = Math.Max(2, slot * (values.Count > 140 ? 0.86 : 0.74));
        var isArea = isRate && _series.RateIsCumulative;

        // Grid and labels, the lines growing in with the same fade the bars arrive under.
        using (var grid = Ink.Format(context.Px(20)))
        {
            var line = (float)Math.Max(1, context.Px(1));

            for (var v = 0.0; v <= scale.Top + 1e-9; v += scale.Step)
            {
                var y = bottom - (v / scale.Top) * span;

                session.DrawLine(
                    new Vector2((float)mx, (float)y),
                    new Vector2((float)(mx + (plotW * introA)), (float)y),
                    Palette.Grid,
                    line);

                Ink.RightMiddle(session, Format(v, isRate ? 2 : _series.VolumeDecimals),
                    mx - context.Px(12), y, grid, Palette.StockAxisLabel, introA);
            }
        }

        var moving = -1;
        var shown = 0.0;
        var tops = new List<(double X, double Y)>();

        for (var i = 0; i < values.Count; i++)
        {
            var start = _plan.IntroMs + (i * _plan.StaggerMs);
            if (t <= start)
            {
                break;
            }

            var raw = Easing.Ramp(t, start, _plan.BarMs);

            // The cumulative curve decelerates without overshooting; bars flick as they arrive.
            var p = raw < 1 ? (isArea ? Easing.OutCubic(raw) : Math.Max(0, Easing.OutBack(raw))) : 1;
            var value = values[i] * p;

            var x = mx + (slot * i) + ((slot - barW) / 2);
            var h = (value / scale.Top) * span;
            var y = bottom - h;
            var colour = RampColour(isRate, values[i]);

            if (!isArea)
            {
                DrawBar(session, context, x, y, barW, h, colour, growing: raw < 1);
            }

            tops.Add((x + (barW / 2), y));

            if (raw < 1)
            {
                moving = i;
                shown = value;
            }
            else if (i > moving)
            {
                moving = i;
                shown = values[i];
            }
        }

        if (isArea && tops.Count > 1)
        {
            DrawArea(session, context, top, bottom, tops);
        }

        // The daily rate panel joins its bar tops, distinguishing it from the volume panel above
        // — the two would otherwise be near-identical shapes, because on daily data they are
        // strictly proportional.
        if (!isArea && isRate && tops.Count > 1)
        {
            using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };
            using var line = Polyline(session, tops);

            session.DrawGeometry(line, Palette.StockRateLine, (float)context.Px(2.5), style);
        }

        DrawPanelTitle(session, context, top, isRate);

        if (moving >= 0 && (!isRate || _series.HasRate))
        {
            using var format = Ink.Format(context.Px(52), bold: true);

            Ink.Centred(session, Format(shown, isRate ? 2 : _series.VolumeDecimals),
                mx + (plotW / 2), top - context.Px(22), format, RampColour(isRate, values[moving]), introA);
        }

        return moving;
    }

    /// <summary>One bar: a vertical gradient with a solid cap, glowing while it still grows.</summary>
    private void DrawBar(
        CanvasDrawingSession session, FrameContext context,
        double x, double y, double w, double h, Color colour, bool growing)
    {
        var top = Ink.Fade(colour, 0.98);
        var tail = Ink.Fade(colour, 0.28);

        void Shape(CanvasDrawingSession ds)
        {
            using var brush = new CanvasLinearGradientBrush(
                ds,
                [
                    new CanvasGradientStop { Position = 0f, Color = top },
                    new CanvasGradientStop { Position = 1f, Color = tail },
                ])
            {
                StartPoint = new Vector2((float)x, (float)y),
                EndPoint = new Vector2((float)x, (float)(y + h)),
            };

            ds.FillRectangle((float)x, (float)y, (float)w, (float)h, brush);
            ds.FillRectangle((float)x, (float)y, (float)w, (float)Math.Min(context.Px(3), h), colour);
        }

        // The source's shadowBlur of 22 is a Gaussian sigma of about 11 — see Ink.Glow.
        if (growing)
        {
            Ink.Glow(session, context.Px(11), 0.8, Shape);
        }
        else
        {
            Shape(session);
        }
    }

    /// <summary>The cumulative rate's area: gradient fill, glowing stroke, a light on the end.</summary>
    private void DrawArea(
        CanvasDrawingSession session, FrameContext context, double top, double bottom,
        List<(double X, double Y)> points)
    {
        var line = Palette.Rate(0.9);
        var fade = Palette.Rate(0.1);

        using var fill = new CanvasLinearGradientBrush(
            session,
            [
                new CanvasGradientStop { Position = 0f, Color = Ink.Fade(line, 0.5) },
                new CanvasGradientStop { Position = 1f, Color = Ink.Fade(fade, 0.05) },
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

        using var stroke = Polyline(session, points);
        using var style = new CanvasStrokeStyle { LineJoin = CanvasLineJoin.Round };

        session.DrawGeometry(stroke, Ink.Fade(line, 0.95), (float)context.Px(3.2), style);
        Ink.Glow(session, context.Px(9), 0.85,
            ds => ds.DrawGeometry(stroke, Ink.Fade(line, 0.95), (float)context.Px(3.2), style));

        var (lx, ly) = points[^1];
        var white = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

        void Dot(CanvasDrawingSession ds) =>
            ds.FillCircle((float)lx, (float)ly, (float)context.Px(7), white);

        Ink.Glow(session, context.Px(11), 1, Dot);
        Dot(session);
    }

    /// <summary>The panel's name and unit, over its top-left corner.</summary>
    private void DrawPanelTitle(CanvasDrawingSession session, FrameContext context, double top, bool isRate)
    {
        var introA = 1.0;
        var mx = context.ChartLeft;

        var title = isRate
            ? Strings.Get(_series.RateIsCumulative ? "StockPanelCumTurnover" : "StockPanelTurnover")
            : Strings.Get(_series.RateIsCumulative ? "StockPanelMinuteVolume" : "StockPanelVolume");

        using (var format = Ink.Format(context.Px(30), bold: true))
        {
            Ink.Left(session, title, mx, top - context.Px(26), format, Palette.StockPanelTitle, introA);

            var width = Ink.Measure(session, title, format);

            using var unitFormat = Ink.Format(context.Px(21));

            Ink.Left(session, $"（{(_series.RateIsCumulative && !isRate ? _series.VolumeUnit : isRate ? "%" : _series.VolumeUnit)}）",
                mx + width + context.Px(58), top - context.Px(26), unitFormat, Palette.StockUnit, introA);
        }
    }

    /// <summary>X labels under a panel, each fading in as its own bar arrives.</summary>
    private void DrawXLabels(CanvasDrawingSession session, FrameContext context, double t, bool isRate)
    {
        var (_, bottom) = PanelArea(context, isRate);
        var mx = context.ChartLeft;
        var slot = context.ChartWidth / _series.Count;
        var barW = Math.Max(2, slot * (_series.Count > 140 ? 0.86 : 0.74));
        var every = Math.Max(1, (int)Math.Ceiling(_series.Count / 8.0));

        using var format = Ink.Format(context.Px(19));

        for (var i = 0; i < _series.Count; i += every)
        {
            var a = Easing.Ramp(t, _plan.IntroMs + (i * _plan.StaggerMs), 450);
            if (a <= 0)
            {
                continue;
            }

            Ink.Centred(session, _series.Labels[i],
                mx + (slot * i) + (slot / 2), bottom + context.Px(28), format, Palette.StockDateLabel, a);
        }
    }

    /// <summary>
    /// The closing line: the mean for bars, the final value for the cumulative curve — a mean of a
    /// running total is its last value's shape, annotated pointlessly at the same height.
    /// </summary>
    private void DrawAverage(CanvasDrawingSession session, FrameContext context, double t, bool isRate)
    {
        var a = Easing.Ramp(t, _plan.FinaleStartMs, 1100);
        if (a <= 0 || (isRate && !_series.HasRate))
        {
            return;
        }

        var (top, bottom) = PanelArea(context, isRate);
        var mx = context.ChartLeft;
        var plotW = context.ChartWidth;
        var isArea = isRate && _series.RateIsCumulative;
        var values = isRate ? _series.Rates : _series.Volumes;
        var scale = isRate ? _rateScale : _volScale;

        var at = isArea ? values[^1] : values.Average();
        var y = bottom - (at / scale.Top) * (bottom - top);

        var line = isArea ? Palette.StockFinalRateLine : Palette.AverageLine;

        using (var dashed = new CanvasStrokeStyle
        {
            // The source's [9, 7] dash pattern; the plain Dash style is the platform's own
            // take on the same rhythm and is what the whole-market page dashes with.
            DashStyle = CanvasDashStyle.Dash,
        })
        {
            session.DrawLine(
                new Vector2((float)mx, (float)y),
                new Vector2((float)(mx + (plotW * Easing.OutCubic(a))), (float)y),
                line,
                (float)context.Px(1.8),
                dashed);
        }

        if (a > 0.5)
        {
            var label = isArea
                ? Strings.Format("StockDayTurnover", Format(_series.FinalRate, 2))
                : Strings.Format("StockMeanLabel", Format(values.Average(), isRate ? 2 : _series.VolumeDecimals));

            using var format = Ink.Format(context.Px(isArea ? 22 : 21), bold: isArea);

            Ink.Left(session, label, mx + context.Px(12), y - context.Px(isArea ? 11 : 10),
                format, isArea ? Palette.StockFinalRateLabel : Palette.AverageLabel, (a - 0.5) / 0.5);
        }
    }

    /// <summary>Boxes the peak or the trough bar — two beats, the high leading the low.</summary>
    private void DrawMark(CanvasDrawingSession session, FrameContext context, double t, bool isRate, bool high, double delay)
    {
        // A cumulative curve's peak is necessarily its last point and its trough its first; the
        // boxes would state what the shape already says.
        if (isRate && _series.RateIsCumulative)
        {
            return;
        }

        var a = Easing.Ramp(t, _plan.FinaleStartMs + delay, 650);
        if (a <= 0 || (isRate && !_series.HasRate))
        {
            return;
        }

        var values = isRate ? _series.Rates : _series.Volumes;
        var scale = isRate ? _rateScale : _volScale;
        var index = high
            ? (isRate ? IndexOf(values, values.Max()) : _series.VolumePeakIndex)
            : (isRate ? IndexOf(values, values.Min()) : _series.VolumeLowIndex);

        if (index < 0)
        {
            return;
        }

        var (top, bottom) = PanelArea(context, isRate);
        var mx = context.ChartLeft;
        var slot = context.ChartWidth / _series.Count;
        var barW = Math.Max(2, slot * (_series.Count > 140 ? 0.86 : 0.74));

        var x = mx + (slot * index) + ((slot - barW) / 2);
        var h = (values[index] / scale.Top) * (bottom - top);
        var y = bottom - h;

        var colour = high ? Palette.Moving : Palette.MarkLow;

        session.DrawRectangle(
            (float)(x - context.Px(3)), (float)(y - context.Px(3)),
            (float)(barW + context.Px(6)), (float)(h + context.Px(5)),
            colour, (float)context.Px(3));

        using var format = Ink.Format(context.Px(21), bold: true);

        Ink.Centred(session, Strings.Get(high ? "StockHighLabel" : "StockLowLabel"),
            x + (barW / 2), y - context.Px(16), format, colour, a);
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
    /// The header block: title, the code-and-range line with the count picked out, and the date
    /// moving through the animation.
    /// </summary>
    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t, int moving)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;
        var iso = CultureInfo.InvariantCulture;

        var title = Title.Length > 0 ? Title : _series.Name;

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, title, context.Px(64), context.Width - context.Px(120), bold: true);

            using (var format = Ink.Format(size, bold: true))
            {
                Ink.Centred(session, title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, a);
            }
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            var code = Code.ToUpperInvariant() + " · ";

            List<(string, Color, CanvasTextFormat)> runs = [];

            if (_series.RateIsCumulative && _series.Day is { Length: 8 } day)
            {
                runs.Add((code, Palette.StockMuted, plain));
                runs.Add((
                    $"{day[..4]}-{day[4..6]}-{day[6..]}",
                    Palette.Moving, strong));
                runs.Add((" " + Strings.Get("StockIntradayLabel") + " · ", Palette.StockMuted, plain));
            }
            else
            {
                // Full ISO dates in the header, where there is room for them; the axis below
                // carries the short forms.
                var span = _series.FileNameSpan.Split('_');

                runs.Add((
                    $"{code}{(span.Length > 0 ? span[0] : _series.Labels[0])} {Strings.Get("StockRangeJoiner")} {(span.Length > 1 ? span[1] : _series.Labels[^1])} · ",
                    Palette.StockMuted, plain));
            }

            runs.Add(((_series.Count).ToString(iso), Palette.Emphasis, strong));
            runs.Add((" " + Strings.Get(_series.RateIsCumulative ? "StockMinutesUnit" : "StockTradingDaysUnit"),
                Palette.StockMuted, plain));

            Ink.Runs(session, runs, cx, context.HeaderRow(0.188, ShowTitle), a);
        }

        if (moving >= 0)
        {
            using var format = Ink.Format(context.Px(40), bold: true);

            // The moving date is drawn from the labels themselves: `09:30` in the intraday mode,
            // where the source had a separate date line, because the label is already the moment.
            Ink.Centred(session, _series.Labels[moving], cx, context.HeaderRow(0.222, ShowTitle),
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

    private Color RampColour(bool isRate, double value) => isRate
        ? Palette.Rate(Position(_series.Rates, value))
        : Palette.Volume(Position(_series.Volumes, value));

    private static double Position(IReadOnlyList<double> values, double value)
    {
        var spread = values.Count > 0 ? values.Max() - values.Min() : 0;

        return spread <= 0 ? 1 : (value - values.Min()) / spread;
    }

    private static int IndexOf(IReadOnlyList<double> values, double value)
    {
        for (var i = 0; i < values.Count; i++)
        {
            if (values[i] == value)
            {
                return i;
            }
        }

        return -1;
    }

    /// <summary>Builds an open polyline through the points.</summary>
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

    /// <summary>Grouped thousands with the panel's own decimals, the read-out's and the axis' format.</summary>
    private static string Format(double value, int decimals) =>
        value.ToString("N" + decimals.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);
}
