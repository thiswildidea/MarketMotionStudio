using System.Globalization;
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
/// The sector race: horizontal bars overtaking one another, their order changing to the last
/// frame — the port of `sector_race_studio.html`'s render path.
///
/// What makes it smooth is that **the ranking itself is interpolated**. The naive approach —
/// snap each row to its new position every time a trading day passes — moves the whole field in
/// steps. Instead every day's ranking is precomputed, playback maps to a fractional day index,
/// and a row's vertical position is its two neighbouring days' ranks eased with a smoothstep
/// while its length interpolates linearly: two rows that trade places cross over smoothly
/// rather than swapping. The whole thing is a pure function of the frame's progress, which is
/// what lets a scrubbed preview and a frame-by-frame export agree.
///
/// The axis range is interpolated per day too, for the same reason — otherwise the whole field
/// rescales in one jump at each midnight — with fixed headroom on both ends because the value
/// labels sit outside the bar's end until the bar is long enough to hold them inside.
/// </summary>
public sealed class SectorRaceRenderer : IFrameRenderer
{
    /// <summary>The left gutter's name column, in baseline pixels.</summary>
    private const double GutterLeft = 150;

    /// <summary>The right gutter's value-label column.</summary>
    private const double GutterRight = 130;

    /// <summary>Baseline rows between the plot's bottom and the credit.</summary>
    private const double CreditGap = 74;

    private const double HeaderTopFraction = 0.278;

    /// <summary>
    /// The source's fixed colour set, in order. A row keeps one colour for the whole video so a
    /// viewer can track it by colour — a ramp keyed to the value would repaint a row the moment
    /// it passed another.
    /// </summary>
    private static readonly Color[] Palette16 =
    [
        Rgb(0xEF, 0x44, 0x44), Rgb(0xF5, 0x9E, 0x0B), Rgb(0xEA, 0xB3, 0x08), Rgb(0x84, 0xCC, 0x16),
        Rgb(0x22, 0xC5, 0x5E), Rgb(0x14, 0xB8, 0xA6), Rgb(0x06, 0xB6, 0xD4), Rgb(0x3B, 0x82, 0xF6),
        Rgb(0x63, 0x66, 0xF1), Rgb(0x8B, 0x5C, 0xF6), Rgb(0xA8, 0x55, 0xF7), Rgb(0xD9, 0x46, 0xEF),
        Rgb(0xEC, 0x48, 0x99), Rgb(0xF4, 0x72, 0xB6), Rgb(0xFB, 0x92, 0x3C), Rgb(0x94, 0xA3, 0xB8),
    ];

    private readonly SectorRaceSeries _series;

    private readonly RaceMetric _metric;

    /// <summary>The per-day ranking: rank[k][i] is racer k's position on day i, 0 leading.</summary>
    private readonly int[][] _rank;

    /// <summary>The axis range per day, precomputed with its headroom.</summary>
    private readonly double[] _axisMin;

    private readonly double[] _axisMax;

    public SectorRaceRenderer(SectorRaceSeries series, RaceMetric metric, TimeSpan duration)
    {
        _series = series;
        _metric = metric;
        Duration = duration;
        TotalMs = duration.TotalMilliseconds;

        var values = series.ReturnsOrAmounts(metric);

        _rank = new int[series.Racers][];

        for (var k = 0; k < series.Racers; k++)
        {
            _rank[k] = new int[series.Days];
        }

        var order = new int[series.Racers];

        for (var i = 0; i < series.Days; i++)
        {
            for (var k = 0; k < series.Racers; k++)
            {
                order[k] = k;
            }

            Array.Sort(order, (a, b) => values[b][i].CompareTo(values[a][i]));

            for (var pos = 0; pos < order.Length; pos++)
            {
                _rank[order[pos]][i] = pos;
            }
        }

        // The axis range per day, with the headroom the labels need. Both ends: the labels sit
        // outside the bar's end, so without room the longest bar pushes its label into the names.
        _axisMin = new double[series.Days];
        _axisMax = new double[series.Days];

        for (var i = 0; i < series.Days; i++)
        {
            var low = double.MaxValue;
            var high = double.MinValue;

            for (var k = 0; k < series.Racers; k++)
            {
                low = Math.Min(low, values[k][i]);
                high = Math.Max(high, values[k][i]);
            }

            var lo = Math.Min(low, 0);
            var hi = Math.Max(high, 0);
            var span = (hi - lo) is var s && s == 0 ? 1 : s;

            _axisMin[i] = lo < 0 ? lo - (span * 0.22) : lo;
            _axisMax[i] = hi > 0 ? hi + (span * 0.16) : hi;
        }
    }

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>The metric's own unit word, on every value label.</summary>
    private string Unit => _metric is RaceMetric.Return ? "%" : Strings.Get("SectorUnitYi");

    private int Decimals => _metric is RaceMetric.Return ? 2 : 0;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * TotalMs;

        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height), Palette.Background);

        var state = StateAt(t);
        DrawAxis(session, context, t, state);
        DrawRows(session, context, t, state);
        DrawFooter(session, context, t);
        DrawHeader(session, context, t, state);
        DrawProgress(session, context);
    }

    /// <summary>Animation shape: the source's own proportions.</summary>
    private double TotalMs { get; set; }

    public TimeSpan Duration { get; set; }

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleStart => TotalMs - FinaleMs;

    private double FinaleMs => Math.Clamp(TotalMs * 0.12, 2500, 8000);

    private double RaceSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

    /// <summary>
    /// Everything one moment needs: each racer's value, its interpolated slot, and the
    /// interpolated axis range. A pure function of the time — no state carried between frames.
    /// </summary>
    private (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) StateAt(double t)
    {
        var values = _series.ReturnsOrAmounts(_metric);

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
            vals[k] = Lerp(values[k][i0], values[k][i1], f);
            slots[k] = Lerp(_rank[k][i0], _rank[k][i1], fe);
            finals[k] = _rank[k][^1];
        }

        return (vals, slots, finals,
            Lerp(_axisMin[i0], _axisMin[i1], f),
            Lerp(_axisMax[i0], _axisMax[i1], f),
            (int)Math.Round(pos));
    }

    private void DrawAxis(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 400, 1200);
        if (a <= 0)
        {
            return;
        }

        var (top, bottom) = PlotArea(context);
        var (x0, _) = PlotColumns(context);
        var zx = ZeroX(context, state);

        session.DrawLine(
            new((float)zx, (float)(top - context.Px(10))),
            new((float)zx, (float)(bottom + context.Px(10))),
            Ink.Fade(Palette.Grid, a),
            (float)Math.Max(1, context.Px(2)));
    }

    private void DrawRows(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var (x0, x1) = PlotColumns(context);
        var plotW = x1 - x0;
        var rowH = (bottom - top) / Math.Max(1, _series.Racers);
        var barH = Math.Min(rowH * 0.64, context.Px(96));
        var nameSize = Math.Min(30, (rowH / context.Scale) * 0.34);

        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;
        var zx = x0 + ((0 - state.AxisMin) / span) * plotW;

        // Trailing rows first, so a leader overlaps whoever it is passing.
        var order = Enumerable.Range(0, _series.Racers).OrderByDescending(k => state.Slots[k]).ToArray();

        using var nameFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var strongFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var valueFormat = Ink.Format(context.Px(nameSize), bold: true);

        foreach (var k in order)
        {
            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            var colour = Palette16[k % Palette16.Length];
            var yc = top + ((state.Slots[k] + 0.5) * rowH);
            var vx = x0 + ((state.Values[k] - state.AxisMin) / span) * plotW;

            var left = Math.Min(zx, vx);
            var right = Math.Max(zx, vx);
            var w = Math.Max(context.Px(3), (right - left) * Easing.OutCubic(intro));
            var bx = vx >= zx ? zx : zx - w;

            // The champion gets a glow through the closing stretch, so the final frame has a focus.
            var champion = t > FinaleStart && state.Finals[k] == 0;

            void Bar(CanvasDrawingSession ds)
            {
                using var brush = new CanvasLinearGradientBrush(
                    ds,
                    [
                        new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.55) },
                        new CanvasGradientStop { Position = 1f, Color = Ink.Fade(colour, 0.98) },
                    ])
                {
                    StartPoint = new((float)bx, 0),
                    EndPoint = new((float)(bx + w), 0),
                };

                ds.FillRoundedRectangle(
                    (float)bx, (float)(yc - (barH / 2)), (float)w, (float)barH,
                    (float)context.Px(6), (float)context.Px(6), brush);
            }

            if (champion)
            {
                // shadowBlur 26 → sigma ~13.
                Ink.Glow(session, context.Px(13), 0.85, Bar);
            }

            Bar(session);

            // The name sits in the left gutter, right-aligned against the plot.
            var nameColour = champion ? Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF) : Rgb(0xC9, 0xD8, 0xF5);

            Ink.RightMiddle(session, _series.Entries[k].Name,
                x0 - context.Px(14), yc, nameFormat, nameColour, intro);

            // The value follows the bar's end outside it; a bar long enough holds its own label
            // inside. Outside, the axis's proportional headroom cannot guarantee room for a label
            // of fixed pixel width — the longest bar is the one that would push its label into
            // the names, and by construction it is also the one long enough to hold it inside.
            var text = ValueText(state.Values[k]);
            var textWidth = Ink.Measure(session, text, valueFormat);
            var inside = w >= textWidth + context.Px(26);

            Color valueColour = inside
                ? Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF)
                : _metric is RaceMetric.Return
                    ? (state.Values[k] >= 0 ? Palette.Emphasis : Rgb(0x4A, 0xDE, 0x80))
                    : colour;

            if (vx >= zx)
            {
                if (inside)
                {
                    Ink.RightMiddle(session, text, bx + w - context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.LeftAt(session, text, bx + w + context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
            else
            {
                if (inside)
                {
                    Ink.LeftAt(session, text, bx + context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.RightMiddle(session, text, bx - context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
        }
    }

    private string ValueText(double value) =>
        (_metric is RaceMetric.Return && value > 0 ? "+" : string.Empty)
        + value.ToString("N" + Decimals.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture)
        + Unit;

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
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : AutoTitle();

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, title, context.Px(64), context.Width - context.Px(120), bold: true);

            using var format = Ink.Format(size, bold: true);

            Ink.Centred(session, title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, a);
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            var unit = _series.Racers == 0 ? string.Empty : UnitWord;

            Ink.Runs(
                session,
                [
                    (Iso(_series.Dates[0]) + " " + Strings.Get("StockRangeJoiner") + " " + Iso(_series.Dates[^1]) + " · ",
                        Palette.StockMuted, plain),
                    (_series.Days.ToString(CultureInfo.InvariantCulture), Palette.Emphasis, strong),
                    (" " + Strings.Get("StockTradingDaysUnit") + " · " + _series.Racers.ToString(CultureInfo.InvariantCulture) + " " + unit,
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
    private (double Top, double Bottom) PlotArea(FrameContext context)
    {
        var top = context.HeaderRow(HeaderTopFraction, ShowTitle);
        var bottom = context.CreditLine - context.Px(CreditGap);

        return (top, bottom);
    }

    /// <summary>The plot's left and right, gutters inside the user's margins.</summary>
    private (double Left, double Right) PlotColumns(FrameContext context) =>
        (context.Margins.Left + context.Px(GutterLeft),
         context.Width - context.Margins.Right - context.Px(GutterRight));

    private double ZeroX(FrameContext context,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (x0, x1) = PlotColumns(context);
        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;

        return x0 + ((0 - state.AxisMin) / span) * (x1 - x0);
    }

    /// <summary>“{list} 涨幅竞速” / “{list} 成交额竞速” — the source's own auto-title shape.</summary>
    private string AutoTitle() => Strings.Format(
        _metric is RaceMetric.Return ? "SectorAutoTitleReturn" : "SectorAutoTitleAmount",
        ListLabel);

    /// <summary>The roster's name, supplied by the page — it knows which list was chosen.</summary>
    public string ListLabel { get; set; } = string.Empty;

    /// <summary>
    /// The count word for the header line — 个板块 or 只个股. Supplied by the page because it
    /// belongs to the roster, not to the metric: a key keyed on the metric here is how
    /// `[SectorUnitPercent]` ended up rendered literally in a shipped frame.
    /// </summary>
    public string UnitWord { get; set; } = string.Empty;

    private static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private static double Lerp(double a, double b, double t) => a + ((b - a) * t);

    private static double SmoothStep(double t) => (t * t) * (3 - (2 * t));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}

/// <summary>Every racer's chosen measure as a per-racer array over the shared days.</summary>
public static class SectorSeriesExtensions
{
    public static double[][] ReturnsOrAmounts(this SectorRaceSeries series, RaceMetric metric) =>
        metric is RaceMetric.Return ? [.. series.Returns] : [.. series.Amounts];
}
