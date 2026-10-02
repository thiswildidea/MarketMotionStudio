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
/// The underwater board: one filled curve per holding, each hanging below its own high-water line
/// and sinking as the months go by.
///
/// Every other board in this app draws a value as a length — a bar that grows. Depth is not a
/// length: it is a *shape over time*, and a bar can only say how deep the water is right now.
/// The curve is what makes the two numbers on this board readable at once, because the deepest
/// point and the climb back out of it are two places on it, and the distance between them across
/// the frame is the months it took.
///
/// **One depth scale for every row, and that is the page's honesty.** Scaling each row to its own
/// worst would draw the money-market fund's 0.2% as a chasm the size of the CSI 500's 56%, on a
/// board whose whole claim is that those are not the same thing. So the axis runs from zero to the
/// deepest point any row on the board has reached, the fund that never really fell is a flat line
/// pinned to the top of its row, and that flatness *is* what the row says.
///
/// The rows still race. They are ordered by how far below their own high each one currently is —
/// closest to its high at the top — and they trade places as their months pass, which is why the
/// ordering is precomputed per month and interpolated, exactly as it is in
/// <see cref="SectorRaceRenderer"/>: two rows that swap do so by sliding past each other.
/// </summary>
public sealed class UnderwaterRenderer : IFrameRenderer
{
    /// <summary>The left gutter's name column, in baseline pixels.</summary>
    private const double GutterLeft = 150;

    /// <summary>
    /// The right gutter, wider than a race's: a row carries three lines on it — where it is now,
    /// how deep it got, and how long the climb took — and a date has to fit in words.
    /// </summary>
    private const double GutterRight = 210;

    /// <summary>Baseline rows between the plot's bottom and the credit.</summary>
    private const double CreditGap = 74;

    private const double HeaderTopFraction = 0.278;

    private readonly DrawdownSeries _series;

    /// <summary>The per-month ordering: rank[k][i] is holding k's place on month i, 0 shallowest.</summary>
    private readonly int[][] _rank;

    /// <summary>Per holding, the first month it is on the board for; past the end when never.</summary>
    private readonly int[] _starts;

    /// <summary>The depth the axis reaches on each month — the deepest point any row has hit.</summary>
    private readonly double[] _depth;

    public UnderwaterRenderer(DrawdownSeries series, TimeSpan duration)
    {
        _series = series;
        Duration = duration;
        TotalMs = duration.TotalMilliseconds;

        _rank = new int[series.Racers][];
        _starts = new int[series.Racers];

        for (var k = 0; k < series.Racers; k++)
        {
            _rank[k] = new int[series.Days];
            _starts[k] = Math.Max(0, series.StartOf(k));
        }

        var field = new List<int>(series.Racers);
        var order = new int[series.Racers];

        for (var i = 0; i < series.Days; i++)
        {
            // Only the rows on the board are ordered, and the rest are filed after them: a
            // holding whose history begins later has no depth to show, and giving it one would
            // rank it by a fall it never took.
            field.Clear();

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    field.Add(k);
                }
            }

            for (var n = 0; n < field.Count; n++)
            {
                order[n] = field[n];
            }

            // Shallowest first: −2% has been kinder to its holder than −40%, and the top of this
            // board is the good end even though every number on it is a fall.
            Array.Sort(order, 0, field.Count, Comparer<int>.Create(
                (a, b) => _series.Underwater[b][i].CompareTo(_series.Underwater[a][i])));

            var absent = field.Count;

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    continue;
                }

                order[absent++] = k;
            }

            for (var pos = 0; pos < order.Length; pos++)
            {
                _rank[order[pos]][i] = pos;
            }
        }

        // One scale for the whole board, per month, with headroom under the deepest point: the
        // curve needs room below its own low before the row's edge cuts it off — and without
        // headroom the deepest row touches the row beneath it and the two read as one shape.
        _depth = new double[series.Days];

        for (var i = 0; i < series.Days; i++)
        {
            var low = 0.0;

            for (var k = 0; k < series.Racers; k++)
            {
                if (i < _starts[k])
                {
                    continue;
                }

                low = Math.Min(low, _series.Underwater[k][i]);
            }

            // Never zero: a board of rows all sitting at their own high has no scale to divide
            // by, and one percent of headroom is a floor the flat rows still fit inside.
            _depth[i] = Math.Min(low * 1.14, -1.0);
        }
    }

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    public TimeSpan Duration { get; set; }

    private double TotalMs { get; set; }

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleStart => TotalMs - FinaleMs;

    private double FinaleMs => Math.Clamp(TotalMs * 0.12, 2500, 8000);

    private double RaceSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

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

    /// <summary>Everything one moment needs: each row's depth and slot, and the shared scale.</summary>
    private (double[] Values, double[] Slots, int[] Finals, double Depth, int DayIndex, double Position) StateAt(double t)
    {
        var p = Easing.Ramp(t, IntroMs, RaceSpan);
        var pos = p * (_series.Days - 1);

        var i0 = (int)Math.Clamp(Math.Floor(pos), 0, _series.Days - 2);
        var i1 = Math.Min(_series.Days - 1, i0 + 1);
        var f = _series.Days > 1 ? Math.Clamp(pos - i0, 0, 1) : 0;
        var fe = SmoothStep(f);

        var vals = new double[_series.Racers];
        var slots = new double[_series.Racers];
        var finals = new int[_series.Racers];

        for (var k = 0; k < _series.Racers; k++)
        {
            vals[k] = Lerp(_series.Underwater[k][i0], _series.Underwater[k][i1], f);
            slots[k] = Lerp(_rank[k][i0], _rank[k][i1], fe);
            finals[k] = _rank[k][^1];
        }

        return (vals, slots, finals, Lerp(_depth[i0], _depth[i1], f), (int)Math.Round(pos), pos);
    }

    private void DrawRows(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double Depth, int DayIndex, double Position) state)
    {
        var (top, bottom) = PlotArea(context);
        var (x0, x1) = PlotColumns(context);
        var plotW = x1 - x0;

        var rows = Math.Max(1, _series.Racers);
        var rowH = (bottom - top) / rows;
        var nameSize = Math.Min(30, (rowH / context.Scale) * 0.34);

        // Trailing rows first, so a row overtaking another passes over it.
        var order = Enumerable.Range(0, _series.Racers).OrderByDescending(k => state.Slots[k]).ToArray();

        var nameFormat = NameFormat(session, context, nameSize);

        using var valueFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var smallFormat = Ink.Format(context.Px(nameSize * 0.6));

        foreach (var k in order)
        {
            if (state.DayIndex < _starts[k])
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            var yc = top + ((state.Slots[k] + 0.5) * rowH);
            var zeroY = yc - (rowH / 2) + context.Px(10);
            var span = rowH * 0.74;

            // The depth scale is shared, so a row's own curve is clipped by its own row height:
            // the deepest fall on the board is drawn at 88% of a row, and every other fall is
            // shallower than it on the same ruler.
            double DepthY(double value) => zeroY + ((value / state.Depth) * span);

            var colour = Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)];
            var from = _starts[k];
            var to = state.Position;

            // One time axis for the whole board, not one per row. A row that joins late has to
            // start where its own month falls on that axis and leave the months before it blank,
            // because a row that began at the left edge would be claiming it was held for years
            // it did not exist — and on a board of depths, the left edge is where the worst of
            // the fall usually is.
            double X(double month) => x0 + (month / Math.Max(1, _series.Days - 1)) * plotW;

            var points = new List<Vector2>();
            var last = Math.Min((int)Math.Floor(to), _series.Days - 1);

            for (var i = from; i <= last; i++)
            {
                points.Add(new((float)X(i), (float)DepthY(_series.Underwater[k][i])));
            }

            // The curve's leading edge, between two months: without it the line advances in
            // monthly steps on a board that is otherwise continuous.
            var ease = Easing.OutCubic(intro);

            if (last + 1 <= _series.Days - 1 && to > last)
            {
                var f = to - last;

                points.Add(new(
                    (float)Lerp(X(last), X(last + 1), f),
                    (float)Lerp(
                        DepthY(_series.Underwater[k][last]),
                        DepthY(_series.Underwater[k][last + 1]),
                        f)));
            }

            if (points.Count >= 2)
            {
                void Curve(CanvasDrawingSession ds)
                {
                    using var fill = new CanvasPathBuilder(ds);

                    fill.BeginFigure(new(points[0].X, (float)zeroY));

                    for (var i = 0; i < points.Count; i++)
                    {
                        fill.AddLine(points[i]);
                    }

                    fill.AddLine(new(points[^1].X, (float)zeroY));
                    fill.EndFigure(CanvasFigureLoop.Closed);

                    using var area = CanvasGeometry.CreatePath(fill);

                    // The fill deepens with depth. A flat 30% wash was invisible against the
                    // background — the board read as eight thin scribbles rather than as water —
                    // and a depth that is only a stroke does not look like one. Weighting it also
                    // says the same thing the axis does: the deeper the water, the heavier.
                    using var wash = new CanvasLinearGradientBrush(
                        ds,
                        [
                            new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.2 * ease) },
                            new CanvasGradientStop { Position = 1f, Color = Ink.Fade(colour, 0.62 * ease) },
                        ])
                    {
                        StartPoint = new(0, (float)zeroY),
                        EndPoint = new(0, (float)(zeroY + span)),
                    };

                    ds.FillGeometry(area, wash);

                    using var line = Polyline(ds, [.. points]);

                    ds.DrawGeometry(line, Ink.Fade(colour, 0.95 * ease), (float)Math.Max(1.5, context.Px(3)));
                }

                // The shallowest row glows through the closing stretch, which on this board is
                // the one back at its own high: the same place the champion occupies on a race,
                // and the same reason — a board whose rows move needs a place to rest the eye.
                if (t > FinaleStart && state.Finals[k] == 0)
                {
                    Ink.Glow(session, context.Px(13), 0.85, Curve);
                }

                Curve(session);
            }

            // The high-water line the row hangs from: a holding at its own high has no curve
            // under it at all, and without this line there is nothing to see it is level with.
            session.DrawLine(
                new((float)x0, (float)zeroY), new((float)x1, (float)zeroY),
                Ink.Fade(Palette.Grid, intro), (float)Math.Max(1, context.Px(2)));

            // The deepest point, once it has happened — the two numbers the row is about are the
            // places on its curve, so the one that names the depth is marked.
            var deepestAt = DeepestIndex(k);

            if (deepestAt >= from && deepestAt <= last)
            {
                session.FillCircle(
                    new((float)X(deepestAt), (float)DepthY(_series.Underwater[k][deepestAt])),
                    (float)Math.Max(2, context.Px(4)), Ink.Fade(colour, 0.9 * intro));
            }

            Ink.RightMiddle(session, _series.Entries[k].Name,
                x0 - context.Px(14), yc, nameFormat, Rgb(0xC9, 0xD8, 0xF5), intro);

            // Three lines in the right gutter: where the row is, how deep it got, how long it
            // took back. The last of the three is the one a single number cannot carry — a fall
            // of 25% mended in six months and one of 25% still open are not the same fact, and
            // only the third line says which this row is.
            Ink.LeftAt(session, DepthText(state.Values[k]), x1 + context.Px(12),
                yc - context.Px(12), valueFormat, Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), intro);

            Ink.LeftAt(session, Strings.Format("DrawdownDeepest", DepthText(_series.Deepest[k])),
                x1 + context.Px(12), yc + context.Px(16), smallFormat,
                Rgb(0x4A, 0xDE, 0x80), intro * 0.9);

            Ink.LeftAt(session, HealedText(_series.HealedMonths[k]),
                x1 + context.Px(12), yc + context.Px(36), smallFormat,
                Palette.StockMuted, intro * 0.85);
        }
    }

    /// <summary>The month a holding's deepest point fell on, or −1 when it never fell.</summary>
    private int DeepestIndex(int k)
    {
        if (_series.Deepest[k] > -0.005)
        {
            return -1;
        }

        for (var i = _starts[k]; i < _series.Days; i++)
        {
            if (_series.Underwater[k][i] <= _series.Deepest[k])
            {
                return i;
            }
        }

        return -1;
    }

    /// <summary>“−9.96%” — every value on this board is below zero, so the sign is not optional.</summary>
    private static string DepthText(double value) =>
        "−" + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    /// <summary>How long the climb took, in the page's own words: “86 个月修复” or “至今未修复”.</summary>
    private static string HealedText(int months) => months switch
    {
        Drawdown.NotHealed => Strings.Get("DrawdownNotHealed"),
        Drawdown.NeverFell => Strings.Get("DrawdownNeverFell"),
        _ => Strings.Format("DrawdownHealed", months.ToString(CultureInfo.InvariantCulture)),
    };

    private CanvasTextFormat? _names;

    private double _namesFor = -1;

    /// <summary>
    /// The left gutter's format, sized down until the longest name fits — one size for the whole
    /// column, and measured once rather than per frame. See the longer note on
    /// <see cref="SectorRaceRenderer.NameFormat"/>.
    /// </summary>
    private CanvasTextFormat NameFormat(CanvasDrawingSession session, FrameContext context, double wanted)
    {
        if (_names is not null && Math.Abs(_namesFor - wanted) < 0.01)
        {
            return _names;
        }

        var (x0, _) = PlotColumns(context);
        var room = x0 - context.Margins.Left - context.Px(24);
        var size = wanted;

        foreach (var entry in _series.Entries)
        {
            if (entry.Name.Length > 0)
            {
                size = Math.Min(size, Ink.FitSize(session, entry.Name, context.Px(wanted), room, bold: true));
            }
        }

        _names?.Dispose();

        _namesFor = wanted;
        _names = Ink.Format(context.Px(Math.Max(wanted * 0.5, size)), bold: true);

        return _names;
    }

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
        (double[] Values, double[] Slots, int[] Finals, double Depth, int DayIndex, double Position) state)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, Title, context.Px(64), context.Width - context.Px(120), bold: true);

            using var format = Ink.Format(size, bold: true);

            Ink.Centred(session, Title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, a);
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            Ink.Runs(
                session,
                [
                    (Iso(_series.Dates[0]) + " " + Strings.Get("StockRangeJoiner") + " " + Iso(_series.Dates[^1]) + " · ",
                        Palette.StockMuted, plain),
                    (_series.Days.ToString(CultureInfo.InvariantCulture), Palette.Emphasis, strong),
                    (" " + Span + " · " + _series.Racers.ToString(CultureInfo.InvariantCulture) + " " + UnitWord,
                        Palette.StockMuted, plain),
                ],
                cx, context.HeaderRow(0.188, ShowTitle), a);
        }

        using (var format = Ink.Format(context.Px(40), bold: true))
        {
            Ink.Centred(session, Iso(_series.Dates[state.DayIndex]), cx,
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
    /// The word after the count of months — 个月 for a monthly series. Supplied by the page,
    /// which is what asked the source for months; the renderer only knows how many came back.
    /// </summary>
    public string SpanWord { get; set; } = string.Empty;

    private string Span => SpanWord.Length > 0 ? SpanWord : Strings.Get("StockTradingDaysUnit");

    /// <summary>个标的, 只个股 — the count word belongs to the roster, so the page supplies it.</summary>
    public string UnitWord { get; set; } = string.Empty;

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

    private static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private static double Lerp(double a, double b, double t) => a + ((b - a) * t);

    private static double SmoothStep(double t) => (t * t) * (3 - (2 * t));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}
