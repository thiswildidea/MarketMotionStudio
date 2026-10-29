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
/// One frame, two answers: what the reader's book did today, and how the two markets it lives in
/// moved — each half of the frame to itself, both on one clock.
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
/// **The two curves are the same width — and the frame's whole width.** The halves are compared
/// by eye, and a plot that runs wider than the one under it invites the reader to line a feature
/// of one against a different minute of the other; both run edge to edge of the same margins.
/// The legend pays for that: it rides the indexes' own label row, at its right end, instead of
/// claiming a column the curves would both have to give up.
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
/// <param name="crossSafeRight">
/// Whether the picture may run into the band the host covers with its button rail — the same
/// switch the intraday page carries, read once at construction as every other renderer reads it.
/// </param>
/// <param name="mascot">Whether the head of the book's curve carries a bull or a bear.</param>
/// <param name="dynamicAxis">
/// Whether the book's vertical axis follows the curve drawn so far instead of being fixed at the
/// whole day's excursion from the first frame.
/// </param>
/// <param name="lunchBreak">
/// Whether the midday pause is on the axis at all. On, it is a shaded stretch of the clock — and
/// only the minutes *both* drawn venues keep: mainland stops at 11:30, Hong Kong at noon, and
/// with both on the frame the shared pause is 12:00 to 13:00, because 11:30-to-noon Hong Kong
/// still traded. Off, the pause comes off the axis altogether and morning and afternoon meet
/// where the market shut.
/// </param>
/// <param name="indexOnTop">Whether the indexes take the upper half and the book the lower.</param>
/// <param name="maskNames">
/// Whether the contributor lines hide the stocks' names behind asterisks — a published video
/// says more about a holding than its owner may mean to.
/// </param>
public sealed class BoardSplitRenderer(
    PortfolioSession session,
    IReadOnlyList<IndexIntradaySeries> indexes,
    AnimationPlan plan,
    bool crossSafeRight = false,
    bool mascot = false,
    bool dynamicAxis = false,
    bool lunchBreak = true,
    bool indexOnTop = false,
    bool maskNames = false) : IFrameRenderer
{
    // The frame, in fractions of its height. Two slots of near-equal weight, and the halves swap
    // between them: the book's panel and the indexes' panel each take a slot's label row, plot
    // and the strip under the plot, whichever order the reader asked for. The band between the
    // slots carries the shared clock axis — rule plus tick labels — and, when the book is the
    // upper panel, its two contributor lines squeezed in just under the book's own plot.
    private const double TopLabelRow = 0.238;
    private const double TopTop = 0.262;
    private const double TopBottom = 0.504;

    private const double BottomLabelRow = 0.618;
    private const double BottomTop = 0.642;
    private const double BottomBottom = 0.858;

    /// <summary>The room the default layout already leaves between the stack's last slot
    /// edge and the credit line, in baseline pixels: the bottom rail of <see cref="Row"/>
    /// rides this far above <see cref="FrameContext.CreditLine"/> at every margin, which is
    /// what makes the default margins draw exactly the fractions above.</summary>
    private const double CreditLineReserve = (0.87 - BottomBottom) * VideoFormat.BaselineHeight;

    /// <summary>The shared clock axis, drawn between the two panels in either order: a rule
    /// across the plot with the tick labels just under it. The old divider lived on this row;
    /// an axis that names the scale is a better tenant than a bare line.</summary>
    private const double ClockRuleRow = 0.566;

    /// <summary>The book's contributor lines when the book is the upper panel: tucked just
    /// under their own plot so the axis rule keeps the row below.</summary>
    private const double BookContribRow = 0.526;

    /// <summary>From a slot's bottom edge to the row that follows it: a clock axis, or the
    /// contributor lines.</summary>
    private const double RowGap = 0.032;

    /// <summary>From the best contributor's row to the worst's. Two lines, not one: the old
    /// single line set the best from the left and the worst from the right, and the two met in
    /// the middle once names went long — masked or not (实测：两串在中点压在一起).</summary>
    private const double ContribPitch = 0.028;

    /// <summary>Radius of the bull/bear badge, in baseline pixels.</summary>
    private const double MascotRadius = 30;

    /// <summary>The title, already resolved: the user's text, or the default.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>Whether the title row is drawn at all.</summary>
    public bool ShowTitle { get; set; } = true;

    private readonly TitleBlock _title = new(58);

    private int _titleLines;

    /// <summary>The indexes this frame draws: the reader's picks, kept only where their venue
    /// is one the book itself traded. An all-mainland book does not carry a Hong Kong index —
    /// the line would walk a market the upper half never touched, and stretch the shared axis
    /// to 16:00 for an hour nothing printed (实测：全 A 股账本下面挂着恒生、轴空跑到 16:00).
    /// Rebuilt at the top of <see cref="Draw"/>; falls back to every pick when the book's
    /// venues match none of them, so a ticked box never buys an empty half.</summary>
    private IReadOnlyList<IndexIntradaySeries> _drawn = [];

    private void ChooseDrawnIndexes()
    {
        var kong = session.Holdings.Any(h => h.Shares > 0 && h.IsHongKong);
        var mainland = session.Holdings.Any(h => h.Shares > 0 && !h.IsHongKong);

        IReadOnlyList<IndexIntradaySeries> picked = mainland && !kong
            ? [.. indexes.Where(s => !IndexIntraday.IsHongKong(s.Code))]
            : kong && !mainland
                ? [.. indexes.Where(s => IndexIntraday.IsHongKong(s.Code))]
                : indexes;

        _drawn = picked.Count > 0 ? picked : indexes;
    }

    /// <summary>
    /// A layout row, in device pixels.
    ///
    /// <para>
    /// The stack's rows are stated as fractions of frame height, and they used to be
    /// multiplied straight out — which made the bottom margin a control that moved a number
    /// and nothing else: every row was anchored to the top of the frame, so dragging the
    /// margin left the picture exactly where it was (实测：下边距滑杆全程无效果). The
    /// contract the other pages keep is that the bottom margin measures to the lowest thing
    /// drawn, and its anchor here is <see cref="FrameContext.CreditLine"/>.
    /// </para>
    /// <para>
    /// The map is a linear remap between two fixed rails: the top rail is where the first
    /// row lands today — still through <see cref="FrameContext.HeaderRow"/>, so the title
    /// block and the top margin keep the behaviour every other page has — and the bottom
    /// rail rides <see cref="CreditLineReserve"/> above the credit line, so it moves with
    /// the bottom margin. Rows between the rails keep their relative positions and
    /// compress or stretch as the margin asks; rows past the bottom rail (the contributor
    /// lines under a book in the lower slot) extrapolate on the same slope, so they move
    /// with their panel and shrink with it rather than hanging at a fixed depth.
    /// </para>
    /// <para>
    /// At the default margins the rails reproduce the tuned fractions exactly — the
    /// reserve is the distance the default layout already left under the stack — so this
    /// changes nothing about the picture users were shown, and only makes the slider mean
    /// what it says.
    /// </para>
    /// </summary>
    private double Row(FrameContext context, double fraction)
    {
        var top = context.HeaderRow(TopLabelRow, _titleLines);
        var bottom = context.CreditLine - context.Px(CreditLineReserve);
        var slope = (bottom - top) / (BottomBottom - TopLabelRow);

        return top + ((fraction - TopLabelRow) * slope);
    }

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

    /// <summary>
    /// The book's last sample at or before the minute on screen — the same rule the indexes
    /// keep (data to the clock, flat after it), so the two halves' heads stay on one vertical.
    ///
    /// <para>
    /// This used to count prints: the head advanced one sample per slice of progress. A mixed
    /// book's morning and afternoon are not evenly spaced on the axis — a shared pause spends
    /// axis width no sample occupies — and across it the counting head jumped ahead of the
    /// clock while the index lines, drawn by the clock, held back (实测：午休里持仓线头跳到
    /// 13:00，三条指数线还停在 11:30).
    /// </para>
    /// </summary>
    private int ShownAt(double clock)
    {
        if (session.Samples.Count < 2)
        {
            return -1;
        }

        for (var i = session.Samples.Count - 1; i >= 0; i--)
        {
            if (session.Samples[i].Minute <= clock)
            {
                return i;
            }
        }

        return 0;
    }

    /// <summary>
    /// The minute the frame's axis ends: the later of the drawn indexes' closes — the picks
    /// kept to the book's own venues (<see cref="ChooseDrawnIndexes"/>), so an all-mainland
    /// book ends at 15:00 however many Hong Kong boxes are ticked. With no index at all the
    /// book's own session decides, which is what the page shows before the first fetch of a
    /// board.
    /// </summary>
    private int WindowClose()
    {
        if (_drawn.Count == 0)
        {
            return Math.Max(session.CloseMinute, IntradayPnl.MainlandClose);
        }

        return _drawn.Max(s => s.CloseMinute);
    }

    private bool AnyMainland => _drawn.Any(s => !s.IsHongKong);

    private bool AnyKong => _drawn.Any(s => s.IsHongKong);

    private int WindowOpen() => IntradayPnl.OpenMinute;

    /// <summary>
    /// Which midday pause is off the axis or shaded: the minutes **both** drawn sides keep.
    /// Mainland stops at 11:30, Hong Kong at noon, and both are back at one — so a frame showing
    /// both venues pauses at 12:00, where Hong Kong joins the mainland, and a frame of one venue
    /// pauses where that venue stops. The book itself counts: a frame whose indexes are all
    /// mainland still shortens to the shared pause when the book holds Hong Kong shares, because
    /// the upper half is on the same axis and the same rule.
    /// </summary>
    private (int From, int To) MiddayPause()
    {
        var bookMainland = session.Holdings.Any(h => h.Shares > 0 && !h.IsHongKong);
        var bookKong = session.Holdings.Any(h => h.Shares > 0 && h.IsHongKong);

        var mainland = AnyMainland || bookMainland;
        var kong = AnyKong || bookKong;

        var from = mainland && kong ? IntradayPnl.KongLunch
            : mainland ? IntradayPnl.MainlandLunch
            : IntradayPnl.KongLunch;

        return (from, IntradayPnl.AfternoonOpen);
    }

    /// <summary>
    /// Minutes since midnight to an x position, on whichever axis is in force.
    ///
    /// <para>
    /// With the pause on the axis, the clock *is* the axis: 09:30 to close laid out evenly, and
    /// the pause is a stretch of it that <see cref="DrawBands"/> shades so a flat stretch reads as
    /// a pause rather than as an hour of nothing happening.
    /// </para>
    ///
    /// <para>
    /// With it off, the pause is not on the axis: the morning and the afternoon each take the
    /// share of the width their own minutes earned, and they meet where the market shut. A minute
    /// inside the pause lands on the seam, which is the afternoon's first point and where the
    /// curve carries it.
    /// </para>
    /// </summary>
    private double X(double minute, double left, double width)
    {
        var open = WindowOpen();
        var close = WindowClose();
        var span = Math.Max(1, close - open);
        var clamped = Math.Clamp(minute, open, close);

        if (lunchBreak)
        {
            return left + ((clamped - open) / (double)span * width);
        }

        var (from, to) = MiddayPause();

        if (from <= open || to >= close)
        {
            return left + ((clamped - open) / (double)span * width);
        }

        // Two piles of minutes meeting at the seam, each taking the share of the width its own
        // minutes earned. A minute inside the pause belongs to neither pile: it sits on the seam,
        // where the morning ends and the afternoon begins — which is also where the curve carries
        // the pause. Extrapolating it backwards with (clamped - to), as this used to, drove every
        // such minute *into the morning*: the head reached noon and then walked left again towards
        // 11:30 before the afternoon's prints resumed, so the clip looked like it rewound and
        // replayed the break (实测：不带午休时播放到 12:00，线头跳回 11:30 重新画一遍).
        var total = span - (to - from);
        var offset = clamped <= from
            ? clamped - open
            : clamped >= to
                ? (from - open) + (clamped - to)
                : from - open;

        return left + (offset / (double)total * width);
    }

    /// <summary>
    /// The minute on screen for a slice of progress — the clock side of <see cref="X"/>.
    ///
    /// <para>
    /// With the pause on the axis the clock rides the whole window, pause included: the pause is
    /// width on the screen, so it is time on the ramp too, and the heads cross it flat. With the
    /// pause off the axis it costs no width — so it must cost no time either, or every head parks
    /// on the seam for the pause's whole slice of the clip and the playback visibly stalls
    /// (实测：不带午休时，动画在 12:00 附近停住约六分之一时长). The ramp therefore runs over
    /// the traded minutes only — morning, then afternoon — stepping over the seam exactly where
    /// <see cref="X"/> compresses it, so position and clock stay on one mapping.
    /// </para>
    /// </summary>
    private double ScreenClock(double p)
    {
        var open = WindowOpen();
        var close = WindowClose();
        var (from, to) = MiddayPause();

        if (lunchBreak || from <= open || to >= close)
        {
            return open + (p * (close - open));
        }

        var traded = close - open - (to - from);
        var minute = open + (p * traded);

        return minute <= from ? minute : to + (minute - from);
    }

    public void Draw(CanvasDrawingSession session2, FrameContext context)
    {
        var t = context.Progress * plan.TotalMs;

        var title = ResolvedTitle();
        var titleShape = _title.For(session2, title, context, ShowTitle);
        _titleLines = titleShape.Lines;

        context.Backdrop.Fill(session2, context, Palette.Background);

        // The headline the other pages draw: measured once above for the rows below, drawn here
        // before the panels take their own rows. The skin and the ink come from the global
        // setting inside TitleBlock itself, so the choice made on the settings page reaches this
        // page's next redraw the same way it reaches every other page.
        _title.Draw(session2, context, title, titleShape, Palette.Title, Easing.Ramp(t, 0, 1000));

        var left = context.ChartLeft;

        // The same rail rule as every other page: the host's avatar strip is wider than the
        // default right margin, so a plot measured to the margin alone runs under it.
        var right = crossSafeRight ? context.ChartRight : Math.Min(context.ChartRight, context.SafeRight());

        var width = Math.Max(1, right - left);

        // **Both halves' curves span the whole run.** The legend rides the indexes' label row
        // instead of claiming a column, so nothing stands between the curves and the margins:
        // two plots of the same width cannot be compared crooked, and comparing them is what
        // this page exists for.
        var plotWidth = width;

        var p = Easing.Ramp(t, plan.IntroMs, Math.Max(1, plan.FinaleStartMs - plan.IntroMs));

        // The clock the whole frame runs on is the window, not the book's own last print: with a
        // Hong Kong index selected the axis reaches 16:00, and the book — closed at three — is
        // held flat across the last hour exactly the way its line in the other half is. Mapping
        // the ramp onto the book's minutes instead would stop every line at 15:00 and leave the
        // right fifth of the lower half permanently empty (实测：恒指线画到 15:00 戛然而止).
        var clock = ScreenClock(p);

        // Which indexes this frame carries — the book's venues decide — and how far the book's
        // own curve has walked, both settled before the panels read them.
        ChooseDrawnIndexes();
        var shown = ShownAt(clock);

        // The two slots, and whichever half sits in each. Swapping moves the whole panel — label
        // row, plot and the strip under it — so each half keeps its own furniture in both orders.
        (double Label, double Top, double Bottom) bookSlot = indexOnTop
            ? (BottomLabelRow, BottomTop, BottomBottom)
            : (TopLabelRow, TopTop, TopBottom);
        (double Label, double Top, double Bottom) indexSlot = indexOnTop
            ? (TopLabelRow, TopTop, TopBottom)
            : (BottomLabelRow, BottomTop, BottomBottom);

        // The clock axis is both halves' shared time scale, so it lives *between* the panels:
        // one rule with its tick labels under it, hung in the band between the two plots in
        // either order. It reads as one axis for the two plots above and below it, and it
        // replaces the old divider — a bare line separating halves is a worse use of the same
        // row than a line that says what the halves are measured in.
        var clockRuleRow = ClockRuleRow;

        // The contributor lines belong to the book. Under a book in the lower slot they keep
        // their place at the frame's foot; under a book in the upper slot they take the band's
        // top, just under their own plot, and leave the axis rule the row below.
        var contribRow = indexOnTop
            ? bookSlot.Bottom + RowGap + 0.002
            : BookContribRow;

        DrawBookPanel(session2, context, t, left, plotWidth, shown, clock, p,
            bookSlot.Label, bookSlot.Top, bookSlot.Bottom, contribRow);
        DrawIndexPanel(session2, context, t, left, plotWidth, clock,
            indexSlot.Label, indexSlot.Top, indexSlot.Bottom, clockRuleRow);
        DrawProgress(session2, context, t);
    }

    // ---- the book's half ---------------------------------------------------------------

    private void DrawBookPanel(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double plotWidth, int shown, double clock, double p,
        double labelRow, double topRow, double bottomRow, double contribRow)
    {
        var top = Row(context, topRow);
        var bottom = Row(context, bottomRow);
        var height = bottom - top;

        // The panel headings read from across a room: set large and heavy, and the book's own
        // heading is inked in the day's sign — red while the book is up, green while it is down —
        // so the heading itself answers "which kind of day is this" before the curve does.
        using var labelFormat = Ink.Format(context.Px(34), bold: true, heavy: true);
        using var noteFormat = Ink.Format(context.Px(27));

        var appear = Easing.Ramp(t, plan.IntroMs * 0.4, 900);

        var pnlNow = shown >= 0 && shown < session.Samples.Count ? session.Samples[shown].Pnl : 0;
        var headingColour = pnlNow > 0 ? Palette.Emphasis : pnlNow < 0 ? Palette.Fall : Palette.StockPanelTitle;

        Ink.Left(session2, Strings.Get("BoardPnlLabel"), left, Row(context, labelRow),
            labelFormat, headingColour, appear);

        var (high, low) = Range(shown);

        // The value axis both plots share a shape: faint rules at each nice step, each with its
        // figure right-aligned just left of the plot. Drawn before the zero line so the zero —
        // this panel's subject — keeps the stronger stroke it already had.
        DrawValueAxis(session2, context, left, plotWidth, top, bottom, high, low, AxisMoney, appear);

        // The zero line is this panel's subject — the moment the morning's gain became the
        // afternoon's loss is what a reader of a day's book is looking for.
        var zero = Y(0, top, height, high, low);

        session2.DrawLine(
            (float)left, (float)zero, (float)(left + plotWidth), (float)zero,
            Ink.Fade(Palette.Grid, 0.85 * appear), 1.5f);

        if (appear <= 0 || shown < 0)
        {
            return;
        }

        var points = Curve(left, plotWidth, top, height, high, low, shown, clock);

        FillSigned(session2, points, (float)zero);
        Stroke(session2, points, here: shown);

        // The day's two extremes, pinned to the curve: the best moment in the red of a gain, the
        // worst in the green of a loss — a peak's figure above its dot, a trough's below it, so
        // each label sits on the side the curve does not fill.
        DrawExtremes(session2, context, left, plotWidth, top, bottom, high, low, shown, appear);

        var value = points.Count > 0 ? points[^1].Value : session.Samples[shown].Pnl;

        // The day's figure rides the end of the curve rather than the middle of the frame: the
        // number is *about* the curve's last point, and a reader's eye is already there.
        DrawEndValue(session2, context, points[^1], left, plotWidth, top, bottom, appear);

        DrawMascot(session2, context, shown, p, value, left, plotWidth, top, height, high, low);

        // Which position is doing the day's work, and which is undoing it. Two lines, one stock
        // each, both hanging from the left: the old arrangement set the best from the left and
        // the worst from the right on a single line, and the two met in the middle once the
        // names went long — masked or not. The names can be masked — a published video says more
        // about a holding than its owner may mean to say — and the lines are set larger than a
        // caption, because they are the only per-stock reading the frame carries now.
        if (Contributions(shown) is var (best, worst) && best is not null && worst is not null)
        {
            Ink.Left(session2,
                Strings.Format("BoardContribBest", Mask(best.Value.Name),
                    PortfolioPnlRenderer.Money(best.Value.Money)),
                left, Row(context, contribRow) + context.Px(9), noteFormat,
                best.Value.Money >= 0 ? Palette.Emphasis : Palette.Fall, appear * 0.9);

            Ink.Left(session2,
                Strings.Format("BoardContribWorst", Mask(worst.Value.Name),
                    PortfolioPnlRenderer.Money(worst.Value.Money)),
                left, Row(context, contribRow + ContribPitch) + context.Px(9), noteFormat,
                worst.Value.Money >= 0 ? Palette.Emphasis : Palette.Fall, appear * 0.9);
        }
    }

    /// <summary>
    /// The day's figure at the curve's head, in a pill of the sign's colour — the index lines'
    /// end tag, carrying the book's money instead. It rides *beside* the moving head, vertically
    /// centred on it: right of the dot while there is room (the curve has not drawn there yet),
    /// and on the dot's left shoulder once the head runs against the plot's right edge — a pill
    /// pressed against the frame's edge is a pill half-read. Clamped inside the plot on both
    /// axes either way.
    /// </summary>
    private void DrawEndValue(
        CanvasDrawingSession session2, FrameContext context,
        (float X, float Y, double Value) head,
        double left, double plotWidth, double top, double bottom, double appear)
    {
        var text = PortfolioPnlRenderer.Money(head.Value);
        var colour = head.Value >= 0 ? Palette.Emphasis : Palette.Fall;

        using var format = Ink.Format(context.Px(48), bold: true);

        using var layout = new CanvasTextLayout(session2, text, format, 0, 0);

        var textWidth = layout.LayoutBounds.Width;
        var textHeight = layout.LayoutBounds.Height;
        var padX = context.Px(22);
        var padY = context.Px(10);
        var boxWidth = textWidth + (padX * 2);
        var boxHeight = textHeight + (padY * 2);

        // Right of the head while the plot has room for it; left of it once the head gets near
        // the plot's right edge. A line stopped early (the mainland close rule) still has axis
        // to its right, so it keeps the pill on the right there.
        var x = head.X + context.Px(16);

        if (x + boxWidth > left + plotWidth - context.Px(6))
        {
            x = head.X - context.Px(16) - boxWidth;
        }

        x = Math.Max(x, left + context.Px(6));

        var y = head.Y - (boxHeight / 2);

        y = Math.Clamp(y, top + context.Px(6), Math.Max(top + context.Px(6), bottom - boxHeight - context.Px(6)));

        session2.FillRoundedRectangle(
            (float)x, (float)y, (float)boxWidth, (float)boxHeight,
            (float)(boxHeight / 2), (float)(boxHeight / 2),
            Ink.Fade(colour, appear));

        session2.DrawText(
            text, (float)(x + padX), (float)(y + padY),
            Ink.Fade(Ink.OnTopOf(colour), appear), format);
    }

    /// <summary>The contributor names, or the same length of asterisks. An instance method, not
    /// a static one: the switch is a primary-constructor parameter, and those may not be read
    /// from static members.</summary>
    private string Mask(string name) => maskNames ? new string('*', name.Length) : name;

    /// <summary>
    /// The book's vertical range: the day's larger excursion on either side of zero, padded so
    /// the curve never touches the frame. Zero is always inside it — the distance from zero is
    /// the number being drawn. With the dynamic axis on, the range is the running extreme of the
    /// points drawn so far, so a violent afternoon is drawn at its own scale instead of being
    /// flattened by a morning that happened to travel further; at the last point the running
    /// extreme is the whole day's, so the closing frame matches the fixed scale.
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
    /// The day's best and worst moments, pinned to the curve they belong to: a red dot and
    /// figure on the largest gain, a green dot and figure on the largest loss. A gain only gets
    /// its mark when there was one (a day that never crossed zero marks nothing red), and the
    /// figure rides the side of the point the fill does not claim — above a peak, below a
    /// trough. Both move as the animation runs: the extremes are of the minutes drawn so far.
    /// </summary>
    private void DrawExtremes(
        CanvasDrawingSession session2, FrameContext context,
        double left, double plotWidth, double top, double bottom,
        double high, double low, int shown, double appear)
    {
        if (appear <= 0 || shown < 0)
        {
            return;
        }

        double best = 0, worst = 0;
        var bestAt = -1;
        var worstAt = -1;

        for (var i = 0; i <= shown && i < session.Samples.Count; i++)
        {
            var v = session.Samples[i].Pnl;

            if (bestAt < 0 || v > best)
            {
                best = v;
                bestAt = i;
            }

            if (worstAt < 0 || v < worst)
            {
                worst = v;
                worstAt = i;
            }
        }

        using var format = Ink.Format(context.Px(20), bold: true);

        if (bestAt >= 0 && best > 0)
        {
            Mark(session2, context, left, plotWidth, top, bottom, high, low,
                session.Samples[bestAt], above: true, Palette.Emphasis, format, appear);
        }

        if (worstAt >= 0 && worst < 0)
        {
            Mark(session2, context, left, plotWidth, top, bottom, high, low,
                session.Samples[worstAt], above: false, Palette.Fall, format, appear);
        }
    }

    /// <summary>One extreme's furniture: a dot on the curve and the moment's figure beside it,
    /// centred on the dot and clamped inside the plot on both axes.</summary>
    private void Mark(
        CanvasDrawingSession session2, FrameContext context,
        double left, double plotWidth, double top, double bottom,
        double high, double low, PnlSample sample, bool above,
        Color colour, CanvasTextFormat format, double appear)
    {
        var text = PortfolioPnlRenderer.Money(sample.Pnl);
        var x = X(sample.Minute, left, plotWidth);
        var y = Y(sample.Pnl, top, bottom - top, high, low);

        session2.FillCircle((float)x, (float)y, (float)context.Px(5), Ink.Fade(colour, appear));

        using var layout = new CanvasTextLayout(session2, text, format, 0, 0);
        var textWidth = layout.LayoutBounds.Width;
        var textHeight = layout.LayoutBounds.Height;

        // DrawText positions by the top-left corner: a peak's figure clears its dot from above,
        // a trough's from below, and both are clamped inside the plot on both axes.
        var textX = Math.Clamp(x - (textWidth / 2), left + context.Px(4), left + plotWidth - textWidth - context.Px(4));
        var textY = above ? y - context.Px(14) - textHeight : y + context.Px(14);

        textY = Math.Clamp(textY, top + context.Px(4), Math.Max(top + context.Px(4), bottom - textHeight - context.Px(4)));

        Ink.Glow(session2, context.Px(8), 0.35 * appear, ds => ds.DrawText(text, (float)textX, (float)textY, colour, format));

        session2.DrawText(text, (float)textX, (float)textY, Ink.Fade(colour, appear), format);
    }

    /// <summary>
    /// The value axis for either half: a faint rule across the plot at each nice step, with the
    /// step's figure right-aligned just left of the plot's start — the axis-label convention
    /// every other page keeps. The zero row is skipped: each half draws its own zero line with
    /// a stronger stroke, and a second rule there would only double the ink.
    /// </summary>
    private void DrawValueAxis(
        CanvasDrawingSession session2, FrameContext context,
        double left, double plotWidth, double top, double bottom,
        double high, double low, Func<double, string> text, double appear)
    {
        var step = NiceStep((high - low) / 4);
        using var format = Ink.Format(context.Px(22));
        var stroke = (float)Math.Max(1, context.Px(1));

        for (var v = Math.Ceiling(low / step) * step; v <= high + 1e-9; v += step)
        {
            if (Math.Abs(v) >= step * 0.25)
            {
                var tickY = Y(v, top, bottom - top, high, low);

                session2.DrawLine(
                    (float)left, (float)tickY, (float)(left + plotWidth), (float)tickY,
                    Ink.Fade(Palette.Grid, 0.4 * appear), stroke);
            }

            Ink.RightMiddle(session2, text(v), left - context.Px(12),
                Y(v, top, bottom - top, high, low), format, Palette.AxisLabel, appear);
        }
    }

    /// <summary>A step a reader rounds to: 1 / 2 / 2.5 / 5 × a power of ten, so the ticks on an
    /// axis read as amounts rather than as the debris of dividing by four.</summary>
    private static double NiceStep(double rough)
    {
        var pow = Math.Pow(10, Math.Floor(Math.Log10(Math.Max(rough, 1e-9))));
        var frac = rough / pow;

        return pow * (frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 2.5 ? 2.5 : frac <= 5 ? 5 : 10);
    }

    /// <summary>The axis form of the book's money: sign kept, magnitude shortened the way the
    /// 定投 page shortens its own axis (万 where the strings have it, K/M where it hasn't).</summary>
    private static string AxisMoney(double value) =>
        value < 0 ? "-" + DcaRenderer.Money(-value) : DcaRenderer.Money(value);

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
        // line does in the other half. A mainland book under a 16:00 axis is the case this exists
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
    /// The bull or the bear, riding the head of the book's curve — the intraday page's badge, on
    /// the same rule: the animal is the day's sign, not the slope's, so it changes exactly when
    /// the curve crosses zero.
    /// </summary>
    private void DrawMascot(
        CanvasDrawingSession session2, FrameContext context, int shown, double p, double value,
        double left, double width, double top, double height, double high, double low)
    {
        if (!mascot || shown < 0 || p <= 0)
        {
            return;
        }

        var x = X(session.Samples[shown].Minute, left, width);
        var y = Y(value, top, height, high, low);

        // Grows in with the curve and bobs on progress alone, so the preview and the export move
        // the badge through exactly the same places.
        var radius = context.Px(MascotRadius) * (0.55 + (0.45 * Math.Min(1, p)));
        var bob = Math.Sin(context.Progress * Math.Tau * 2) * context.Px(4);

        // Kept inside the plot: a head near the top would otherwise push the badge out of the
        // panel, and one near the right edge would put half of it outside the frame.
        var cx = Math.Clamp(x, left + radius, Math.Max(left + radius, left + width - radius));
        var cy = Math.Max(top + radius + context.Px(6), y - radius - context.Px(14)) + bob;

        Mascots.Draw(
            session2, (float)cx, (float)cy, (float)radius,
            value >= 0, Palette.Emphasis, Palette.Fall, Math.Min(1, p));
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

    // ---- the markets' half -------------------------------------------------------------

    private void DrawIndexPanel(
        CanvasDrawingSession session2, FrameContext context, double t,
        double left, double plotWidth, double clock,
        double labelRow, double topRow, double bottomRow, double clockRow)
    {
        var top = Row(context, topRow);
        var bottom = Row(context, bottomRow);

        // Same heading treatment as the book's half: large, heavy, readable from across a room.
        using var labelFormat = Ink.Format(context.Px(34), bold: true, heavy: true);
        using var tickFormat = Ink.Format(context.Px(22));
        using var legendFormat = Ink.Format(context.Px(20));

        var appear = Easing.Ramp(t, plan.IntroMs * 0.4, 900);

        // The heading is inked in the sign of the reference index — the Shanghai composite when
        // it is on the frame, else the first mainland index, else the first of them — red while
        // that index is up and green while it is down. The heading answers "which kind of day is
        // the market having" the same way the book's heading answers it for the portfolio.
        Ink.Left(session2, Strings.Get("BoardIndexLabel"), left, Row(context, labelRow),
            labelFormat, HeadingColour(clock), appear);

        if (_drawn.Count == 0 || appear <= 0)
        {
            Ink.Left(session2, Strings.Get("BoardNoIndex"), left, top + context.Px(40),
                tickFormat, Palette.Muted, appear);

            return;
        }

        var (high, low) = IndexRange();
        var zero = Y(0, top, bottom - top, high, low);

        // Same axis furniture as the book's half: rules and figures at each nice step. Percent
        // ticks carry their sign (+/−) like the legend's changes do, and 0 stays bare.
        var axisStep = NiceStep((high - low) / 4);
        var axisDecimals = axisStep < 0.25 ? 2 : axisStep <= 2.5 ? 1 : 0;

        DrawValueAxis(session2, context, left, plotWidth, top, bottom, high, low, v =>
            Math.Abs(v) < axisStep * 0.25
                ? "0"
                : (v > 0 ? "+" : string.Empty) + v.ToString(
                    "0." + new string('#', axisDecimals), CultureInfo.InvariantCulture) + "%",
            appear);

        DrawBands(session2, context, left, plotWidth, top, bottom, appear);

        session2.DrawLine(
            (float)left, (float)zero, (float)(left + plotWidth), (float)zero,
            Ink.Fade(Palette.Grid, 0.9 * appear), 1.5f);

        // Each line carries its own tag at its end — name and live change on the line's colour.
        // The tags know about each other only as rectangles: two lines that end close together
        // must not print their tags on top of one another.
        var tags = new List<(double Top, double Bottom)>(_drawn.Count);

        foreach (var series in _drawn)
        {
            DrawIndex(session2, context, series, left, plotWidth, top, bottom - top, high, low,
                clock, legendFormat, tags, appear);
        }

        DrawCloseRule(session2, context, left, plotWidth, top, bottom, appear);
        DrawClocks(session2, context, left, plotWidth, clockRow, tickFormat, appear);

        // The legend sits on its own line under the heading: the heading grew to headline size,
        // and with three indexes live the two no longer share a row (实测：图例左端压进标题).
        // The slot's label band is the vertical room between the heading's baseline and the
        // plot's top edge; a drop of 30px parks the legend inside it, clear of both.
        DrawLegend(session2, context, _drawn, left + plotWidth,
            Row(context, labelRow) + context.Px(30), legendFormat, clock, appear);
    }

    /// <summary>
    /// The vertical range of the indexes' panel: symmetric about the zero line, because an axis
    /// where a one-per-cent fall takes a tenth of the height and a one-per-cent rise takes a
    /// third makes the two directions look like different things.
    /// </summary>
    private (double High, double Low) IndexRange()
    {
        var reach = 0d;

        foreach (var series in _drawn)
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
    /// The midday pause, shaded rather than merely skipped over — and only when the pause is on
    /// the axis at all. The band is the minutes **both** drawn venues keep (see
    /// <see cref="MiddayPause"/>): 11:30-to-noon Hong Kong still traded, and shading it would
    /// call traded minutes a break.
    /// </summary>
    private void DrawBands(
        CanvasDrawingSession session2, FrameContext context,
        double left, double width, double top, double bottom, double appear)
    {
        if (!lunchBreak || _drawn.Count == 0)
        {
            return;
        }

        var (fromMinute, toMinute) = MiddayPause();
        var from = X(fromMinute, left, width);
        var to = X(toMinute, left, width);

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

    /// <summary>The index heading's colour: the reference index's change sign — red up, green
    /// down, and the neutral title colour when there is nothing on the frame to read a sign
    /// from.</summary>
    private Color HeadingColour(double clock)
    {
        var reference =
            _drawn.FirstOrDefault(s => s.Code == "sh000001") ??
            _drawn.FirstOrDefault(s => !IndexIntraday.IsHongKong(s.Code)) ??
            _drawn.FirstOrDefault();

        if (reference is null)
        {
            return Palette.StockPanelTitle;
        }

        var stop = Math.Min(clock, reference.CloseMinute);
        var sample = reference.Minutes.LastOrDefault(m => m.Minute <= stop) ?? reference.Last;
        var change = reference.ChangeAt(sample);

        return change > 0 ? Palette.Emphasis : change < 0 ? Palette.Fall : Palette.StockPanelTitle;
    }

    private void DrawIndex(
        CanvasDrawingSession session2, FrameContext context, IndexIntradaySeries series,
        double left, double width, double top, double height, double high, double low, double clock,
        CanvasTextFormat tagFormat, List<(double Top, double Bottom)> tags, double appear)
    {
        var colour = Palette.Race16[Palette.RaceIndex(series.Code)];
        var stop = Math.Min(clock, series.CloseMinute);

        var points = new List<Vector2>();
        var lastDrawn = -1;

        foreach (var minute in series.Minutes)
        {
            if (minute.Minute > stop)
            {
                break;
            }

            points.Add(new Vector2(
                (float)X(minute.Minute, left, width),
                (float)Y(series.ChangeAt(minute), top, height, high, low)));
            lastDrawn = minute.Minute;
        }

        // Past the minute the line was drawn to, the head holds its level out to where the clock
        // has reached — the same convention the book's curve keeps in the other half (see
        // Curve). One rule, three cases: the lunch gap (mainland data stops at 11:30 while Hong
        // Kong trades to noon — the line follows flat instead of freezing there, 实测：持仓走
        // 到 13:00 三条 A 股指数还冻在 11:30), a board fetched mid-session (data ends at the
        // fetch minute), and the line's own close (a mainland index rides the 16:00 axis flat
        // from 15:00, where its market shut but Hong Kong's has not). The old condition
        // compared the clock against the series' *last* print, which none of the first two
        // cases reach — the freeze the screenshot caught.
        if (points.Count > 0 && clock > lastDrawn)
        {
            points.Add(new Vector2(
                (float)X(clock, left, width),
                points[^1].Y));
        }

        if (points.Count < 2)
        {
            return;
        }

        for (var i = 1; i < points.Count; i++)
        {
            session2.DrawLine(points[i - 1], points[i], colour, 3f);
        }

        session2.FillCircle(points[^1], 6f, colour);

        DrawEndTag(session2, context, series, colour, points[^1], stop, left, width,
            top, top + height, tagFormat, tags, appear);
    }

    /// <summary>
    /// The tag riding a line's end: the index's name and its change at the minute on screen, on
    /// a pill of the line's own colour. A legend answers *which line is which*; this answers
    /// *where is it now* — the reader follows the line's head and the number is already there,
    /// not across the frame in a column. The pill sits just left of the head dot (the lines end
    /// at the plot's right edge, so the tag reads backwards into the morning it summarises),
    /// clamped inside the plot, and nudged vertically clear of the tags already placed when two
    /// lines end close together.
    /// </summary>
    private void DrawEndTag(
        CanvasDrawingSession session2, FrameContext context, IndexIntradaySeries series, Color colour,
        Vector2 head, double stop, double left, double width, double top, double bottom,
        CanvasTextFormat format, List<(double Top, double Bottom)> tags, double appear)
    {
        var sample = series.Minutes.LastOrDefault(m => m.Minute <= stop) ?? series.Last;
        var text = $"{series.Name} {Signed(series.ChangeAt(sample))}";

        using var layout = new CanvasTextLayout(session2, text, format, 0, 0);

        var textWidth = layout.LayoutBounds.Width;
        var textHeight = layout.LayoutBounds.Height;
        var padX = context.Px(11);
        var padY = context.Px(5);
        var boxWidth = textWidth + (padX * 2);
        var boxHeight = textHeight + (padY * 2);

        var x = head.X - context.Px(12) - boxWidth;

        if (x < left)
        {
            // A line that stopped early (the mainland close rule) may end near the left; the
            // tag then reads off the dot's right shoulder instead, kept inside the plot.
            x = Math.Min(head.X + context.Px(12), left + width - boxWidth);
        }

        // The nudging searches both directions and takes the nearest free slot, not just the
        // next one down: a line ending among friends (指数 lines crowd the top when the market
        // is only slightly off) used to see its tag walk past every tag below it and land at
        // the plot's foot — where the reader reads the frame's worst number as *its* number
        // (实测：恒生 -0.67% 的标签被挤到最底、挂在跌幅最大的那条线旁).
        var home = head.Y - (boxHeight / 2);
        var gap = boxHeight + context.Px(6);
        var plotFloor = Math.Max(top + context.Px(4), bottom - boxHeight - context.Px(4));

        var y = home;
        var placed = false;

        for (var ring = 0; ring <= 8 && !placed; ring++)
        {
            foreach (var candidate in ring == 0 ? new[] { home } : new[] { home - (ring * gap), home + (ring * gap) })
            {
                var clamped = Math.Clamp(candidate, top + context.Px(4), plotFloor);

                if (!tags.Any(t => clamped < t.Bottom + context.Px(4) && clamped + boxHeight > t.Top - context.Px(4)))
                {
                    y = clamped;
                    placed = true;
                    break;
                }
            }
        }

        // A tag that had to leave its line's side carries a leader back to the head dot, in the
        // line's own colour — the one thread a displaced tag needs to stay read as *this* line's.
        if (Math.Abs(y - home) > gap * 0.5)
        {
            session2.DrawLine(head, new Vector2(
                (float)(x + boxWidth), (float)(y + (boxHeight / 2))), colour, 1.5f);
        }

        tags.Add((y, y + boxHeight));

        session2.FillRoundedRectangle(
            (float)x, (float)y, (float)boxWidth, (float)boxHeight,
            (float)(boxHeight / 2), (float)(boxHeight / 2),
            Ink.Fade(colour, appear));

        session2.DrawText(
            text, (float)(x + padX), (float)(y + padY),
            Ink.Fade(Ink.OnTopOf(colour), appear), format);
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
        double left, double width, double clockRuleRow, CanvasTextFormat format, double appear)
    {
        // The rule is the axis itself — the same faint line the divider used to be, but here
        // it has a job: the ticks under it say what the two plots above and below are measured
        // in. The labels sit one caption's height below the rule, clear of it.
        var ruleY = Row(context, clockRuleRow);

        session2.DrawLine((float)left, (float)ruleY, (float)(left + width), (float)ruleY,
            Ink.Fade(Palette.Grid, 0.9 * appear), 1);

        var y = ruleY + context.Px(30);

        // With the axis running to 16:00 the 15:00 label is left off: the close rule names that
        // minute already, and two labels fifty pixels apart print over each other (实测：
        // "15:00" 与 "16:00" 连成一串). With the pause off the axis, the pause's own label goes
        // with it — 11:30 is not on the axis to be labelled.
        var ticks = WindowClose() > IntradayPnl.MainlandClose
            ? new[] { IntradayPnl.OpenMinute, IntradayPnl.AfternoonOpen, IntradayPnl.HongKongClose }
            : lunchBreak
                ? new[] { IntradayPnl.OpenMinute, IntradayPnl.MainlandLunch, IntradayPnl.AfternoonOpen,
                          IntradayPnl.MainlandClose }
                : new[] { IntradayPnl.OpenMinute, IntradayPnl.AfternoonOpen, IntradayPnl.MainlandClose };

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
    /// The legend: one entry per index — a dot in the line's colour, the name, and the change at
    /// the minute on screen — laid out in a row along the indexes' own label line, right-aligned
    /// to the plot's right edge. It used to sit in a column of its own that *both* plots paid
    /// for; a column is a poor trade when the two curves underneath it exist to be compared, and
    /// a label row has the whole right half of itself to spare.
    /// </summary>
    private void DrawLegend(
        CanvasDrawingSession session2, FrameContext context, IReadOnlyList<IndexIntradaySeries> list,
        double right, double baseline, CanvasTextFormat format, double clock, double appear)
    {
        var entries = new List<(Color Colour, string Name, string Change, double Width)>(list.Count);
        var total = 0d;

        foreach (var series in list)
        {
            var name = series.Name.Length > 6 ? series.Name[..6] : series.Name;
            var stop = Math.Min(clock, series.CloseMinute);
            var sample = series.Minutes.LastOrDefault(m => m.Minute <= stop) ?? series.Last;
            var change = Signed(series.ChangeAt(sample));
            var colour = Palette.Race16[Palette.RaceIndex(series.Code)];

            using var nameLayout = new CanvasTextLayout(session2, name, format, 0, 0);
            using var changeLayout = new CanvasTextLayout(session2, change, format, 0, 0);

            var width = context.Px(6) + context.Px(10) + nameLayout.LayoutBounds.Width
                + context.Px(8) + changeLayout.LayoutBounds.Width;

            entries.Add((colour, name, change, width));
            total += width;
        }

        total += context.Px(30) * Math.Max(0, entries.Count - 1);

        var x = right - total;

        foreach (var entry in entries)
        {
            session2.FillCircle(
                (float)(x + context.Px(6)), (float)(baseline - context.Px(8)),
                (float)context.Px(6), Ink.Fade(entry.Colour, appear));

            Ink.Left(session2, entry.Name, x + context.Px(20), baseline, format,
                Palette.AxisLabel, appear);

            using var nameLayout = new CanvasTextLayout(session2, entry.Name, format, 0, 0);

            Ink.Left(session2, entry.Change,
                x + context.Px(20) + nameLayout.LayoutBounds.Width + context.Px(8), baseline,
                format, entry.Change.StartsWith('+') ? Palette.Emphasis : Palette.Fall, appear);

            x += entry.Width + context.Px(30);
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
