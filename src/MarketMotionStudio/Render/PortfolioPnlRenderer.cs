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
/// A day of a portfolio, minute by minute: the running profit or loss from 09:30 to the last
/// print, drawn against the zero line it started from.
///
/// <para>
/// **The zero line is the subject, not a gridline.** Every other chart in this app plots a
/// quantity that is positive by nature — a turnover, a market value, a price — so its axis runs
/// from zero up. A day's profit crosses zero, and the one thing a reader looks for is where it
/// crossed: the moment the morning's gain became an afternoon's loss. So the axis is scaled to
/// both sides of zero, the area between the curve and zero is filled in the sign's colour, and the
/// fill sits *under* the line rather than under the frame.
/// </para>
///
/// <para>
/// Red up, green down — the mainland convention and the opposite of the Western one, as everywhere
/// else in this app. It is not a setting for the same reason it is not one elsewhere: these
/// videos are published to an audience that reads it one way.
/// </para>
/// </summary>
/// <param name="crossSafeRight">
/// Whether the picture may run into the band the host covers with its button rail. A
/// constructor argument and not a property, as on every other page: a setting the renderer read
/// back off a mutable property would arrive as the default on the frame that mattered, with the
/// checkbox still looking switched on.
/// </param>
/// <param name="mascot">
/// Whether the head of the curve carries a bull or a bear. A decoration is switched on, never
/// assumed, so the page offers it off.
/// </param>
/// <param name="dynamicAxis">
/// Whether the vertical axis follows the curve drawn so far instead of being fixed at the whole
/// day's excursion from the first frame. Off is what the page shipped with, and the option exists
/// because a quiet morning followed by a violent afternoon otherwise draws the afternoon at the
/// same scale as the morning and flattens it.
/// </param>
public sealed class PortfolioPnlRenderer(
    PortfolioSession session, AnimationPlan plan,
    bool crossSafeRight = false, bool mascot = false, bool dynamicAxis = false) : IFrameRenderer
{
    /// <summary>Distance from the credit up to the top of the statistic cards.</summary>
    private const double CardsAboveCredit = 192;

    /// <summary>Radius of the bull/bear badge, in baseline pixels.</summary>
    private const double MascotRadius = 30;

    /// <summary>Where the plot's top edge sits when the title is one line.</summary>
    private const double PlotTop = 0.395;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all.</summary>
    public bool ShowTitle { get; set; } = true;

    private readonly TitleBlock _title = new(62);

    private int _titleLines;

    private double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, _titleLines);

    /// <summary>Every frame names the day it is drawing, because it is not always today.</summary>
    private string ResolvedTitle() => Title.Length > 0 ? Title : Strings.Get("PortfolioPnlTitle");

    public void Draw(CanvasDrawingSession session2, FrameContext context)
    {
        var t = context.Progress * plan.TotalMs;

        _titleLines = _title.For(session2, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session2, context, Palette.Background);

        var left = context.ChartLeft;

        // The rail the host draws its avatar and comment button in is 194 px of a 1080-wide
        // frame — wider than the default right margin of 150 — so a plot measured to the margin
        // alone runs 44 px into it. Off, the picture keeps clear of it, and *only* clear: a margin
        // already wider than the rail keeps the width it asked for rather than being stretched out
        // to the frame's edge. On, the margin is the only answer, which is what the setting means.
        var right = crossSafeRight ? context.ChartRight : Math.Min(context.ChartRight, context.SafeRight());
        var width = Math.Max(1, right - left);

        var baseline = context.BaselineAbove(TurnoverRenderer.CreditGap);
        var top = Row(context, PlotTop);

        // How far along the curve the frame has come, worked out once: the axis reads it (dynamic
        // axis), the curve is drawn to it, and the badge rides it. Three answers to one question
        // would be three chances to disagree about where "now" is.
        var last = session.Samples.Count - 1;
        var p = Easing.Ramp(t, plan.IntroMs, Math.Max(1, plan.FinaleStartMs - plan.IntroMs));
        var shown = last < 1 ? -1 : Math.Min(last, (int)Math.Floor(p * last));
        var here = shown >= 0 ? session.Samples[shown].Pnl : 0;

        var (high, low) = Range(shown);

        DrawLunch(session2, context, left, width, top, baseline, high, low);
        DrawGrid(session2, context, t, left, width, top, baseline, high, low);

        var (index, value) = DrawCurve(
            session2, context, shown, p, left, width, top, baseline, high, low);

        DrawTrades(session2, context, index, left, width, top, baseline, high, low);
        DrawMascot(session2, context, shown, p, here, left, width, top, baseline, high, low);
        DrawClocks(session2, context, t, left, width, baseline);
        DrawRateNote(session2, context, t, left, width, baseline);
        DrawStats(session2, context, t);
        DrawHeader(session2, context, t, index, value);
        DrawProgress(session2, context, t);
    }

    /// <summary>
    /// The top and bottom of the axis, padded so the curve never touches the frame.
    ///
    /// Zero is always inside the range even on a day that only went one way, because the distance
    /// from zero *is* the number being drawn: a curve that started at the frame's bottom edge
    /// would say "this begins at minus one" to anyone reading the axis.
    ///
    /// <paramref name="shown"/> is how far the animation has come. With the dynamic axis on, the
    /// range is the running extreme of the points drawn so far rather than the whole day's — so a
    /// violent afternoon is drawn at its own scale instead of being flattened by a morning that
    /// happened to travel further. At the last point the running extreme *is* the whole day's, so
    /// the closing frame is the same axis the fixed scale always drew and a cover taken from it
    /// matches one drawn with the option off.
    /// </summary>
    private (double High, double Low) Range(int shown)
    {
        var peak = session.Peak;
        var trough = session.Trough;

        if (dynamicAxis && shown >= 0)
        {
            peak = 0;
            trough = 0;

            for (var i = 0; i <= shown && i < session.Samples.Count; i++)
            {
                peak = Math.Max(peak, session.Samples[i].Pnl);
                trough = Math.Min(trough, session.Samples[i].Pnl);
            }
        }

        var high = Math.Max(0, peak);
        var low = Math.Min(0, trough);

        if (high - low < 1e-9)
        {
            return (1, -1);
        }

        return (high > 0 ? high * 1.12 : 0, low < 0 ? low * 1.12 : 0);
    }

    private static double Y(double value, double top, double height, double high, double low) =>
        top + ((high - value) / (high - low) * height);

    /// <summary>
    /// The lunch break, shaded rather than merely skipped over.
    ///
    /// The curve is flat across it — nothing traded, so nothing moved — and a flat stretch of two
    /// hours is the one feature of the shape a reader will otherwise read as a mistake. The band
    /// is drawn on the clock, so an afternoon that resumed at 13:00 is visibly a second session.
    /// </summary>
    private void DrawLunch(
        CanvasDrawingSession session2, FrameContext context,
        double left, double width, double top, double baseline, double high, double low)
    {
        var (from, to) = Lunch();

        var x0 = X(from, left, width);
        var x1 = X(to, left, width);

        if (x1 <= x0)
        {
            return;
        }

        session2.FillRectangle(
            (float)x0, (float)top, (float)(x1 - x0), (float)(baseline - top),
            Ink.Fade(Palette.Grid, 0.55));

        using var format = Ink.Format(context.Px(18));

        Ink.Centred(session2, Strings.Get("PortfolioPnlNoon"), (x0 + x1) / 2, top + context.Px(26),
            format, Palette.AxisLabel, 0.8);
    }

    /// <summary>
    /// Which band is the lunch break: Shanghai and Shenzhen stop at 11:30, Hong Kong at 12:00,
    /// and both resume at 13:00. A book holding both is shaded from the earlier of the two.
    /// </summary>
    private (int From, int To) Lunch()
    {
        var mainland = session.Holdings.Any(h => h.HasSession && !h.IsHongKong);

        // The same three numbers as the axis in IntradayPnl: Shanghai and Shenzhen stop at
        // 11:30, Hong Kong at 12:00, and both resume at 13:00. Asked here once, from the one
        // source, so the band and the axis cannot drift apart.
        return (mainland ? IntradayPnl.MainlandLunch : IntradayPnl.KongLunch, IntradayPnl.AfternoonOpen);
    }

    /// <summary>Minutes since midnight to an x position on the session's clock.</summary>
    private double X(int minute, double left, double width)
    {
        var span = Math.Max(1, session.CloseMinute - session.OpenMinute);

        return left + (width * (minute - session.OpenMinute) / (double)span);
    }

    private void DrawGrid(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double width, double top, double baseline, double high, double low)
    {
        var a = Easing.Ramp(t, 500, 1500);

        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(21));
        var stroke = (float)Math.Max(1, context.Scale);
        var span = high - low;

        var (step, _) = AnimationPlan.NiceScale(span / 4, 1);

        for (var v = Math.Ceiling(low / step) * step; v <= high + 1e-6; v += step)
        {
            var y = (float)Y(v, top, baseline - top, high, low);
            var zero = Math.Abs(v) < step / 2;

            session2.DrawLine(
                new Vector2((float)left, y),
                new Vector2((float)(left + (width * a)), y),
                Ink.Fade(zero ? Palette.AverageLine : Palette.Grid, a * (zero ? 0.75 : 1)),
                stroke * (zero ? 1.6f : 1f));

            Ink.RightMiddle(session2, Short(v), left - context.Px(12), y, format, Palette.AxisLabel, a);
        }
    }

    /// <summary>
    /// The curve up to the minute the animation has reached, with the ground between it and zero
    /// filled in the sign of the moment.
    ///
    /// The fill is built as its own closed path rather than by filling the open one: filling an
    /// open figure closes it with a chord back to the start, which would paint a triangle across
    /// the frame instead of the ground between the curve and the zero line.
    /// </summary>
    private (int Index, double Value) DrawCurve(
        CanvasDrawingSession session2, FrameContext context, int shown, double p,
        double left, double width, double top, double baseline, double high, double low)
    {
        if (shown < 0)
        {
            return (-1, 0);
        }

        var value = session.Samples[shown].Pnl;
        var zeroY = (float)Y(0, top, baseline - top, high, low);

        double XS(int i) => X(session.Samples[i].Minute, left, width);
        double YS(int i) => Y(session.Samples[i].Pnl, top, baseline - top, high, low);

        var head = new Vector2((float)XS(shown), (float)YS(shown));
        var positive = value >= 0;
        var colour = positive ? Palette.Emphasis : Palette.Fall;

        // The fill, drawn first so the line sits on top of it.
        var area = new CanvasPathBuilder(session2);
        area.BeginFigure(new Vector2((float)XS(0), zeroY));

        for (var i = 0; i <= shown; i++)
        {
            area.AddLine(new Vector2((float)XS(i), (float)YS(i)));
        }

        area.AddLine(new Vector2(head.X, zeroY));
        area.EndFigure(CanvasFigureLoop.Closed);

        using (var ground = CanvasGeometry.CreatePath(area))
        {
            session2.FillGeometry(ground, Ink.Fade(colour, 0.22));
        }

        // The line.
        var shape = new CanvasPathBuilder(session2);
        shape.BeginFigure(new Vector2((float)XS(0), (float)YS(0)));

        for (var i = 1; i <= shown; i++)
        {
            shape.AddLine(new Vector2((float)XS(i), (float)YS(i)));
        }

        shape.AddLine(head);
        shape.EndFigure(CanvasFigureLoop.Open);

        using (var line = CanvasGeometry.CreatePath(shape))
        {
            session2.DrawGeometry(line, colour, (float)context.Px(4));
        }

        // Where the day's extremes were. Marked with their clock and their number: a marker
        // without a value is a dot a reader has to guess the meaning of.
        Mark(session2, context, session.PeakMinute, session.Peak, shown, left, width, top, baseline, high, low, positive: true);
        Mark(session2, context, session.TroughMinute, session.Trough, shown, left, width, top, baseline, high, low, positive: false);

        if (p > 0)
        {
            var r = (float)context.Px(10);

            Ink.Glow(session2, context.Px(12), 0.85, ds => ds.FillCircle(head, r, colour));
            session2.FillCircle(head, r, colour);
            session2.FillCircle(head, r * 0.45f, Palette.Background[0].Colour);
        }

        return (shown, value);
    }

    /// <summary>
    /// The bull or the bear, riding the head of the curve.
    ///
    /// One line on this page and one head, so the badge sits where the reader's eye already is:
    /// just above the dot the animation has reached. Which animal is not a fact about the slope —
    /// a rolling window would flip it on every wobble — but about the day's own sign: the running
    /// total is a profit (bull) or a loss (bear), the same rule that colours the line, the fill and
    /// the headline. A day that spent the morning in profit and the afternoon in loss changes
    /// animal exactly when the curve crosses zero, which is the one moment this page exists to
    /// show.
    /// </summary>
    private void DrawMascot(
        CanvasDrawingSession session2, FrameContext context, int shown, double p, double value,
        double left, double width, double top, double baseline, double high, double low)
    {
        if (!mascot || shown < 0 || p <= 0)
        {
            return;
        }

        var x = X(session.Samples[shown].Minute, left, width);
        var y = Y(value, top, baseline - top, high, low);

        // Grows in with the curve and bobs on progress alone, so the preview and the export move
        // the badge through exactly the same places.
        var radius = context.Px(MascotRadius) * (0.55 + (0.45 * Math.Min(1, p)));
        var bob = Math.Sin(context.Progress * Math.Tau * 2) * context.Px(4);

        // Kept inside the plot: a head near the top would otherwise push the badge into the
        // header, and one near the right edge would put half of it outside the frame.
        var cx = Math.Clamp(x, left + radius, Math.Max(left + radius, left + width - radius));
        var cy = Math.Max(top + radius + context.Px(6), y - radius - context.Px(14)) + bob;

        Mascots.Draw(
            session2, (float)cx, (float)cy, (float)radius,
            value >= 0, Palette.Emphasis, Palette.Fall, Math.Min(1, p));
    }

    /// <summary>
    /// A dot on the line at every trade, in the side's colour, appearing as the animation reaches
    /// it.
    ///
    /// The trades are placed on the curve in <see cref="IntradayPnl"/> — each one lands on a sample
    /// — so the dot sits on the line rather than beside it, and a trade stamped inside the lunch
    /// break shows at the afternoon's first point, exactly where the curve carries it. Buy is red
    /// and sell is green, the same pairing the broker's own buttons use, so "added here" reads the
    /// way "the line rose here" does.
    /// </summary>
    private void DrawTrades(
        CanvasDrawingSession session2, FrameContext context, int shown,
        double left, double width, double top, double baseline, double high, double low)
    {
        if (shown < 0 || session.Trades.Count == 0)
        {
            return;
        }

        var reached = session.Samples[shown].Minute;

        foreach (var trade in session.Trades)
        {
            if (trade.Minute > reached)
            {
                continue;
            }

            var at = -1;

            for (var i = 0; i <= shown && i < session.Samples.Count; i++)
            {
                if (session.Samples[i].Minute == trade.Minute)
                {
                    at = i;
                    break;
                }
            }

            if (at < 0)
            {
                continue;
            }

            var x = X(trade.Minute, left, width);
            var y = Y(session.Samples[at].Pnl, top, baseline - top, high, low);
            var colour = trade.Side == TradeSide.Buy ? Palette.Emphasis : Palette.Fall;
            var r = (float)context.Px(4);

            Ink.Glow(session2, context.Px(8), 0.9, ds => ds.FillCircle((float)x, (float)y, r, colour));
            session2.FillCircle((float)x, (float)y, r, colour);
            session2.FillCircle((float)x, (float)y, r * 0.45f, Palette.Background[0].Colour);
        }
    }

    /// <summary>One extreme, with its clock and its amount, omitted when the day never left zero.</summary>
    private void Mark(
        CanvasDrawingSession session2, FrameContext context, int minute, double value, int shown,
        double left, double width, double top, double baseline, double high, double low, bool positive)
    {
        if (Math.Abs(value) < 1e-9 || minute < session.OpenMinute)
        {
            return;
        }

        var at = -1;

        for (var i = 0; i <= shown && i < session.Samples.Count; i++)
        {
            if (session.Samples[i].Minute == minute)
            {
                at = i;
                break;
            }
        }

        if (at < 0)
        {
            return;
        }

        var x = (float)X(minute, left, width);
        var y = (float)Y(value, top, baseline - top, high, low);

        session2.FillCircle(x, y, (float)context.Px(5), positive ? Palette.Emphasis : Palette.Fall);

        using var format = Ink.Format(context.Px(19));

        // Above a peak, below a trough, so a label never sits on the curve it describes — and
        // pulled back inside the plot area, because the extremes are by definition at its edges.
        // Left unclamped, the trough's label (the axis pads the trough by 12%, so it lands near
        // the bottom) fell below the baseline and printed on top of the 09:30 clock label.
        var labelY = positive
            ? Math.Max(top + context.Px(22), y - context.Px(20))
            : Math.Min(baseline - context.Px(8), y + context.Px(30));

        // And pulled inward horizontally for the same reason: an extreme is usually at one end of
        // the axis, and a label centred on it prints half outside the plot — over the axis numbers
        // on the left, or off the frame's edge on the right.
        var text = Money(value);

        using var measured = new CanvasTextLayout(session2, text, format, 0, 0);
        var half = measured.LayoutBounds.Width / 2;
        var labelX = Math.Clamp(x, left + half + context.Px(4), left + width - half - context.Px(4));

        Ink.Centred(session2, text, labelX, labelY, format, positive ? Palette.Emphasis : Palette.Fall, 0.9);
    }

    private void DrawClocks(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double width, double baseline)
    {
        var a = Easing.Ramp(t, 300, 1200);

        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));

        var ticks = new[] { session.OpenMinute, (session.OpenMinute + session.CloseMinute) / 2, session.CloseMinute };
        var y = baseline + context.Px(34);

        foreach (var minute in ticks.Distinct())
        {
            var x = X(minute, left, width);

            Ink.Centred(session2, PortfolioSession.Clock(minute), x, y, format, Palette.DateLabel, a);
        }
    }

    /// <summary>
    /// A note under the axis when the total had to cross a currency, and a note when part of the
    /// book was shut. Both are things the frame would otherwise be quietly wrong about.
    /// </summary>
    private void DrawRateNote(
        CanvasDrawingSession session2, FrameContext context, double t, double left, double width, double baseline)
    {
        var a = Easing.Ramp(t, 1200, 1200);

        if (a <= 0)
        {
            return;
        }

        var note = session.HkdCny > 0
            ? Strings.Format("PortfolioPnlRateNote", Rate(session.HkdCny))
            : string.Empty;

        if (note.Length == 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(18));

        Ink.Centred(session2, note, left + (width / 2), baseline + context.Px(66), format, Palette.AxisLabel, a * 0.8);
    }

    /// <summary>The four closing cards, arriving with the same beat as every other page's.</summary>
    private void DrawStats(CanvasDrawingSession session2, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var cards = new (string Label, string Value)[]
        {
            (Strings.Get("PortfolioPnlStatReturn"), Percent(session.ReturnPct)),
            (Strings.Get("PortfolioPnlStatValue"), Money(session.Value, signed: false)),
            (Strings.Get("PortfolioPnlStatHigh"), Money(session.Peak)),
            (Strings.Get("PortfolioPnlStatLow"), Money(session.Trough)),
        };

        var left = context.ChartLeft;
        var gap = context.Px(14);
        var cardWidth = (context.CardRowRight() - left - (gap * 3)) / 4;
        var cardHeight = context.Px(132);
        var y = context.CreditLine - context.Px(CardsAboveCredit);

        using var labelFormat = Ink.Format(context.Px(22));
        using var valueFormat = Ink.Format(context.Px(30), bold: true);

        for (var i = 0; i < cards.Length; i++)
        {
            var x = left + (i * (cardWidth + gap));
            var box = new Rect(x, y, cardWidth, cardHeight);
            var radius = (float)context.Px(14);

            session2.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, a));
            session2.DrawRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardStroke, a), (float)context.Px(1.5));

            Ink.Centred(session2, cards[i].Label, x + (cardWidth / 2), y + context.Px(42), labelFormat, Palette.Muted, a);

            var tone = cards[i].Label == Strings.Get("PortfolioPnlStatHigh")
                ? Palette.Emphasis
                : cards[i].Label == Strings.Get("PortfolioPnlStatLow")
                    ? Palette.Fall
                    : Palette.CardValue;

            Ink.Centred(session2, cards[i].Value, x + (cardWidth / 2), y + context.Px(92), valueFormat, tone, a);
        }

        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(
            session2, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    /// <summary>The title block, the day, the clock, and the running figure.</summary>
    private void DrawHeader(
        CanvasDrawingSession session2, FrameContext context, double t, int index, double value)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = ResolvedTitle();

        _title.Draw(session2, context, title, _title.For(session2, title, context, ShowTitle), Palette.Title, a);

        using var small = Ink.Format(context.Px(25));

        Ink.Centred(
            session2,
            Strings.Format("PortfolioPnlSubtitle", session.Day, session.Holdings.Count),
            cx, Row(context, 0.187), small, Palette.Muted, a);

        var trades = session.TradeCount.ToString(CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session2,
                Strings.Format("PortfolioPnlTradesLine", PortfolioSession.Clock(session.LastMinute), trades),
                trades,
                Palette.Muted, Palette.Emphasis,
                small, strong,
                cx, Row(context, 0.214), a);
        }

        if (index < 0)
        {
            return;
        }

        // The clock the frame has reached, which is what "实时" means on a still frame.
        using (var clockFormat = Ink.Format(context.Px(32)))
        {
            Ink.Centred(
                session2, PortfolioSession.Clock(session.Samples[index].Minute),
                cx, Row(context, 0.2533), clockFormat, Palette.Muted, a);
        }

        var colour = value >= 0 ? Palette.Emphasis : Palette.Fall;

        using (var bigFormat = Ink.Format(context.Px(112), bold: true))
        {
            var text = Money(value);

            Ink.Glow(session2, context.Px(13), 0.45 * a, ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, colour));
            Ink.Centred(session2, text, cx, Row(context, 0.327), bigFormat, colour, a);
        }

        // The return so far, measured the same way the headline is: profit over what the book
        // was worth at yesterday's close.
        var pct = session.PrevValue > 0
            ? Percent(session.Samples[index].Pnl / session.PrevValue * 100) + "  ·  "
            : string.Empty;

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(
            session2,
            pct + Strings.Format("PortfolioPnlValueLine", Money(session.Value, signed: false)),
            cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    private void DrawProgress(CanvasDrawingSession session2, FrameContext context, double t)
    {
        var heightPx = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - heightPx);
        var p = Math.Clamp(t / plan.TotalMs, 0, 1);

        session2.FillRectangle(0, y, (float)context.Width, heightPx, Palette.ProgressTrack);

        Ink.FillHorizontal(session2, new Rect(0, y, context.Width * p, heightPx), Palette.ProgressFill, context.Width);
    }

    /// <summary>
    /// An amount in yuan, always signed: `+1,753.00`. The sign is not decoration — on this chart
    /// it is the half of the answer the colour also carries, and a reader who cannot tell red
    /// from green still has to be able to read the number.
    /// </summary>
    public static string Money(double value, bool signed = true)
    {
        var text = Math.Abs(value).ToString("#,##0.00", CultureInfo.InvariantCulture);

        if (!signed)
        {
            return "¥" + text;
        }

        return (value >= 0 ? "+" : "-") + "¥" + text;
    }

    /// <summary>A percentage with a sign, two decimals: what a daily return is read at.</summary>
    public static string Percent(double value) =>
        (value >= 0 ? "+" : "-") + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    /// <summary>A rate to four places, which is how a currency quote is written.</summary>
    private static string Rate(double value) => value.ToString("0.0000", CultureInfo.InvariantCulture);

    /// <summary>A short axis label: grouped thousands, no decimals, sign kept.</summary>
    private static string Short(double value)
    {
        var text = Math.Abs(value).ToString("#,##0", CultureInfo.InvariantCulture);

        return value < 0 ? "-" + text : text;
    }
}
