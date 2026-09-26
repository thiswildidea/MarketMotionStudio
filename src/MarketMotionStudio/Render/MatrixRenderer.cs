using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The monthly matrix: rows and columns of cells lighting up in time order, with a summary
/// column and four statistic cards — the port of `monthly_matrix_studio.html`'s render path.
///
/// One renderer draws both kinds, because the kinds differ in what the rows and columns *are*
/// rather than in how a grid is drawn; the differences were resolved when the spec was built.
/// The compare kind with more than twelve months folds into horizontal bands of twelve, each
/// band carrying its own column heads and a sub-total column — cells stay big enough to read,
/// which is the whole point of folding rather than shrinking.
///
/// Cell colour is red up green down with depth as the square root of magnitude over the frame's
/// largest: linear puts nearly every month at almost the same dark tone, because most months
/// are far smaller than the extreme — the square root lifts small moves into visibility while
/// keeping the extreme distinct.
/// </summary>
public sealed class MatrixRenderer : IFrameRenderer
{
    /// <summary>Months per band when the compare kind folds.</summary>
    private const int PerBand = 12;

    private const double GridTopFraction = 0.395;

    /// <summary>Baseline rows between the grid's bottom and the statistic cards.</summary>
    private const double StatsAboveCredit = 250;

    private readonly MatrixSpec _spec;

    private readonly TimeSpan _duration;

    public MatrixRenderer(MatrixSpec spec, TimeSpan duration)
    {
        _spec = spec;
        _duration = duration;
    }

    public string Title { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    private double TotalMs => _duration.TotalMilliseconds;

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleMs => Math.Clamp(TotalMs * 0.14, 2500, 8000);

    private double FinaleStart => TotalMs - FinaleMs;

    private double GrowSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

    private double CellMs { get; set; }

    private double StaggerMs { get; set; }

    private double AbsMax { get; set; }

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        AbsMax = Math.Max(0.0001, _spec.Cells.Count > 0 ? _spec.Cells.Max(c => Math.Abs(c.Value)) : 1);

        CellMs = Math.Min(900, Math.Max(180, GrowSpan / Math.Max(1, _spec.Cells.Count) * 2.4));
        StaggerMs = _spec.Cells.Count > 1
            ? (GrowSpan - CellMs) / (_spec.Cells.Count - 1)
            : 0;

        var t = context.Progress * TotalMs;

        // The source's own backdrop: the same shape, lifted green at the top.
        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height),
        [
            (0f, Rgb(0x0C, 0x1A, 0x14)),
            (0.5f, Rgb(0x09, 0x0E, 0x1D)),
            (1f, Rgb(0x07, 0x09, 0x14)),
        ]);

        var current = DrawGrid(session, context, t);
        DrawStats(session, context, t);
        DrawHeader(session, context, t, current);
        DrawProgress(session, context);
    }

    /// <summary>
    /// The grid and its labels. Returns the cell the header should read out — the most recently
    /// *started* one, which in a gap between cells is still the last one that started rather
    /// than snapping back to the first.
    /// </summary>
    private MatrixCell? DrawGrid(CanvasDrawingSession session, FrameContext context, double t)
    {
        var rows = _spec.RowLabels.Count;
        var months = _spec.ColumnLabels.Count;
        var isCompare = _spec.Kind == "cmp";

        var bands = isCompare ? (int)Math.Ceiling(months / (double)PerBand) : 1;
        var slots = Math.Min(months, PerBand) + 1;

        var ml = context.Margins.Left;
        var plotW = context.ChartWidth;
        var gridTop = context.HeaderRow(GridTopFraction, ShowTitle);
        var gridBottom = context.CreditLine - context.Px(StatsAboveCredit);

        var headH = Math.Min(context.Px(42), (gridBottom - gridTop) * 0.10);
        var bandGap = context.Px(18);
        var labelW = Math.Min(context.Px(isCompare ? 130 : 80), plotW * 0.22);
        var cw = (plotW - labelW) / slots;

        var chMax = ((gridBottom - gridTop) - ((bands - 1) * bandGap) - (bands * headH)) / (bands * rows);
        var ch = Math.Min(chMax, Math.Max(cw * 1.05, Math.Min(chMax, context.Px(120))));

        var totalH = (bands * (headH + (rows * ch))) + ((bands - 1) * bandGap);
        var top0 = gridTop + ((gridBottom - gridTop) - totalH) / 2;
        var gap = Math.Max(context.Px(2), Math.Min(cw, ch) * 0.09);

        double BandTop(int b) => top0 + (b * (headH + (rows * ch) + bandGap));
        int BandColumns(int b) => Math.Min((b + 1) * PerBand, months) - (b * PerBand);

        MatrixCell? current = null;

        // Column heads, thinned when the width cannot carry every label.
        using (var headFormat = Ink.Format(Math.Clamp(cw / context.Scale * 0.30, 11, 22)))
        {
            var headText = "00/00";
            var headWidth = Ink.Measure(session, headText, headFormat);
            var step = Math.Max(1, (int)Math.Ceiling(headWidth / (cw * 0.92)));

            for (var b = 0; b < bands; b++)
            {
                var count = BandColumns(b);
                var sumSlot = b < bands - 1 || count == PerBand ? PerBand : count;
                var sumLabel = bands == 1
                    ? _spec.TailLabel
                    : Strings.Get(b < bands - 1 ? "MatrixTailSubtotal" : "MatrixTailTotal");

                for (var c = 0; c < count; c++)
                {
                    if (c % step != 0)
                    {
                        continue;
                    }

                    Ink.Centred(session, _spec.ColumnLabels[(b * PerBand) + c],
                        ml + labelW + (c * cw) + (cw / 2), BandTop(b) - (headH * 0.42),
                        headFormat, Palette.Credit);
                }

                Ink.Centred(session, sumLabel,
                    ml + labelW + (sumSlot * cw) + (cw / 2), BandTop(b) - (headH * 0.42),
                    headFormat, Palette.Credit);
            }
        }

        // Row labels, right-aligned into the grid.
        using (var rowFormat = Ink.Format(Math.Clamp(ch / context.Scale * 0.38, 13, 26), bold: true))
        {
            for (var b = 0; b < bands; b++)
            {
                for (var r = 0; r < rows; r++)
                {
                    Ink.RightMiddle(session, _spec.RowLabels[r],
                        ml + labelW - context.Px(10), BandTop(b) + (r * ch) + (ch / 2),
                        rowFormat, Palette.MonthLabel);
                }
            }
        }

        using var cellFormat = Ink.Format(Math.Clamp(cw / context.Scale * 0.24, 10, 18), bold: true);

        // The cells, in spec order — which is time order.
        for (var i = 0; i < _spec.Cells.Count; i++)
        {
            var cell = _spec.Cells[i];
            var start = IntroMs + (i * StaggerMs);

            if (t <= start)
            {
                break;
            }

            var raw = Easing.Ramp(t, start, CellMs);
            var band = cell.Column / PerBand;
            var local = cell.Column - (band * PerBand);
            var x = ml + labelW + (local * cw);
            var y = BandTop(band) + (cell.Row * ch);

            var colour = Palette.Return(cell.Value, AbsMax);

            void Cell(CanvasDrawingSession ds)
            {
                var radius = (float)Math.Max(context.Px(2), Math.Min(cw, ch) * 0.14);

                ds.FillRoundedRectangle(
                    (float)(x + (gap / 2)), (float)(y + (gap / 2)),
                    (float)(cw - gap), (float)(ch - gap), radius, radius,
                    Ink.Fade(colour, 0.95 * (0.25 + (0.75 * raw))));
            }

            // shadowBlur 16 → sigma ~8, while the cell is still arriving.
            if (raw < 1)
            {
                Ink.Glow(session, context.Px(8), 0.9, Cell);
            }
            else
            {
                Cell(session);
            }

            if (cw > context.Px(46) && raw > 0.5)
            {
                Ink.Centred(session, cell.Value.ToString("0", CultureInfo.InvariantCulture),
                    x + (cw / 2), y + (ch / 2) + (cellFormat.FontSize * 0.35),
                    cellFormat, Rgb(0xF4, 0xF8, 0xFF), (raw - 0.5) / 0.5);
            }

            current = cell;
        }

        // The summary column: each row's appears once its band's last cell has finished.
        using var tailFormat = Ink.Format(Math.Clamp(cw / context.Scale * 0.24, 10, 18), bold: true);
        var lastIndexByRow = new Dictionary<int, int>();

        for (var i = 0; i < _spec.Cells.Count; i++)
        {
            lastIndexByRow[_spec.Cells[i].Row * 1000 + _spec.Cells[i].Column] = i;
        }

        for (var b = 0; b < bands; b++)
        {
            var count = BandColumns(b);
            var sumSlot = b < bands - 1 || count == PerBand ? PerBand : count;

            for (var r = 0; r < rows; r++)
            {
                var lastColumn = (b * PerBand) + count - 1;

                if (!lastIndexByRow.TryGetValue(r * 1000 + lastColumn, out var index))
                {
                    continue;
                }

                var appear = Easing.Ramp(t, IntroMs + (index * StaggerMs) + CellMs, 500);
                if (appear <= 0)
                {
                    continue;
                }

                var value = _spec.Tail[r];
                var x = ml + labelW + (sumSlot * cw);
                var y = BandTop(b) + (r * ch);
                var edge = value >= 0 ? Rgb(0xEF, 0x44, 0x44) : Rgb(0x22, 0xC5, 0x5E);

                session.DrawRoundedRectangle(
                    (float)(x + (gap / 2)), (float)(y + (gap / 2)),
                    (float)(cw - gap), (float)(ch - gap),
                    (float)Math.Max(context.Px(2), Math.Min(cw, ch) * 0.14),
                    (float)Math.Max(context.Px(2), Math.Min(cw, ch) * 0.14),
                    Ink.Fade(edge, 0.85 * appear),
                    (float)context.Px(2));

                Ink.Centred(session, value.ToString("0", CultureInfo.InvariantCulture),
                    x + (cw / 2), y + (ch / 2) + (tailFormat.FontSize * 0.35),
                    tailFormat,
                    value >= 0 ? Rgb(0xFF, 0x80, 0x80) : Rgb(0x4A, 0xDE, 0x80),
                    appear);
            }
        }

        return current;
    }

    /// <summary>The four closing cards, over the credit.</summary>
    private void DrawStats(CanvasDrawingSession session, FrameContext context, double t)
    {
        var appear = Easing.Ramp(t, FinaleStart - 800, 900);
        if (appear <= 0)
        {
            return;
        }

        var ml = context.Margins.Left;
        var plotW = context.ChartWidth;
        var gap = context.Px(14);
        var cardW = (plotW - (gap * 3)) / 4;
        var cardH = context.Px(132);
        var top = context.CreditLine - context.Px(192);

        for (var i = 0; i < _spec.Stats.Count && i < 4; i++)
        {
            var (label, value) = _spec.Stats[i];
            var x = ml + (i * (cardW + gap));

            session.FillRoundedRectangle(
                (float)x, (float)top, (float)cardW, (float)cardH,
                (float)context.Px(14), (float)context.Px(14),
                Ink.Fade(Palette.CardFill, 0.9 * appear));

            session.DrawRoundedRectangle(
                (float)x, (float)top, (float)cardW, (float)cardH,
                (float)context.Px(14), (float)context.Px(14),
                Ink.Fade(Palette.CardStroke, appear),
                (float)context.Px(1.5));

            using (var labelFormat = Ink.Format(context.Px(21)))
            {
                Ink.Centred(session, label, x + (cardW / 2), top + context.Px(42) + (labelFormat.FontSize * 0.35),
                    labelFormat, Palette.StockMuted, appear);
            }

            var size = Ink.FitSize(session, value, context.Px(30), cardW - context.Px(16), bold: true);

            using (var valueFormat = Ink.Format(size, bold: true))
            {
                Ink.Centred(session, value, x + (cardW / 2), top + context.Px(92) + (valueFormat.FontSize * 0.35),
                    valueFormat, Palette.CardValue, appear);
            }
        }
    }

    private void DrawHeader(CanvasDrawingSession session, FrameContext context, double t, MatrixCell? current)
    {
        var appear = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = Title.Length > 0 ? Title : _spec.Title;

        if (ShowTitle)
        {
            var size = Ink.FitSize(session, title, context.Px(62), context.Width - context.Px(120), bold: true);

            using var format = Ink.Format(size, bold: true);

            Ink.Centred(session, title, cx, context.HeaderRow(0.155, ShowTitle), format, Palette.Title, appear);
        }

        using (var sub = Ink.Format(context.Px(25)))
        {
            Ink.Centred(session, _spec.Subtitle, cx, context.HeaderRow(0.188, ShowTitle), sub, Palette.StockMuted, appear);
        }

        using (var span = Ink.Format(context.Px(24)))
        {
            Ink.Centred(session, _spec.Span, cx, context.HeaderRow(0.218, ShowTitle), span, Palette.StockMuted, appear);
        }

        if (current is null)
        {
            return;
        }

        using (var label = Ink.Format(context.Px(36), bold: true))
        {
            Ink.Centred(session, current.Label, cx, context.HeaderRow(0.262, ShowTitle), label, Palette.Moving, appear);
        }

        var colour = Palette.Return(current.Value, AbsMax);
        var text = (current.Value > 0 ? "+" : string.Empty)
            + current.Value.ToString("0.00", CultureInfo.InvariantCulture);

        var sizeBig = Ink.FitSize(session, text, context.Px(118), context.Width - context.Px(160), bold: true);

        using (var big = Ink.Format(sizeBig, bold: true))
        {
            void Figure(CanvasDrawingSession ds) =>
                Ink.Centred(ds, text, cx, context.HeaderRow(0.330, ShowTitle), big, colour, appear);

            // shadowBlur 26 → sigma ~13.
            Ink.Glow(session, context.Px(13), 0.5, Figure);
            Figure(session);
        }

        using (var unit = Ink.Format(context.Px(26)))
        {
            Ink.Centred(session, "%", cx, context.HeaderRow(0.357, ShowTitle), unit, Palette.StockMuted, appear);
        }
    }

    private static void DrawProgress(CanvasDrawingSession session, FrameContext context)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        // The matrix's own pair: green into sky blue.
        Ink.FillHorizontal(
            session,
            new Rect(0, y, context.Width * Math.Clamp(context.Progress, 0, 1), height),
            [(0f, Rgb(0x22, 0xC5, 0x5E)), (1f, Rgb(0x0E, 0xA5, 0xE9))],
            context.Width);
    }

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}
