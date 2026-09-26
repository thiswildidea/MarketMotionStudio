using System.Globalization;
using AShareMotionStudio.Localization;
using AShareMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Windows.Foundation;
using Windows.UI;

namespace AShareMotionStudio.Render;

/// <summary>
/// A calendar, one block per month, cells lighting up day by day with colour standing for that
/// day's figure — of **either** measure.
///
/// The grid answers *when*, which a time axis spreads out: a heavy fortnight or a run of losses is
/// a patch of colour you can point at. That is true of turnover and of daily change alike, and the
/// two differ only in the value and its colour — so this is one renderer taking a
/// <see cref="Metric"/> rather than two nearly identical ones.
/// </summary>
public sealed class CalendarHeatmapRenderer(TurnoverSeries series, AnimationPlan plan, Metric metric)
    : TurnoverRenderer(series, plan, metric)
{
    /// <summary>
    /// Monday to Friday only — five columns, not seven.
    ///
    /// A-shares do not trade at weekends, so two of seven columns would always be empty while
    /// costing every cell nearly a third of its width. On a phone-sized frame that is the
    /// difference between a readable grid and a mosaic.
    /// </summary>
    private const int Columns = 5;

    /// <summary>The most calendar weeks a single month can straddle.</summary>
    private const int Weeks = 6;

    /// <summary>The most month-blocks to put side by side. Beyond four, cells stop being legible.</summary>
    private const int MostBlockColumns = 4;

    protected override (int Index, double Value) DrawPlot(
        CanvasDrawingSession session, FrameContext context, double t)
    {
        var layout = Layout(context);
        var moving = DrawCells(session, context, t, layout);

        // The marker colours stay yellow and blue even on the return calendar, where the cells are
        // red and green. Boxing a red cell in red would make the box disappear into it; the marker
        // has to contrast with whatever it is marking rather than agree with it.
        var extremes = Metric.Extremes(Series);
        var colours = new[] { Palette.Moving, Palette.MarkLow };
        var delays = new[] { 350.0, 1000.0 };

        for (var i = 0; i < extremes.Length && i < colours.Length; i++)
        {
            MarkDay(session, context, t, layout, extremes[i].Index, extremes[i].Label, colours[i], delays[i]);
        }

        return moving;
    }

    /// <summary>One month's block: where it sits and which days belong to it.</summary>
    private sealed record Block(int Year, int Month, List<int> Days)
    {
        public double X { get; set; }

        public double Y { get; set; }

        public double TitleHeight { get; set; }

        /// <summary>Which column the first of the month falls in, 0 being Monday.</summary>
        public int FirstColumn { get; set; }
    }

    private sealed record CalendarLayout(List<Block> Blocks, double Cell);

    /// <summary>
    /// Groups the series into month blocks and works out how big the cells can be.
    ///
    /// The block column count is **searched, not decided by a rule**: every count from one to four
    /// is tried and whichever yields the largest cell wins. On a portrait frame height is the
    /// binding constraint, so the best arrangement depends on how many months there are in a way
    /// no fixed rule captures — three months land on two columns, six on four columns of two rows,
    /// a year on four columns of four rows, and nobody has to choose.
    /// </summary>
    private CalendarLayout Layout(FrameContext context)
    {
        var blocks = new List<Block>();

        // The series is ascending, so a month ends when the next date's month differs. Grouping by
        // a key over the whole list would work too, but this keeps the blocks in date order without
        // a sort.
        foreach (var (date, i) in Series.Dates.Select((d, i) => (d, i)))
        {
            var last = blocks.Count > 0 ? blocks[^1] : null;

            if (last is null || last.Year != date.Year || last.Month != date.Month)
            {
                blocks.Add(new Block(date.Year, date.Month, [i]));
            }
            else
            {
                last.Days.Add(i);
            }
        }

        var left = context.ChartLeft;
        var width = context.ChartWidth;
        var top = Row(context, PlotTopFraction);
        var gridHeight = Math.Max(1, context.BaselineAbove(CreditGap) - top);

        var best = (Cell: 0.0, Columns: 1, Rows: blocks.Count, BlockWidth: width, BlockHeight: gridHeight, TitleHeight: 0.0);

        for (var c = 1; c <= MostBlockColumns; c++)
        {
            var rows = (int)Math.Ceiling((double)blocks.Count / c);
            var blockWidth = width / c;
            var blockHeight = gridHeight / rows;
            var titleHeight = Math.Min(context.Px(44), blockHeight * 0.16);

            // The 1.1 rows of slack are the weekday header line; the 18 and 8 are breathing room
            // inside the block so neighbouring months do not touch.
            var cell = Math.Min(
                (blockWidth - context.Px(18)) / Columns,
                (blockHeight - titleHeight - context.Px(8)) / (Weeks + 1.1));

            if (cell > best.Cell)
            {
                best = (cell, c, rows, blockWidth, blockHeight, titleHeight);
            }
        }

        var usedHeight = best.Rows * best.BlockHeight;

        for (var i = 0; i < blocks.Count; i++)
        {
            var column = i % best.Columns;
            var row = i / best.Columns;

            blocks[i].X = left + (column * best.BlockWidth) + ((best.BlockWidth - (best.Cell * Columns)) / 2);
            blocks[i].Y = top + ((gridHeight - usedHeight) / 2) + (row * best.BlockHeight);
            blocks[i].TitleHeight = best.TitleHeight;
            blocks[i].FirstColumn = MondayIndex(new DateOnly(blocks[i].Year, blocks[i].Month, 1).DayOfWeek);
        }

        return new CalendarLayout(blocks, best.Cell);
    }

    /// <summary>Monday as 0 through Sunday as 6, which is how the grid is laid out.</summary>
    private static int MondayIndex(DayOfWeek day) => ((int)day + 6) % 7;

    /// <summary>
    /// Which cell a date occupies within its block.
    /// </summary>
    /// <remarks>
    /// The week index is computed on a seven-day week even though only five columns are drawn.
    /// That is deliberate and not an inconsistency: the row a date lands on depends on how many
    /// *calendar* weeks have passed, weekends included, so switching the arithmetic to five would
    /// pull dates into the wrong rows the moment a month started on a Thursday.
    /// </remarks>
    private static (int Column, int Week) CellOf(DateOnly date, int firstColumn) =>
        (MondayIndex(date.DayOfWeek), (date.Day - 1 + firstColumn) / 7);

    private (int Index, double Value) DrawCells(
        CanvasDrawingSession session, FrameContext context, double t, CalendarLayout layout)
    {
        var cell = layout.Cell;
        var gap = Math.Max(2 * context.Scale, cell * 0.08);
        var values = Metric.Values(Series);
        var index = -1;
        var value = 0.0;

        foreach (var block in layout.Blocks)
        {
            // The block's own frame arrives slightly *before* its first day, so the month has a
            // grid to land in rather than a cell appearing in empty space.
            var blockAlpha = Easing.Ramp(t, Plan.IntroMs + (block.Days[0] * Plan.StaggerMs) - 400, 500);

            if (blockAlpha <= 0)
            {
                continue;
            }

            DrawBlockChrome(session, context, block, cell, blockAlpha);

            foreach (var i in block.Days)
            {
                var startsAt = Plan.IntroMs + (i * Plan.StaggerMs);

                // Not `break` as in the bar form: cells within a block are not in a single visual
                // run, so skipping one that has not started is not a reason to stop the block.
                if (t <= startsAt)
                {
                    continue;
                }

                var raw = Math.Clamp((t - startsAt) / Plan.BarMs, 0, 1);
                var (column, week) = CellOf(Series.Dates[i], block.FirstColumn);

                if (column >= Columns)
                {
                    // A trading day at the weekend should not exist. If the source ever returns
                    // one, dropping it is better than drawing it outside the grid.
                    continue;
                }

                var x = block.X + (column * cell);
                var y = block.Y + block.TitleHeight + (cell * 1.1) + (week * cell);
                var colour = Metric.Colour(Series, i);

                // Grows from just over half size as it fades in, so a cell arrives rather than
                // appears. Both curves are monotonic — a cell that overshot its own size would
                // read as a click.
                var scale = 0.55 + (0.45 * Easing.OutCubic(raw));
                var size = (cell - gap) * scale;
                var offset = (cell - gap - size) / 2;
                var alpha = blockAlpha * (0.25 + (0.75 * raw));

                var box = new Rect(x + (gap / 2) + offset, y + (gap / 2) + offset, size, size);
                var radius = (float)Math.Max(2 * context.Scale, cell * 0.16);

                if (raw < 1)
                {
                    Ink.Glow(session, context.Px(9), 0.9 * blockAlpha,
                        ds => ds.FillRoundedRectangle(box, radius, radius, colour));
                    index = i;
                    value = values[i];
                }

                session.FillRoundedRectangle(box, radius, radius, Ink.Fade(colour, alpha * 0.95));

                if (raw >= 1 && i > index)
                {
                    index = i;
                    value = values[i];
                }
            }
        }

        return (index, value);
    }

    /// <summary>A block's month name and its weekday header row.</summary>
    private static void DrawBlockChrome(
        CanvasDrawingSession session, FrameContext context, Block block, double cell, double alpha)
    {
        // The short month name from the *interface's* culture, so this reads "6月" in a Chinese
        // frame and "Jun" in an English one without a resource string per month. Strings.Culture
        // rather than CurrentCulture: the latter follows the operating system, not the language
        // the app is showing, and produced "Jun" inside a Chinese frame.
        var month = new DateOnly(block.Year, block.Month, 1)
            .ToString("MMM", Strings.Culture);

        var titleSize = Math.Clamp(block.TitleHeight / context.Scale * 0.72, 16, 34);

        using (var format = Ink.Format(context.Px(titleSize), bold: true))
        {
            Ink.Left(session, month, block.X, block.Y + (block.TitleHeight * 0.85), format, Palette.MonthLabel, alpha);
        }

        using var headFormat = Ink.Format(context.Px(Math.Clamp(cell / context.Scale * 0.42, 12, 22)));

        // Taken from the culture rather than hard-coded, and started at Monday to match the grid.
        var names = Strings.Culture.DateTimeFormat.ShortestDayNames;

        for (var c = 0; c < Columns; c++)
        {
            var day = (DayOfWeek)(((c + 1) % 7));

            Ink.Centred(
                session, names[(int)day],
                block.X + (c * cell) + (cell / 2),
                block.Y + block.TitleHeight + (cell * 0.72),
                headFormat, Palette.Credit, alpha);
        }
    }

    /// <summary>Boxes one day's cell during the closing stretch.</summary>
    private void MarkDay(
        CanvasDrawingSession session, FrameContext context, double t, CalendarLayout layout,
        int index, string label, Color colour, double delayMs)
    {
        var a = Easing.Ramp(t, Plan.FinaleStartMs + delayMs, 650);

        if (a <= 0)
        {
            return;
        }

        var block = layout.Blocks.FirstOrDefault(b => b.Days.Contains(index));

        if (block is null)
        {
            return;
        }

        var (column, week) = CellOf(Series.Dates[index], block.FirstColumn);

        if (column >= Columns)
        {
            return;
        }

        var cell = layout.Cell;
        var x = block.X + (column * cell);
        var y = block.Y + block.TitleHeight + (cell * 1.1) + (week * cell);
        var inset = context.Scale;
        var radius = (float)Math.Max(3 * context.Scale, cell * 0.18);

        session.DrawRoundedRectangle(
            new Rect(x + inset, y + inset, cell - (2 * inset), cell - (2 * inset)),
            radius, radius, Ink.Fade(colour, a), (float)context.Px(3));

        using var format = Ink.Format(context.Px(20), bold: true);

        Ink.Centred(session, label, x + (cell / 2), y - context.Px(6), format, colour, a);
    }
}
