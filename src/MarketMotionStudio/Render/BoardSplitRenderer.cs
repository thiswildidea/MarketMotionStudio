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
/// One frame, two answers: what the reader's book did today, above, and how the two markets it
/// lives in moved, below — each half of the frame to itself, both on one clock.
///
/// <para>
/// **The halves are a comparison, so they share an axis of time.** The book's curve and the
/// indexes' lines are drawn against the same 09:30-to-close window and grow together, minute for
/// minute, which is the only thing that lets a reader see that the morning's loss turned at the
/// same moment the Hang Seng turned. Drawn on two independent clocks the same two shapes would
/// sit in one frame saying nothing to each other.
/// </para>
///
/// <para>
/// **The window ends at the later of the two closes.** With a Hong Kong index selected the frame
/// runs to 16:00, and the mainland indexes stop at 15:00 where they stop trading: the line goes
/// flat and a rule marks the minute, because a mainland index drawn to 16:00 as a flat line with
/// no explanation reads as an index that stopped moving rather than as a market that closed.
/// </para>
///
/// <para>
/// **Percentages, not levels.** 恒生 at 23,094 and 上证 at 3,681 cannot share a vertical axis;
/// every index here is plotted as its change against yesterday's close, which is the quantity
/// the two markets do share. The upper half is already a change (yuan of profit), so the two
/// halves speak the same language as well as keeping the same clock.
/// </para>
/// </summary>
public sealed class BoardSplitRenderer(
    PortfolioSession session,
    IReadOnlyList<IndexIntradaySeries> indexes,
    AnimationPlan plan) : IFrameRenderer
{
    // The frame, in fractions of its height, so the layout survives every format. Two panels of
    // equal weight: the book's plot and the indexes' plot are within a few per cent of the same
    // height, because neither half is decoration for the other.
    private const double PnlLabelRow = 0.238;
    private const double PnlTop = 0.262;
    private const double PnlBottom = 0.468;
    private const double ValueRow = 0.548;
    private const double StatRow = 0.590;
    private const double DividerRow = 0.619;
    private const double IndexLabelRow = 0.651;
    private const double IndexTop = 0.675;
    private const double IndexBottom = 0.856;
    private const double ClockRow = 0.888;

    /// <summary>Room the legend column takes off the right of the lower plot, in baseline pixels.</summary>
    private const double LegendWidth = 292;

    private const double LegendPitch = 40;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all.</summary>
    public bool ShowTitle { get; set; } = true;

    private readonly TitleBlock _title = new(58);

    private int _titleLines;

    private double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, _titleLines);

    private string ResolvedTitle() =>
        Title.Length > 0 ? Title : Strings.Get("BoardTitle");

    /// <summary>
    /// Which minute the picture has reached at this progress — the same ramp the rest of the app
    /// uses, so a scrub bar stops where its frame stops.
    /// </summary>
    public int ShownIndex(double progress)
    {
        var p = Easing.Ramp(
            progress * plan.TotalMs, plan.IntroMs,
            Math.Max(1, plan.FinaleStartMs - plan.IntroMs));

        return ShownAt(p);
    }

    private int ShownAt(double p)
    {
        var last = session.Samples.Count - 1;

        return last < 1 ? -1 : Math.Min(last, (int)Math.Floor(p * last));
    }

    /// <summary>
    /// The minute the frame's axis ends: the later of the selected venues' closes. With no index
    /// selected the book's own session decides, which is what the page shows before the first
    /// fetch of a board.
    /// </summary>
    private int WindowClose()
    {
        if (indexes.Count == 0)
        {
            return Math.Max(session.CloseMinute, IntradayPnl.MainlandClose);
        }

        return indexes.Max(s => s.CloseMinute);
    }

    private bool AnyMainland => indexes.Any(s => !s.IsHongKong);

    private int WindowOpen() => IntradayPnl.OpenMinute;

    private double X(double minute, double left, double width)
    {
        var span = Math.Max(1, WindowClose() - WindowOpen());

        return left + (Math.Clamp(minute - WindowOpen(), 0, span) / (double)span * width);
    }

    public void Draw(CanvasDrawingSession session2, FrameContext context)
    {
        var t = context.Progress * plan.TotalMs;

        _titleLines = _title.For(session2, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session2, context, Palette.Background);

        var left = context.ChartLeft;

        // The same rail rule as every other page: the host's avatar strip is wider than the
        // default right margin, so a plot measured to the margin alone runs under it.
        var right = Math.Min(context.ChartRight, context.SafeRight());

        var width = Math.Max(1, right - left);

        var p = Easing.Ramp(t, plan.IntroMs, Math.Max(1, plan.FinaleStartMs - plan.IntroMs));
        var shown = ShownAt(p);

        // The clock the whole frame runs on is the window, not the book's own last print: with a
        // Hong Kong index selected the axis reaches 16:00, and the book — closed at three — is
        // held flat across the last hour exactly the way its line in the lower half is. Mapping
        // the ramp onto the book's minutes instead would stop every line at 15:00 and leave the
        // right fifth of the lower half permanently empty (实测：恒指线画到 15:00 戛然而止).
        var clock = WindowOpen() + (p * (WindowClose() - WindowOpen()));

        DrawPnlPanel(session2, context, t, left, width, shown, clock);
        DrawDivider(session2, context, left, width);
        DrawIndexPanel(session2, context, t, left, width, shown, clock);
        DrawProgress(session2, context, t);
    }

    // ---- upper half: the book ---------------------------------------------------------

    private void DrawPnlPanel(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double width, int shown, double clock)
    {
        var top = Row(context, PnlTop);
        var bottom = Row(context, PnlBottom);

        using var labelFormat = Ink.Format(context.Px(24), bold: true);
        using var noteFormat = Ink.Format(context.Px(19));

        var appear = Easing.Ramp(t, plan.IntroMs * 0.4, 900);

        Ink.Left(session2, Strings.Get("BoardPnlLabel"), left, Row(context, PnlLabelRow),
            labelFormat, Palette.StockPanelTitle, appear);

        var (high, low) = Range();

        // The zero line is this panel's subject — the moment the morning's gain became the
        // afternoon's loss is what a reader of a day's book is looking for.
        var zero = Y(0, top, bottom - top, high, low);

        session2.DrawLine(
            (float)left, (float)zero, (float)(left + width), (float)zero,
            Ink.Fade(Palette.Grid, 0.85 * appear), 1.5f);

        if (appear <= 0 || shown < 0)
        {
            return;
        }

        var points = Curve(left, width, top, bottom - top, high, low, shown, clock);

        FillSigned(session2, points, (float)zero);
        Stroke(session2, points, here: shown);

        // The frame's own read-out: what the book was worth at this minute, said in figures.
        var value = session.Samples[shown].Pnl;
        var positive = value >= 0;

        using var valueFormat = Ink.Format(context.Px(76), bold: true);

        Ink.Centred(session2, PortfolioPnlRenderer.Money(value), context.Width / 2,
            Row(context, ValueRow), valueFormat,
            positive ? Palette.Emphasis : Palette.Fall, appear);

        var pct = session.PrevValue > 0 ? value / session.PrevValue * 100 : 0;

        Ink.Centred(session2, Strings.Format(
                "BoardPnlStatLine",
                Signed(pct),
                session.OpenPositions.ToString(CultureInfo.InvariantCulture)),
            context.Width / 2, Row(context, StatRow), noteFormat, Palette.Muted, appear);

        // Which position is doing the day's work, and which is undoing it. Two names, not a
        // table: at this height a table would be four rows of eight-pixel type, and the reader
        // who wants the table has the page's own list beside the frame.
        if (Contributions(shown) is var (best, worst) && best is not null && worst is not null)
        {
            Ink.Left(session2,
                Strings.Format("BoardContribBest", best.Value.Name, PortfolioPnlRenderer.Money(best.Value.Money)),
                left, Row(context, StatRow) + context.Px(34), noteFormat,
                best.Value.Money >= 0 ? Palette.Emphasis : Palette.Fall, appear * 0.9);

            Ink.RightMiddle(session2,
                Strings.Format("BoardContribWorst", worst.Value.Name, PortfolioPnlRenderer.Money(worst.Value.Money)),
                left + width, Row(context, StatRow) + context.Px(34) - context.Px(7), noteFormat,
                worst.Value.Money >= 0 ? Palette.Emphasis : Palette.Fall, appear * 0.9);
        }
    }

    /// <summary>
    /// The panel's vertical range: the day's larger excursion on either side of zero, padded so
    /// the curve never touches the frame. Zero is always inside it — the distance from zero is
    /// the number being drawn.
    /// </summary>
    private (double High, double Low) Range()
    {
        var high = Math.Max(0, session.Peak);
        var low = Math.Min(0, session.Trough);

        if (high - low < 1e-9)
        {
            return (1, -1);
        }

        return (high > 0 ? high * 1.12 : 0, low < 0 ? low * 1.12 : 0);
    }

    private static double Y(double value, double top, double height, double high, double low) =>
        top + ((high - value) / (high - low) * height);

    /// <summary>
    /// The curve to the minute being drawn, in device coordinates. The last point is interpolated
    /// inside its minute, so the head of the line advances smoothly instead of stepping 242 times.
    /// </summary>
    private List<(float X, float Y, double Value)> Curve(
        double left, double width, double top, double height, double high, double low,
        int shown, double clock)
    {
        var points = new List<(float, float, double)>(shown + 2);

        for (var i = 0; i <= shown && i < session.Samples.Count; i++)
        {
            var sample = session.Samples[i];

            points.Add((
                (float)X(sample.Minute, left, width),
                (float)Y(sample.Pnl, top, height, high, low),
                sample.Pnl));
        }

        if (points.Count == 0)
        {
            return points;
        }

        // The book's own last print: past it the line holds its level, the way a closed market's
        // line does in the lower half. A mainland book under a 16:00 axis is the case this exists
        // for; a book that itself reached 16:00 is untouched by it.
        var printed = session.Samples[Math.Min(shown, session.Samples.Count - 1)];

        if (clock > printed.Minute)
        {
            points.Add(((float)X(clock, left, width), points[^1].Item2, printed.Pnl));
        }
        else if (shown + 1 < session.Samples.Count)
        {
            // Between two prints: the head advances inside its own minute.
            var a = session.Samples[shown];
            var b = session.Samples[shown + 1];
            var frac = Math.Clamp((clock - a.Minute) / (double)Math.Max(1, b.Minute - a.Minute), 0, 1);
            var value = a.Pnl + ((b.Pnl - a.Pnl) * frac);
            var minute = a.Minute + ((b.Minute - a.Minute) * frac);

            points.Add(((float)X(minute, left, width),
                (float)Y(value, top, height, high, low), value));
        }

        return points;
    }

    /// <summary>
    /// Fills the area between the curve and zero, in the colour of the sign it is on.
    ///
    /// Per segment rather than as one polygon, because a day crosses zero and a single fill would
    /// have to pick one colour for both sides — the one thing this panel exists to show. A
    /// segment that crosses is split where it crosses.
    /// </summary>
    private static void FillSigned(
        CanvasDrawingSession session2, List<(float X, float Y, double Value)> points, float zero)
    {
        for (var i = 1; i < points.Count; i++)
        {
            var a = points[i - 1];
            var b = points[i];

            if (a.Value >= 0 && b.Value >= 0)
            {
                Quad(session2, a.X, a.Y, b.X, b.Y, zero, Palette.Emphasis);
            }
            else if (a.Value <= 0 && b.Value <= 0)
            {
                Quad(session2, a.X, a.Y, b.X, b.Y, zero, Palette.Fall);
            }
            else
            {
                // Where the line crosses: the crossing's x is where the value would be zero.
                var t = a.Value / (a.Value - b.Value);
                var crossX = a.X + ((b.X - a.X) * (float)t);

                if (a.Value >= 0)
                {
                    Quad(session2, a.X, a.Y, crossX, zero, zero, Palette.Emphasis);
                    Quad(session2, crossX, zero, b.X, b.Y, zero, Palette.Fall);
                }
                else
                {
                    Quad(session2, a.X, a.Y, crossX, zero, zero, Palette.Fall);
                    Quad(session2, crossX, zero, b.X, b.Y, zero, Palette.Emphasis);
                }
            }
        }
    }

    private static void Quad(
        CanvasDrawingSession session2, float x0, float y0, float x1, float y1, float zero, Color colour)
    {
        if (Math.Abs(x0 - x1) < 0.01f)
        {
            return;
        }

        using var path = new CanvasPathBuilder(session2);

        path.BeginFigure(x0, zero);
        path.AddLine(x0, y0);
        path.AddLine(x1, y1);
        path.AddLine(x1, zero);
        path.EndFigure(CanvasFigureLoop.Closed);

        using var geometry = CanvasGeometry.CreatePath(path);

        session2.FillGeometry(geometry, Ink.Fade(colour, 0.16));
    }

    private static void Stroke(
        CanvasDrawingSession session2, List<(float X, float Y, double Value)> points, int here)
    {
        for (var i = 1; i < points.Count; i++)
        {
            var a = points[i - 1];
            var b = points[i];
            var colour = (a.Value + b.Value) / 2 >= 0 ? Palette.Emphasis : Palette.Fall;

            session2.DrawLine(a.X, a.Y, b.X, b.Y, colour, 3.4f);
        }

        if (points.Count == 0)
        {
            return;
        }

        // The head: a dot that says where "now" is on the day.
        var last = points[^1];

        session2.FillCircle(last.X, last.Y, 7f, Color.FromArgb(255, 255, 255, 255));
        session2.FillCircle(last.X, last.Y, 4.5f, last.Value >= 0 ? Palette.Emphasis : Palette.Fall);
    }

    /// <summary>
    /// The best and worst contributors at the minute on screen, or nothing when the session has
    /// no per-minute breakdown to read.
    /// </summary>
    private ((string Name, double Money)? Best, (string Name, double Money)? Worst)? Contributions(int shown)
    {
        if (shown < 0 || session.Moments.Count == 0)
        {
            return null;
        }

        var moment = session.Moments[Math.Min(shown, session.Moments.Count - 1)];

        (string Name, double Money)? best = null;
        (string Name, double Money)? worst = null;

        foreach (var holding in session.Holdings)
        {
            if (!moment.Contributions.TryGetValue(holding.Code, out var money) || holding.Shares <= 0)
            {
                continue;
            }

            var name = InstrumentNames.Display(holding.Code, holding.Name);

            if (best is null || money > best.Value.Money)
            {
                best = (name, money);
            }

            if (worst is null || money < worst.Value.Money)
            {
                worst = (name, money);
            }
        }

        return (best, worst);
    }

    private void DrawDivider(CanvasDrawingSession session2, FrameContext context, double left, double width)
    {
        var y = Row(context, DividerRow);

        session2.DrawLine((float)left, (float)y, (float)(left + width), (float)y,
            Ink.Fade(Palette.Grid, 0.9), 1);
    }

    // ---- lower half: the two markets ---------------------------------------------------

    private void DrawIndexPanel(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double width, int shown, double clock)
    {
        var top = Row(context, IndexTop);
        var bottom = Row(context, IndexBottom);

        using var labelFormat = Ink.Format(context.Px(24), bold: true);
        using var tickFormat = Ink.Format(context.Px(19));
        using var legendFormat = Ink.Format(context.Px(20));

        var appear = Easing.Ramp(t, plan.IntroMs * 0.4, 900);

        Ink.Left(session2, Strings.Get("BoardIndexLabel"), left, Row(context, IndexLabelRow),
            labelFormat, Palette.StockPanelTitle, appear);

        if (indexes.Count == 0 || appear <= 0)
        {
            Ink.Left(session2, Strings.Get("BoardNoIndex"), left, top + context.Px(40),
                tickFormat, Palette.Muted, appear);

            return;
        }

        var plotRight = left + width - context.Px(LegendWidth);
        var plotWidth = Math.Max(1, plotRight - left);

        var (high, low) = IndexRange();
        var zero = Y(0, top, bottom - top, high, low);

        DrawBands(session2, context, left, plotWidth, top, bottom, appear);

        session2.DrawLine(
            (float)left, (float)zero, (float)plotRight, (float)zero,
            Ink.Fade(Palette.Grid, 0.9 * appear), 1.5f);

        foreach (var series in indexes)
        {
            DrawIndex(session2, context, series, left, plotWidth, top, bottom - top, high, low, clock);
        }

        DrawCloseRule(session2, context, left, plotWidth, top, bottom, appear);
        DrawClocks(session2, context, left, plotWidth, bottom, tickFormat, appear);

        DrawLegend(session2, context, indexes, plotRight + context.Px(24), top, legendFormat, clock, appear);
    }

    /// <summary>
    /// The vertical range of the lower panel: symmetric about the zero line, because an axis
    /// where a one-per-cent fall takes a tenth of the height and a one-per-cent rise takes a
    /// third makes the two directions look like different things.
    /// </summary>
    private (double High, double Low) IndexRange()
    {
        var reach = 0d;

        foreach (var series in indexes)
        {
            foreach (var minute in series.Minutes)
            {
                reach = Math.Max(reach, Math.Abs(series.ChangeAt(minute)));
            }
        }

        reach = Math.Max(reach, 0.15);

        return (reach * 1.12, -(reach * 1.12));
    }

    /// <summary>
    /// The lunch break and the mainland's close, as bands and a rule rather than as flat stretches
    /// the reader has to interpret. Hong Kong breaks an hour later than Shanghai, so the shaded
    /// band is the one they share — 11:30 to 13:00 — and the half hour either side of noon is
    /// named as what it is: the mainland's pause, or Hong Kong's.
    /// </summary>
    private void DrawBands(
        CanvasDrawingSession session2, FrameContext context,
        double left, double width, double top, double bottom, double appear)
    {
        // The band is whichever pause the drawn venues keep: Hong Kong stops at noon, the
        // mainland at half past eleven, and both are back at one.
        var lunchStart = AnyMainland ? IntradayPnl.MainlandLunch : IntradayPnl.KongLunch;
        var from = X(lunchStart, left, width);
        var to = X(IntradayPnl.AfternoonOpen, left, width);

        if (to <= from)
        {
            return;
        }

        session2.FillRectangle(
            (float)from, (float)top, (float)(to - from), (float)(bottom - top),
            Ink.Fade(Palette.Grid, 0.5 * appear));

        using var format = Ink.Format(context.Px(17));

        Ink.Centred(session2, Strings.Get("BoardNoon"), (from + to) / 2, top + context.Px(24),
            format, Palette.AxisLabel, 0.75 * appear);
    }

    private void DrawIndex(
        CanvasDrawingSession session2, FrameContext context, IndexIntradaySeries series,
        double left, double width, double top, double height, double high, double low, double clock)
    {
        var colour = Palette.Race16[Palette.RaceIndex(series.Code)];
        var stop = Math.Min(clock, series.CloseMinute);

        var points = new List<Vector2>();

        foreach (var minute in series.Minutes)
        {
            if (minute.Minute > stop)
            {
                break;
            }

            points.Add(new Vector2(
                (float)X(minute.Minute, left, width),
                (float)Y(series.ChangeAt(minute), top, height, high, low)));
        }

        if (points.Count < 2)
        {
            return;
        }

        // A venue that has closed while the frame's clock runs on: the line holds its last level
        // out to the end of the axis, which is what a closed market does.
        if (stop >= series.CloseMinute && clock > series.CloseMinute)
        {
            points.Add(new Vector2(
                (float)X(clock, left, width),
                points[^1].Y));
        }

        for (var i = 1; i < points.Count; i++)
        {
            session2.DrawLine(points[i - 1], points[i], colour, 3f);
        }

        session2.FillCircle(points[^1], 6f, colour);
    }

    /// <summary>The rule at 15:00, drawn only when the axis actually runs past it.</summary>
    private void DrawCloseRule(
        CanvasDrawingSession session2, FrameContext context,
        double left, double width, double top, double bottom, double appear)
    {
        if (!AnyMainland || WindowClose() <= IntradayPnl.MainlandClose)
        {
            return;
        }

        var x = X(IntradayPnl.MainlandClose, left, width);

        session2.DrawLine(
            (float)x, (float)top, (float)x, (float)bottom,
            Ink.Fade(Palette.Muted, 0.75 * appear), 1.5f);

        using var format = Ink.Format(context.Px(17));

        Ink.RightMiddle(session2, Strings.Get("BoardMainlandClose"), x - context.Px(10),
            top + context.Px(26), format, Palette.Muted, 0.9 * appear);
    }

    private void DrawClocks(
        CanvasDrawingSession session2, FrameContext context,
        double left, double width, double bottom, CanvasTextFormat format, double appear)
    {
        var y = Row(context, ClockRow);

        // With the axis running to 16:00 the 15:00 label is left off: the close rule names that
        // minute already, and two labels fifty pixels apart print over each other (实测：
        // "15:00" 与 "16:00" 连成一串). Without a mainland index there is no rule, and the
        // three o'clock label is dropped with it — the axis still reads, and the reader who
        // wants the exact minute has the legend's own clock in the frame's header.
        var ticks = WindowClose() > IntradayPnl.MainlandClose
            ? new[] { IntradayPnl.OpenMinute, IntradayPnl.AfternoonOpen, IntradayPnl.HongKongClose }
            : new[] { IntradayPnl.OpenMinute, IntradayPnl.MainlandLunch, IntradayPnl.AfternoonOpen,
                      IntradayPnl.MainlandClose };

        foreach (var minute in ticks)
        {
            var x = X(minute, left, width);

            // The last label's centre would hang past the plot's edge; it is pulled inside so the
            // axis does not end in a number half outside the frame.
            var half = context.Px(28);

            Ink.Centred(session2, PortfolioSession.Clock(minute),
                Math.Clamp(x, left + half, left + width - half), y, format,
                Palette.DateLabel, appear);
        }
    }

    /// <summary>
    /// The legend: one row per index, a dot in the line's colour, the name, and the change at the
    /// minute on screen. Right of the plot rather than across its top, because a row of names
    /// above the plot would push the plot down into the clock labels.
    /// </summary>
    private void DrawLegend(
        CanvasDrawingSession session2, FrameContext context, IReadOnlyList<IndexIntradaySeries> list,
        double x, double top, CanvasTextFormat format, double clock, double appear)
    {
        for (var i = 0; i < list.Count; i++)
        {
            var series = list[i];
            var colour = Palette.Race16[Palette.RaceIndex(series.Code)];
            var y = top + context.Px(6) + (i * context.Px(LegendPitch));
            var stop = Math.Min(clock, series.CloseMinute);
            var sample = series.Minutes.LastOrDefault(m => m.Minute <= stop) ?? series.Last;
            var change = series.ChangeAt(sample);

            session2.FillCircle((float)(x + context.Px(6)), (float)(y + context.Px(7)),
                (float)context.Px(6), Ink.Fade(colour, appear));

            var name = series.Name.Length > 6 ? series.Name[..6] : series.Name;

            Ink.Left(session2, name, x + context.Px(22), y + context.Px(14), format,
                Palette.AxisLabel, appear);

            Ink.Left(session2, Signed(change), x + context.Px(22), y + context.Px(14) + context.Px(24),
                format, change >= 0 ? Palette.Emphasis : Palette.Fall, appear);
        }
    }

    private void DrawProgress(CanvasDrawingSession session2, FrameContext context, double t)
    {
        var heightPx = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - heightPx);
        var p = Math.Clamp(t / plan.TotalMs, 0, 1);

        session2.FillRectangle(0, y, (float)context.Width, heightPx, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session2, new Rect(0, y, context.Width * p, heightPx), Palette.ProgressFill, context.Width);
    }

    private static string Signed(double value) =>
        (value >= 0 ? "+" : string.Empty)
        + value.ToString("0.00", CultureInfo.InvariantCulture) + "%";
}
