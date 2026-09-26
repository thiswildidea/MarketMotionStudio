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
/// Turnover as bars along a time axis, growing in sequence and then having their mean and
/// extremes called out.
///
/// The form for "how did turnover move over this stretch": the horizontal axis is time, so a run
/// of heavy days reads as a run.
/// </summary>
/// <remarks>
/// Turnover only. A bar chart of daily percentage change would need a zero line with bars going
/// both ways, which is a different drawing rather than this one with different numbers — and the
/// calendar already answers that question better, because what you want from returns is *when*.
/// </remarks>
public sealed class BarRaceRenderer(TurnoverSeries series, AnimationPlan plan)
    : TurnoverRenderer(series, plan, Metric.Turnover)
{
    protected override (int Index, double Value) DrawPlot(
        CanvasDrawingSession session, FrameContext context, double t)
    {
        var left = context.ChartLeft;
        var width = context.ChartWidth;
        var baseline = context.BaselineAbove(CreditGap);
        var plotTop = Row(context, PlotTopFraction);
        var plotHeight = Math.Max(1, baseline - plotTop);

        DrawAxes(session, context, t, left, width, baseline, plotHeight);

        var moving = DrawBars(session, context, t, left, width, baseline, plotHeight);

        DrawDateLabels(session, context, t, left, width, baseline);
        DrawAverage(session, context, t, left, width, baseline, plotHeight);

        // Two beats rather than one: the high is boxed first and the low follows, so the eye is
        // taken to them in turn. The delays live here because they are pacing; which days they name
        // lives on the metric.
        var extremes = Metric.Extremes(Series);
        var colours = new[] { Palette.Moving, Palette.MarkLow };
        var delays = new[] { 350.0, 1000.0 };

        for (var i = 0; i < extremes.Length && i < colours.Length; i++)
        {
            DrawExtreme(session, context, t, left, width, baseline, plotHeight,
                extremes[i].Index, extremes[i].Label, colours[i], delays[i]);
        }

        return moving;
    }

    /// <summary>Gridlines and their labels, drawing in from the left as they appear.</summary>
    private void DrawAxes(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double plotHeight)
    {
        var a = Easing.Ramp(t, 500, 1500);

        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(21));
        var stroke = (float)Math.Max(1, context.Scale);

        for (var v = 0.0; v <= Plan.AxisTop + 1e-6; v += Plan.AxisStep)
        {
            var y = (float)(baseline - (v / Plan.AxisTop * plotHeight));

            session.DrawLine(
                new Vector2((float)left, y),
                new Vector2((float)(left + (width * a)), y),
                Ink.Fade(Palette.Grid, a),
                stroke);

            // Drawn leftwards from the gridline's start. This is what the left margin has to leave
            // room for: too small a value does not crop the chart, it pushes these numbers off the
            // edge of the frame.
            Ink.RightMiddle(session, Round(v), left - context.Px(12), y, format, Palette.AxisLabel, a);
        }
    }

    /// <summary>Where bar <paramref name="i"/> sits and how wide it is.</summary>
    private (double X, double Width) BarBox(FrameContext context, double left, double width, int i)
    {
        var slot = width / Series.Count;

        // Tighter packing once the bars are thin: at 140-plus the gap dominates and the chart reads
        // as a comb rather than as a series.
        var fill = Series.Count > 140 ? 0.86 : 0.74;
        var bar = Math.Max(2 * context.Scale, slot * fill);

        return (left + (slot * i) + ((slot - bar) / 2), bar);
    }

    private (int Index, double Value) DrawBars(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double plotHeight)
    {
        var index = -1;
        var value = 0.0;

        for (var i = 0; i < Series.Count; i++)
        {
            var startsAt = Plan.IntroMs + (i * Plan.StaggerMs);

            // Bars start in order, so the first one that has not begun ends the loop — there is
            // nothing after it to draw.
            if (t <= startsAt)
            {
                break;
            }

            var raw = Math.Clamp((t - startsAt) / Plan.BarMs, 0, 1);

            // Clamped at zero because the overshoot curve dips below it at the very start; a
            // negative height would draw the bar hanging under the axis for a frame.
            var grown = Math.Max(0, raw < 1 ? Easing.OutBack(raw) : 1);

            var (x, barWidth) = BarBox(context, left, width, i);
            var height = Series.Totals[i] * grown / Plan.AxisTop * plotHeight;
            var y = baseline - height;
            var colour = Metric.Colour(Series, i);
            var box = new Rect(x, y, barWidth, height);

            if (raw < 1)
            {
                // The bar still growing is the one the eye should be on, so it carries a halo its
                // finished neighbours do not.
                Ink.Glow(session, context.Px(12), 0.8, ds => ds.FillRectangle(box, colour));
                index = i;
                value = Series.Totals[i] * grown;
            }

            Ink.FillVertical(
                session, box,
                [(0f, Ink.Fade(colour, 0.98)), (1f, Ink.Fade(colour, 0.30))]);

            // A solid cap, so a bar whose body fades to 30 per cent still has a definite top.
            session.FillRectangle(new Rect(x, y, barWidth, Math.Min(context.Px(3), height)), colour);

            if (raw >= 1 && i > index)
            {
                index = i;
                value = Series.Totals[i];
            }
        }

        return (index, value);
    }

    /// <summary>Dates under the bars, thinned to about nine so they never collide.</summary>
    private void DrawDateLabels(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline)
    {
        var every = Math.Max(1, (int)Math.Ceiling(Series.Count / 9.0));

        using var format = Ink.Format(context.Px(20));

        for (var i = 0; i < Series.Count; i += every)
        {
            // Each label fades in with its own bar rather than the block appearing at once.
            var a = Easing.Ramp(t, Plan.IntroMs + (i * Plan.StaggerMs), 450);

            if (a <= 0)
            {
                continue;
            }

            var (x, barWidth) = BarBox(context, left, width, i);

            Ink.Centred(
                session,
                Series.Dates[i].ToString("MM-dd", CultureInfo.InvariantCulture),
                x + (barWidth / 2), baseline + context.Px(30),
                format, Palette.DateLabel, a);
        }
    }

    /// <summary>The mean, as a dashed line that draws itself in during the closing stretch.</summary>
    private void DrawAverage(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double plotHeight)
    {
        var a = Easing.Ramp(t, Plan.FinaleStartMs, 1100);

        if (a <= 0)
        {
            return;
        }

        var y = (float)(baseline - (Series.Average / Plan.AxisTop * plotHeight));
        var thickness = (float)context.Px(2);

        // Win2D's dash lengths are multiples of the stroke width, where a canvas takes them in
        // pixels. Dividing by the thickness is what keeps a 9-on-7-off dash the same pattern at
        // every resolution instead of scaling twice.
        var dashes = new CanvasStrokeStyle
        {
            CustomDashStyle = [(float)(context.Px(9) / thickness), (float)(context.Px(7) / thickness)],
        };

        session.DrawLine(
            new Vector2((float)left, y),
            new Vector2((float)(left + (width * Easing.OutCubic(a))), y),
            Ink.Fade(Palette.AverageLine, a),
            thickness,
            dashes);

        if (a > 0.5)
        {
            using var format = Ink.Format(context.Px(22));

            Ink.Left(
                session,
                Strings.Format("TurnoverAverageLabel", Round(Series.Average)),
                left + context.Px(12), y - context.Px(11),
                format, Palette.AverageLabel, (a - 0.5) / 0.5);
        }
    }

    /// <summary>One extreme, boxed and labelled with its date.</summary>
    private void DrawExtreme(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double plotHeight,
        int index, string label, Color colour, double delayMs)
    {
        var a = Easing.Ramp(t, Plan.FinaleStartMs + delayMs, 650);

        if (a <= 0 || Series.Count == 0)
        {
            return;
        }

        var (x, barWidth) = BarBox(context, left, width, index);
        var height = Series.Totals[index] / Plan.AxisTop * plotHeight;
        var y = baseline - height;
        var pad = context.Px(3);

        session.DrawRectangle(
            new Rect(x - pad, y - pad, barWidth + (pad * 2), height + (pad * 5 / 3)),
            Ink.Fade(colour, a),
            (float)context.Px(3));

        using var strong = Ink.Format(context.Px(22), bold: true);
        using var plain = Ink.Format(context.Px(19));

        Ink.Centred(session, label, x + (barWidth / 2), y - context.Px(18), strong, colour, a);

        Ink.Centred(
            session,
            Series.Dates[index].ToString("MM-dd", CultureInfo.InvariantCulture),
            x + (barWidth / 2), y - context.Px(42),
            plain, Palette.AverageLabel, a);
    }
}
