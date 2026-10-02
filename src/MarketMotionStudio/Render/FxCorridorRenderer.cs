using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The currency corridor: one row per pair, and on each row the pair's own range — the floor and
/// the ceiling it has actually traded between — with the current rate as a marker somewhere along
/// it.
///
/// The row is not a bar and the value is not an amount. A board of corridors is the one place in
/// this app where **the two ends of a row mean something different from the marker's distance
/// along it**: the ends are where the pair has been, and the marker is where it is. So the row is
/// drawn full width every frame — the corridor is a *place*, not a quantity — and what moves is
/// the marker, together with the walls, which are pushed outwards by any month that goes further
/// than any month before it.
///
/// **The walls expand.** They are the lowest low and the highest high *so far*, not over the whole
/// span. A fixed ruler with a dot sliding along it would measure the span's extremes from the
/// first frame and the picture would be a gauge; an expanding corridor is what makes the picture a
/// record — early on the walls are narrow and the rate fills them, and a month outside them moves
/// one of them. It is also why a pair's marker can sit at 100%: it is at the ceiling because the
/// ceiling is the highest it has ever been, and this month is it.
///
/// **Every pair is measured against itself.** 157.92 on USD/JPY and 1.1245 on EUR/USD are not two
/// points on one scale, and normalising the corridor is what lets six of them stand on one board.
/// The consequence is stated on the frame by the floor and ceiling printed under each row: a
/// narrow corridor and a wide one look alike, and the numbers are what tell them apart.
///
/// Ranking and interpolation work as they do on the race — every month's order is precomputed and
/// a row's vertical place is its two neighbouring months' ranks eased — with one difference: a row
/// is only ranked while it is on the board. A pair the source has no rate for in a month is not
/// a pair at 0%, it is a pair with no position, and ranking it would put a currency that has not
/// been quoted yet above one that has been quoted at its floor.
/// </summary>
public sealed class FxCorridorRenderer : IFrameRenderer
{
    /// <summary>The left gutter's name column, in baseline pixels.</summary>
    private const double GutterLeft = 150;

    /// <summary>The right gutter: the rate and, under it, the position in the corridor.</summary>
    private const double GutterRight = 180;

    /// <summary>Baseline rows between the plot's bottom and the credit.</summary>
    private const double CreditGap = 74;

    private const double HeaderTopFraction = 0.278;

    private readonly FxCorridorSeries _series;

    /// <summary>Position along the corridor, per pair per month; 0 at the floor, 1 at the ceiling.</summary>
    private readonly double[][] _position;

    /// <summary>Whether the pair was quoted in that month at all.</summary>
    private readonly bool[][] _present;

    /// <summary>The per-month ranking among the pairs that are on the board; −1 for the rest.</summary>
    private readonly int[][] _rank;

    /// <summary>The floor and ceiling per pair per month, expanding — see the note on the class.</summary>
    private readonly double[][] _floor;

    private readonly double[][] _ceiling;

    public FxCorridorRenderer(FxCorridorSeries series, TimeSpan duration)
    {
        _series = series;
        Duration = duration;
        TotalMs = duration.TotalMilliseconds;

        _position = new double[series.Racers][];
        _present = new bool[series.Racers][];
        _rank = new int[series.Racers][];
        _floor = new double[series.Racers][];
        _ceiling = new double[series.Racers][];

        for (var k = 0; k < series.Racers; k++)
        {
            _position[k] = new double[series.Months];
            _present[k] = new bool[series.Months];
            _rank[k] = new int[series.Months];
            _floor[k] = new double[series.Months];
            _ceiling[k] = new double[series.Months];

            for (var i = 0; i < series.Months; i++)
            {
                _present[k][i] = series.Closes[k][i] > 0;

                if (!_present[k][i])
                {
                    _rank[k][i] = -1;
                    continue;
                }

                var (low, high) = FxRates.Corridor.Walls(series, k, i);

                _position[k][i] = FxRates.Corridor.Position(series, k, i);
                _floor[k][i] = low;
                _ceiling[k][i] = high;
            }
        }

        for (var i = 0; i < series.Months; i++)
        {
            var order = Enumerable.Range(0, series.Racers).Where(k => _present[k][i]).ToArray();

            Array.Sort(order, (a, b) => _position[b][i].CompareTo(_position[a][i]));

            for (var pos = 0; pos < order.Length; pos++)
            {
                _rank[order[pos]][i] = pos;
            }
        }
    }

    private double TotalMs { get; set; }

    public TimeSpan Duration { get; set; }

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleStart => TotalMs - FinaleMs;

    private double FinaleMs => Math.Clamp(TotalMs * 0.12, 2500, 8000);

    private double RaceSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>
    /// The word after the count of months — 个月 for a monthly series.
    ///
    /// Supplied by the page, for the same reason the race renderer asks for it: a renderer that
    /// cannot see the interval it was handed has no business naming it, and a monthly board
    /// announcing "124 个交易日" is a lie repeated on every frame.
    /// </summary>
    public string SpanWord { get; set; } = string.Empty;

    /// <summary>
    /// The word after the count of pairs — 对货币. Supplied by the page: it belongs to the list
    /// that was chosen, not to the corridor.
    /// </summary>
    public string UnitWord { get; set; } = string.Empty;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * TotalMs;

        context.Backdrop.Fill(session, context, Palette.Background);

        var state = StateAt(t);

        DrawRows(session, context, t, state);
        DrawFooter(session, context, t);
        DrawHeader(session, context, t, state);
        DrawProgress(session, context);
    }

    private (double[] Position, double[] Slots, int[] Finals, int MonthIndex) StateAt(double t)
    {
        var p = Easing.Ramp(t, IntroMs, RaceSpan);
        var pos = p * (_series.Months - 1);

        var i0 = (int)Math.Clamp(Math.Floor(pos), 0, _series.Months - 2);
        var i1 = Math.Min(_series.Months - 1, i0 + 1);
        var f = _series.Months > 1 ? Math.Clamp(pos - i0, 0, 1) : 0;
        var fe = SmoothStep(f);

        var positions = new double[_series.Racers];
        var slots = new double[_series.Racers];
        var finals = new int[_series.Racers];

        for (var k = 0; k < _series.Racers; k++)
        {
            positions[k] = Lerp(_position[k][i0], _position[k][i1], f);

            // A pair that arrives part-way through — the renminbi list's five non-dollar pairs
            // begin in 2016 — has no rank before it does. Taking the rank it holds once it is
            // there, rather than −1, is what lets it slide into the board instead of appearing
            // at the top for a frame first.
            var a = _rank[k][i0] < 0 ? _rank[k][i1] : _rank[k][i0];
            var b = _rank[k][i1] < 0 ? _rank[k][i0] : _rank[k][i1];

            slots[k] = Lerp(a, b, fe);
            finals[k] = _rank[k][^1];
        }

        return (positions, slots, finals, (int)Math.Round(pos));
    }

    private void DrawRows(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Position, double[] Slots, int[] Finals, int MonthIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var (x0, x1) = PlotColumns(context);
        var plotW = x1 - x0;

        var rows = Math.Max(1, _series.Racers);
        var rowH = (bottom - top) / rows;

        // Thinner than a race's bar, because a row carries three lines: the corridor, and under
        // it the floor and ceiling it is measured between.
        var barH = Math.Min(rowH * 0.30, context.Px(40));
        var radius = (float)Math.Min(barH / 2, context.Px(8));

        var nameSize = Math.Min(26, (rowH / context.Scale) * 0.30);
        var valueSize = Math.Min(24, (rowH / context.Scale) * 0.28);
        var smallSize = Math.Min(17, (rowH / context.Scale) * 0.20);

        using var nameFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var valueFormat = Ink.Format(context.Px(valueSize), bold: true);
        using var smallFormat = Ink.Format(context.Px(smallSize));

        // Trailing rows first, so a leader overlaps whoever it is passing.
        var order = Enumerable.Range(0, _series.Racers).OrderByDescending(k => state.Slots[k]).ToArray();

        foreach (var k in order)
        {
            if (!_present[k][state.MonthIndex])
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);

            if (intro <= 0)
            {
                continue;
            }

            var colour = Palette.Race16[Palette.RaceIndex(_series.Pairs[k].Code)];
            var yc = top + ((state.Slots[k] + 0.5) * rowH);
            var cx = x0 + (state.Position[k] * plotW);
            var filled = Math.Max(0, (cx - x0) * Easing.OutCubic(intro));

            var top2 = (float)(yc - (barH / 2));

            // The corridor itself: the whole row, because a corridor is a place and not a
            // quantity. Its own colour is the row's at a fifth of the way up the frame's
            // background, so six of them read as tracks rather than as bars.
            session.FillRoundedRectangle(
                (float)x0, top2, (float)plotW, (float)barH, radius, radius,
                Ink.Fade(Rgb(0x9C, 0xB4, 0xE0), 0.16));

            using (var brush = new CanvasLinearGradientBrush(
                session,
                [
                    new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.45) },
                    new CanvasGradientStop { Position = 1f, Color = Ink.Fade(colour, 0.95) },
                ])
            {
                StartPoint = new((float)x0, 0),
                EndPoint = new((float)(x0 + plotW), 0),
            })
            {
                session.FillRoundedRectangle(
                    (float)x0, top2, (float)Math.Max(filled, context.Px(2)), (float)barH,
                    radius, radius, brush);
            }

            // The midpoint: half a corridor is not a neutral position, but it is the one a
            // viewer needs a reference for before the percentage beside it means anything.
            session.DrawLine(
                new((float)(x0 + (plotW / 2)), (float)(yc - (barH * 0.62))),
                new((float)(x0 + (plotW / 2)), (float)(yc + (barH * 0.62))),
                Ink.Fade(Palette.Muted, 0.5 * intro),
                (float)Math.Max(1, context.Px(2)));

            // The marker. Taller than the corridor, so it reads as something placed on the row
            // rather than as the end of a bar.
            var markerColour = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

            session.DrawLine(
                new((float)cx, (float)(yc - (barH * 0.72))),
                new((float)cx, (float)(yc + (barH * 0.72))),
                Ink.Fade(markerColour, 0.95 * intro),
                (float)Math.Max(2, context.Px(4)));

            session.FillCircle(
                (float)cx, (float)yc, (float)Math.Max(context.Px(4), barH * 0.26),
                Ink.Fade(markerColour, intro));

            Ink.RightMiddle(session, _series.Pairs[k].Pair,
                x0 - context.Px(14), yc, nameFormat, colour, intro);

            var close = _series.Closes[k][state.MonthIndex];

            Ink.LeftAt(session, Rate(close), x1 + context.Px(14), yc - context.Px(9),
                valueFormat, markerColour, intro);

            Ink.LeftAt(session, Percent(state.Position[k]), x1 + context.Px(14), yc + context.Px(13),
                smallFormat, Ink.Fade(Palette.StockMuted, intro), 1);

            // What the corridor is, in the pair's own units — the only place on the frame that
            // says whether a row is a range of two points or of two hundred.
            var ends = context.Px(smallSize * 0.92);

            using var endFormat = Ink.Format(ends);

            Ink.LeftAt(session, Rate(_floor[k][state.MonthIndex]), x0,
                yc + (barH / 2) + context.Px(13), endFormat, Ink.Fade(Palette.StockMuted, intro), 1);

            Ink.RightMiddle(session, Rate(_ceiling[k][state.MonthIndex]), x1,
                yc + (barH / 2) + context.Px(13), endFormat, Ink.Fade(Palette.StockMuted, intro), 1);
        }
    }

    /// <summary>
    /// A rate to the precision the pair is quoted in: four decimals for a rate around one, two
    /// for one in the hundreds. One rule for all six rather than one per pair, because a corridor
    /// drawn from 157.9243 and one drawn from 1.1245 are the same picture and the extra digits
    /// are noise the frame cannot use — but dropping below two would put two different months of
    /// USD/JPY on the same number.
    /// </summary>
    private static string Rate(double value)
    {
        var decimals = Math.Abs(value) >= 100 ? 2 : 4;

        return value.ToString("N" + decimals.ToString(CultureInfo.InvariantCulture),
            CultureInfo.InvariantCulture);
    }

    private static string Percent(double position) =>
        ((int)Math.Round(position * 100)).ToString(CultureInfo.InvariantCulture) + "%";

    private void DrawFooter(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, FinaleStart - 1200, 900);

        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            format, Palette.Credit, a * 0.8);
    }

    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Position, double[] Slots, int[] Finals, int MonthIndex) state)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : Strings.Get("FxCorridorStageTitle");

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, title, context.Px(64), context.Width - context.Px(120), bold: true);

            using var format = Ink.Format(size, bold: true);

            Ink.Centred(session, title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, a);
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            Ink.Runs(
                session,
                [
                    (Month(_series.Dates[0]) + " " + Strings.Get("StockRangeJoiner") + " " +
                        Month(_series.Dates[^1]) + " · ", Palette.StockMuted, plain),
                    (_series.Months.ToString(CultureInfo.InvariantCulture), Palette.Emphasis, strong),
                    (" " + SpanWord + " · " + _series.Quoted.ToString(CultureInfo.InvariantCulture) +
                        " " + UnitWord, Palette.StockMuted, plain),
                ],
                cx, context.HeaderRow(0.188, ShowTitle), a);
        }

        using (var format = Ink.Format(context.Px(40), bold: true))
        {
            Ink.Centred(session, Month(_series.Dates[state.MonthIndex]), cx,
                context.HeaderRow(0.222, ShowTitle), format, Palette.Moving, a);
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
            Palette.RaceProgressFill,
            context.Width);
    }

    /// <summary>The plot's rows: the top anchored to the header block, the bottom to the credit.</summary>
    private (double Top, double Bottom) PlotArea(FrameContext context) =>
        (context.HeaderRow(HeaderTopFraction, ShowTitle), context.CreditLine - context.Px(CreditGap));

    /// <summary>The plot's left and right, gutters inside the user's margins.</summary>
    private (double Left, double Right) PlotColumns(FrameContext context) =>
        (context.Margins.Left + context.Px(GutterLeft),
         context.Width - context.Margins.Right - context.Px(GutterRight));

    /// <summary>
    /// A month, not a day: the axis is monthly and the series dates each month to its last day,
    /// so printing the day would claim a precision the source's month does not have.
    /// </summary>
    private static string Month(DateOnly day) => day.ToString("yyyy-MM", CultureInfo.InvariantCulture);

    private static double Lerp(double a, double b, double t) => a + ((b - a) * t);

    private static double SmoothStep(double t) => (t * t) * (3 - (2 * t));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}
