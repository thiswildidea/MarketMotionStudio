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
/// One session, drawn the way a session is lived: turnover accumulating from the opening bell to
/// the close, minute by minute.
///
/// The daily forms say *how much* traded on each of a hundred days. This one says *when* it
/// traded on one of them, which is a different question with a different shape — the heavy
/// opening auction, the thin lunch hour, the rush into the close. A cumulative curve is the only
/// honest way to draw it: it can only ever rise, which is what makes the flat stretches legible.
///
/// <para>
/// The frame is laid out on the same lines as <see cref="TurnoverRenderer"/>, and deliberately so:
/// these are two forms of the same page, and the statistics and the credit must sit where they sat
/// a moment ago when the reader switched. Both plot areas therefore start at
/// <see cref="TurnoverRenderer.PlotTopFraction"/> and end at
/// <see cref="TurnoverRenderer.CreditGap"/> above the credit.
/// </para>
/// </summary>
public sealed class IntradayRenderer(IntradayTurnover series, AnimationPlan plan) : IFrameRenderer
{
    /// <summary>Distance from the credit up to the top of the statistic cards.</summary>
    private const double CardsAboveCredit = 192;

    /// <summary>How many clock labels fit along the bottom without colliding.</summary>
    private const int ClockTicks = 6;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all — see <see cref="TurnoverRenderer.ShowTitle"/>.</summary>
    public bool ShowTitle { get; set; } = true;

    /// <summary>The wrapped headline, in the daily forms' own size.</summary>
    private readonly TitleBlock _title = new(62);

    /// <summary>
    /// How many lines the title took on the frame being drawn — what every row below it is moved
    /// by. Set once at the top of <see cref="Draw"/>.
    /// </summary>
    private int _titleLines;

    /// <summary>A header row, stated as a fraction of frame height and shifted the way every other
    /// indicator's header row is shifted: by the top margin, and by the room the title block
    /// took — up when it is hidden, down when it wraps.
    /// See <see cref="FrameContext.HeaderRow"/>.</summary>
    private double Row(FrameContext context, double fraction) =>
        context.HeaderRow(fraction, _titleLines);

    /// <summary>
    /// The headline this frame draws: what the user typed, or the default naming the session. One
    /// place, because the text measured at the top of <see cref="Draw"/> and the text drawn in the
    /// header have to be the same string.
    /// </summary>
    private string ResolvedTitle() => Title.Length > 0 ? Title : Strings.Get("TurnoverIntradayStageTitle");

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * plan.TotalMs;

        // The line count before the first row is read — the plot's top edge is one of those rows.
        _titleLines = _title.For(session, ResolvedTitle(), context, ShowTitle).Lines;

        context.Backdrop.Fill(session, context, Palette.Background);

        var left = context.ChartLeft;
        var width = context.ChartWidth;
        var baseline = context.BaselineAbove(TurnoverRenderer.CreditGap);
        var top = Row(context, TurnoverRenderer.PlotTopFraction);
        var height = Math.Max(1, baseline - top);

        DrawAxes(session, context, t, left, width, baseline, height);

        var (index, value) = DrawCurve(session, context, t, left, width, baseline, height, top);

        DrawClocks(session, context, t, left, width, baseline);
        DrawStats(session, context, t);
        DrawHeader(session, context, t, index, value);
        DrawProgress(session, context, t);
    }

    /// <summary>Gridlines and their labels, drawing in from the left as they appear.</summary>
    private void DrawAxes(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double height)
    {
        var a = Easing.Ramp(t, 500, 1500);

        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(21));
        var stroke = (float)Math.Max(1, context.Scale);

        for (var v = 0.0; v <= plan.AxisTop + 1e-6; v += plan.AxisStep)
        {
            var y = (float)(baseline - (v / plan.AxisTop * height));

            session.DrawLine(
                new Vector2((float)left, y),
                new Vector2((float)(left + (width * a)), y),
                Ink.Fade(Palette.Grid, a),
                stroke);

            Ink.RightMiddle(session, TurnoverRenderer.Round(v), left - context.Px(12), y,
                format, Palette.AxisLabel, a);
        }
    }

    /// <summary>
    /// The curve up to the minute the animation has reached, and the running total at that minute.
    ///
    /// **The head advances linearly, not on an easing curve.** This animation is a clock: the
    /// minute being drawn at a third of the way through is the minute a third of the way through
    /// the session, and an ease-out would compress the morning into the first seconds and dwell on
    /// the close. The one thing a cumulative curve must not do is appear to slow down, because a
    /// reader takes that as trading having stopped.
    /// </summary>
    private (int Index, double Value) DrawCurve(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline, double height, double top)
    {
        var last = series.Count - 1;

        if (last < 1)
        {
            return (-1, 0);
        }

        var p = Easing.Ramp(t, plan.IntroMs, Math.Max(1, plan.FinaleStartMs - plan.IntroMs));
        var at = p * last;
        var whole = (int)Math.Floor(at);
        var fraction = at - whole;

        var shown = Math.Min(last, whole);
        var value = series.CumulativeYi[shown]
            + ((series.CumulativeYi[Math.Min(last, shown + 1)] - series.CumulativeYi[shown]) * fraction);

        // The axis is scaled to the *whole day*, not to what has been drawn, so the curve grows
        // into a frame that was already the right size. Scaling to the part drawn would make the
        // curve fill the height within seconds and then flatten into it — the shape would be a
        // lie about how much of the day's total has arrived.
        double Y(double amount) => baseline - ((amount / plan.AxisTop) * height);
        double X(int i) => left + (width * i / (double)last);

        var head = new Vector2((float)X(shown), (float)Y(value));

        var shape = new CanvasPathBuilder(session);
        shape.BeginFigure(new Vector2((float)X(0), (float)Y(series.CumulativeYi[0])));

        for (var i = 1; i <= shown; i++)
        {
            shape.AddLine(new Vector2((float)X(i), (float)Y(series.CumulativeYi[i])));
        }

        shape.AddLine(head);
        shape.EndFigure(CanvasFigureLoop.Open);

        using (var line = CanvasGeometry.CreatePath(shape))
        {
            session.DrawGeometry(line, Palette.Moving, (float)context.Px(3.5));
        }

        // The area under the curve, closed back to the baseline. Built as its own path rather than
        // by letting the open one be filled, because filling an open figure closes it with a
        // straight chord from the head to the start — which would paint a triangle across the
        // whole frame instead of the ground the day has covered.
        var area = new CanvasPathBuilder(session);
        area.BeginFigure(new Vector2((float)X(0), (float)baseline));

        for (var i = 0; i <= shown; i++)
        {
            area.AddLine(new Vector2((float)X(i), (float)Y(series.CumulativeYi[i])));
        }

        area.AddLine(new Vector2(head.X, (float)baseline));
        area.EndFigure(CanvasFigureLoop.Closed);

        using (var ground = CanvasGeometry.CreatePath(area))
        using (var wash = new CanvasLinearGradientBrush(
            session,
            [
                new CanvasGradientStop { Position = 0, Color = Ink.Fade(Palette.Moving, 0.40) },
                new CanvasGradientStop { Position = 1, Color = Ink.Fade(Palette.Moving, 0.02) },
            ])
        {
            StartPoint = new Vector2(0, (float)top),
            EndPoint = new Vector2(0, (float)baseline),
        })
        {
            session.FillGeometry(ground, wash);
        }

        // The lunch break, marked on the axis rather than left for the reader to infer from a
        // plateau. A session is two sessions with an hour between them, and the curve's flat
        // stretch is the one feature of it that needs naming.
        var noon = series.IndexAtOrAfter(series.NoonLabel);

        if (noon > 0 && noon <= shown)
        {
            var x = (float)X(noon);

            session.DrawLine(new Vector2(x, (float)top), new Vector2(x, (float)baseline),
                Ink.Fade(Palette.Grid, 1.6), (float)context.Px(1.5));

            using var noonFormat = Ink.Format(context.Px(18));

            Ink.Centred(session, Strings.Get("TurnoverIntradayNoon"), x, (float)top + context.Px(24),
                noonFormat, Palette.AxisLabel, 0.9);
        }

        if (p > 0)
        {
            var r = (float)context.Px(9);

            Ink.Glow(session, context.Px(11), 0.85,
                ds => ds.FillCircle(head, r, Palette.Moving));

            session.FillCircle(head, r, Palette.Moving);
        }

        return (shown, value);
    }

    /// <summary>Clock labels along the bottom, thinned so they never collide.</summary>
    private void DrawClocks(
        CanvasDrawingSession session, FrameContext context, double t,
        double left, double width, double baseline)
    {
        var a = Easing.Ramp(t, 300, 1200);

        if (a <= 0 || series.Count < 2)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));
        var last = series.Count - 1;
        var y = baseline + context.Px(34);

        for (var tick = 0; tick < ClockTicks; tick++)
        {
            var i = (int)Math.Round(last * tick / (double)(ClockTicks - 1));
            var x = left + (width * i / (double)last);

            Ink.Centred(session, series.Labels[i], x, y, format, Palette.DateLabel, a);
        }
    }

    /// <summary>
    /// The four closing cards, arriving with the same beat as the daily forms'.
    ///
    /// Three of them are shares of the day rather than amounts, because on a chart whose whole
    /// subject is *when* money moved, "how much moved before lunch" is the question and "how much
    /// moved" is one the title block has already answered. Amounts would make all four cards
    /// restate the same total and none of them say anything about the shape.
    /// </summary>
    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, plan.FinaleStartMs + 1900, 900);

        if (a <= 0)
        {
            return;
        }

        var cards = new (string Label, string Value)[]
        {
            (Strings.Get("TurnoverIntradayStatTotal"), TurnoverRenderer.Round(series.TotalYi)),
            (Strings.Get("TurnoverIntradayStatMorning"), Percent(series.Share(series.MorningYi))),
            (Strings.Get("TurnoverIntradayStatAfternoon"), Percent(series.Share(series.AfternoonYi))),
            (Strings.Get("TurnoverIntradayStatClose"), Percent(series.Share(series.CloseRunYi))),
        };

        var left = context.ChartLeft;
        var gap = context.Px(14);
        var cardWidth = (context.CardRowRight() - left - (gap * 3)) / 4;
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

            Ink.Centred(session, cards[i].Label, x + (cardWidth / 2), y + context.Px(42), labelFormat, Palette.Muted, a);
            Ink.Centred(session, cards[i].Value, x + (cardWidth / 2), y + context.Px(92), valueFormat, Palette.CardValue, a);
        }

        using var creditFormat = Ink.Format(context.Px(20));

        Ink.Centred(
            session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            creditFormat, Palette.Credit, a * 0.75);
    }

    /// <summary>The title block, the session, the clock, and the running total.</summary>
    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t, int index, double value)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = ResolvedTitle();

        _title.Draw(session, context, title, _title.For(session, title, context, ShowTitle), Palette.Title, a);

        using var small = Ink.Format(context.Px(25));

        // What is being summed, then the unit — the same two facts the daily form's subtitle
        // carries, so switching forms does not change what the frame claims to be measuring.
        Ink.Centred(
            session,
            Strings.Format("TurnoverIntradaySubtitle", series.Name, Strings.Get("TurnoverUnit")),
            cx, Row(context, 0.187), small, Palette.Muted, a);

        var count = series.Count.ToString(CultureInfo.InvariantCulture);

        using (var strong = Ink.Format(context.Px(25), bold: true))
        {
            Ink.Highlighted(
                session,
                Strings.Format("TurnoverIntradayLine", series.Day, count),
                count,
                Palette.Muted, Palette.Emphasis,
                small, strong,
                cx, Row(context, 0.214), a);
        }

        if (index < 0)
        {
            return;
        }

        using (var clockFormat = Ink.Format(context.Px(34)))
        {
            Ink.Centred(session, series.Labels[index], cx, Row(context, 0.2533), clockFormat, Palette.Moving, a);
        }

        using (var bigFormat = Ink.Format(context.Px(128), bold: true))
        {
            var text = TurnoverRenderer.Round(value);

            Ink.Glow(session, context.Px(13), 0.5 * a,
                ds => Ink.Centred(ds, text, cx, Row(context, 0.327), bigFormat, Palette.Moving));

            Ink.Centred(session, text, cx, Row(context, 0.327), bigFormat, Palette.Moving, a);
        }

        using var unitFormat = Ink.Format(context.Px(26));

        Ink.Centred(session, Strings.Get("TurnoverUnit"), cx, Row(context, 0.354), unitFormat, Palette.Muted, a);
    }

    /// <summary>A bar along the bottom edge — see <see cref="TurnoverRenderer"/>'s, which this matches.</summary>
    private void DrawProgress(CanvasDrawingSession session, FrameContext context, double t)
    {
        var heightPx = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - heightPx);
        var p = Math.Clamp(t / plan.TotalMs, 0, 1);

        session.FillRectangle(0, y, (float)context.Width, heightPx, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session, new Rect(0, y, context.Width * p, heightPx), Palette.ProgressFill, context.Width);
    }

    private static string Percent(double value) =>
        value.ToString("0.0", CultureInfo.InvariantCulture) + "%";
}
