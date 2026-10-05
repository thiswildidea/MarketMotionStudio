using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Text;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The headline every page draws at the top of its frame: free text, in the frame's own large
/// type, wrapped onto at most <see cref="MaxLines"/> lines.
///
/// **Wrapping rather than shrinking** is the point. The title used to be laid out on one line and
/// scaled down until it fitted, with a floor at half size — which turns a title long enough to
/// matter into small type, and turns one long enough to hit the floor into a line that runs off
/// both edges of the frame. Breaking it instead keeps the size and spends height: a two-line
/// headline reads as a headline, and the room it costs comes out of the chart through
/// <see cref="FrameContext.HeaderRow"/>.
///
/// Typewritten line breaks are honoured as they are typed and count towards the same cap, so a
/// title can be broken where it should be broken rather than wherever the width happens to run
/// out. The cap is on the *automatic* breaks: a title someone broke into three paragraphs itself
/// keeps all three, and the reservation follows, because dropping a line a person deliberately
/// wrote is the one outcome worse than a short chart.
///
/// Measured and drawn through the same format, and the line pitch is
/// <see cref="FrameContext.TitleLineHeight"/> rather than the font's own leading — the rows below
/// are moved by that same number, so one copy of it is the difference between a second line and a
/// second line drawn on top of the subtitle.
/// </summary>
public sealed class TitleBlock
{
    /// <summary>
    /// How many lines an automatically wrapped title is allowed before the size gives way
    /// instead. Two: a headline is one line or two, and every line past the second comes out of
    /// the chart.
    /// </summary>
    public const int MaxLines = 2;

    /// <summary>
    /// Room left clear at the sides, in baseline pixels — half at each side. The title is the one
    /// element allowed to use the full frame width; this keeps it off the very edge, where a
    /// phone's own chrome and the rounded corners of a thumbnail cut into it.
    /// </summary>
    private const double SidePad = 120;

    /// <summary>
    /// The smallest size the title may be shrunk to, as a fraction of the size asked for.
    ///
    /// The floor exists because the alternative on a pasted paragraph is four-point text, which
    /// reads as a broken renderer rather than as a title that is too long. At half size it is
    /// legibly too small, which reads as "shorten this".
    /// </summary>
    private const double Floor = 0.5;

    /// <summary>How much one attempt of the shrink loop gives up.</summary>
    private const double ShrinkStep = 0.9;

    private readonly double _wanted;
    private readonly bool _bold;
    private readonly int _maxLines;
    private Cache? _memo;

    /// <param name="wantedBaselineSize">
    /// The size to draw at, in baseline pixels. Per page, because the pages' headline sizes were
    /// each tuned against their own header block.
    /// </param>
    /// <param name="bold">Whether the headline is set bold — the same on every page so far.</param>
    /// <param name="maxLines">Automatic wraps allowed before the size gives way instead.</param>
    public TitleBlock(double wantedBaselineSize, bool bold = true, int maxLines = MaxLines)
    {
        _wanted = wantedBaselineSize;
        _bold = bold;
        _maxLines = Math.Max(1, maxLines);
    }

    /// <summary>
    /// What the title came out as on this frame: the size it is drawn at (in device pixels) and
    /// how many lines it took. <see cref="Lines"/> zero means there is nothing to draw — the
    /// title is hidden or empty — and it is the number the rows below the title are moved by.
    /// </summary>
    public readonly record struct Shape(double Size, int Lines);

    /// <summary>
    /// The shape of <paramref name="text"/> on a frame this wide, or zero lines when it is hidden
    /// or empty.
    ///
    /// Memoised on the text and the width it was measured against, so the callers that need the
    /// line count — every row below the title, on every frame — do not each pay for a text
    /// layout. Those callers pass the same text every time by construction, which is why the
    /// memo is keyed on it rather than carrying a "state changed" flag somebody has to remember
    /// to set.
    /// </summary>
    public Shape For(ICanvasResourceCreator target, string text, FrameContext context, bool shown)
    {
        if (!shown)
        {
            return default;
        }

        var available = Available(context);

        // Shown but empty still reserves the row, and draws nothing in it. "Hidden" and "blank"
        // are two different choices — the first hands the row back to the chart, the second leaves
        // a band of empty frame — and collapsing them here would silently move every page that
        // leaves the text to a fallback the renderer does not know about.
        if (string.IsNullOrWhiteSpace(text))
        {
            return new Shape(context.Px(_wanted), 1);
        }

        if (_memo is { } hit && hit.Text == text && hit.Available == available)
        {
            return hit.Shape;
        }

        var shape = Resolve(target, text, context, available);

        _memo = new Cache(text, available, shape);

        return shape;
    }

    /// <summary>
    /// Draws the block, its first line's baseline at <see cref="FrameContext.TitleBaseline"/> and
    /// every line after it one <see cref="FrameContext.TitleLineHeight"/> below.
    /// </summary>
    public void Draw(
        CanvasDrawingSession session, FrameContext context, string text, Shape shape,
        Color colour, double opacity = 1)
    {
        if (shape.Lines <= 0)
        {
            return;
        }

        var available = Available(context);

        using var layout = new CanvasTextLayout(
            session, text, Format(context, shape.Size), (float)available, 0);

        // The box is as wide as the room the title has and centred in the frame; the format's own
        // centre alignment then puts the text in the middle of it, per line, which is what a
        // wrapped title has to do to read as a block rather than as a ragged edge.
        Ink.Draw(session, layout, (context.Width - available) / 2, context.TitleBaseline(0), colour, opacity);
    }

    /// <summary>The width the title is measured and drawn against, in device pixels.</summary>
    private static double Available(FrameContext context) => Math.Max(1, context.Width - context.Px(SidePad));

    /// <summary>
    /// The largest size at or above the floor at which the text wraps into no more than the cap,
    /// and the lines it comes to there.
    /// </summary>
    private Shape Resolve(ICanvasResourceCreator target, string text, FrameContext context, double available)
    {
        var size = context.Px(_wanted);
        var floor = size * Floor;

        var lines = Count(target, text, context, size, available);

        while (lines > _maxLines && size > floor)
        {
            size = Math.Max(floor, size * ShrinkStep);

            lines = Count(target, text, context, size, available);
        }

        return new Shape(size, lines);
    }

    /// <summary>
    /// How many lines the text takes at this size, measured against the width it will be drawn
    /// into rather than against the whole frame: a title laid out through a wider box than it is
    /// drawn in wraps in one place and is broken in another.
    /// </summary>
    private int Count(
        ICanvasResourceCreator target, string text, FrameContext context, double size, double available)
    {
        using var format = Format(context, size);
        using var layout = new CanvasTextLayout(target, text, format, (float)available, 0);

        // Never zero: a layout always reports at least one line, and a title that somehow reports
        // none must still be reserved for rather than drawn over the subtitle. The floor is one
        // rather than the cap because this is "what was drawn", not "what was allowed".
        return Math.Max(1, layout.LineMetrics.Length);
    }

    /// <summary>
    /// The format the title is measured and drawn in: wrapping, centred, and with the line pitch
    /// pinned to <see cref="FrameContext.TitleLineHeight"/> instead of the font's own leading.
    ///
    /// The pin is what lets the block be drawn in one call and still land on the rows
    /// <see cref="FrameContext.HeaderRow"/> moved out of the way — the alternative, drawing each
    /// line at its own baseline, needs the line breaks read back out of the layout and puts the
    /// two halves of the same decision in two places.
    /// </summary>
    private CanvasTextFormat Format(FrameContext context, double size)
    {
        var format = Ink.Format(size, _bold);

        format.WordWrapping = CanvasWordWrapping.Wrap;
        format.HorizontalAlignment = CanvasHorizontalAlignment.Center;
        format.LineSpacing = (float)context.Px(FrameContext.TitleLineHeight);
        format.LineSpacingMode = CanvasLineSpacingMode.Uniform;

        return format;
    }

    private sealed record Cache(string Text, double Available, Shape Shape);
}
