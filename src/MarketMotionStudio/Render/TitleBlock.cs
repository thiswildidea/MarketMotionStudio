using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Effects;
using Microsoft.Graphics.Canvas.Text;
using System.Numerics;
using Windows.Foundation;
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

    /// <summary>
    /// The serif <see cref="TitleSkin.Engraved"/> is set in.
    ///
    /// Song rather than the prettier STSong: <c>SimSun</c> ships with Windows, while
    /// <c>STSong</c> mostly arrives with Office, and a headline that is a different face on a
    /// machine without Office is not a choice the reader made. At headline size the two are hard
    /// to tell apart.
    /// </summary>
    private const string Serif = "SimSun";

    /// <summary>
    /// Extra room between characters in <see cref="TitleSkin.Engraved"/>, in baseline pixels.
    /// Tracking, not a wider box: a serif at this size reads as cramped without air between the
    /// glyphs, and the block is centred either way.
    /// </summary>
    private const double Tracking = 4;

    /// <summary>How far the faux outline's offsets reach, as a fraction of the type size.</summary>
    private const double EdgeReach = 0.022;

    /// <summary>The eight directions an outline is drawn in, as unit vectors.</summary>
    private static readonly (double X, double Y)[] Ring =
        [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)];

    private readonly double _wanted;
    private readonly bool _bold;
    private readonly int _maxLines;
    private readonly TitleSkin _skin;
    private Cache? _memo;

    /// <param name="wantedBaselineSize">
    /// The size to draw at, in baseline pixels. Per page, because the pages' headline sizes were
    /// each tuned against their own header block.
    /// </param>
    /// <param name="bold">Whether the headline is set bold — the same on every page so far.</param>
    /// <param name="maxLines">Automatic wraps allowed before the size gives way instead.</param>
    /// <param name="skin">How the type is inked. <see cref="TitleSkin.Plain"/> is what the pages
    /// shipped with, and it is the only one that leaves the face and the finish alone.</param>
    public TitleBlock(
        double wantedBaselineSize, bool bold = true, int maxLines = MaxLines,
        TitleSkin skin = TitleSkin.Plain)
    {
        _wanted = wantedBaselineSize;
        _bold = bold;
        _maxLines = Math.Max(1, maxLines);
        _skin = skin;
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

        // The skin decides the typeface — the serif tracks wider — so the line count it settles
        // can change with it. Keyed on the skin, not only the text and width, so a global change
        // while the page is open does not hand back a stale count.
        var skin = EffectiveSkin();

        if (_memo is { } hit && hit.Text == text && hit.Available == available && hit.Skin == skin)
        {
            return hit.Shape;
        }

        var shape = Resolve(target, text, context, available, skin);

        _memo = new Cache(text, available, skin, shape);

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

        // Which treatment and ink this draw uses. The skin is the page's own when the page passed
        // one — the portfolio page keeps its per-page choice — otherwise it is the global setting,
        // read here at draw time so a change in Settings reaches every page's next redraw without a
        // restart. The ink follows the same ownership rule.
        var skin = EffectiveSkin();
        var ink = ResolveInk(colour);

        var available = Available(context);

        using var layout = Layout(session, text, context, shape.Size, skin);

        // The box is as wide as the room the title has and centred in the frame; the format's own
        // centre alignment then puts the text in the middle of it, per line, which is what a
        // wrapped title has to do to read as a block rather than as a ragged edge.
        var left = (context.Width - available) / 2;
        var baseline = context.TitleBaseline(0);

        if (skin is TitleSkin.Plain)
        {
            Ink.Draw(session, layout, left, baseline, ink, opacity);

            return;
        }

        Painted(session, context, layout, shape.Size, left, baseline, ink, opacity);
    }

    /// <summary>
    /// The headline filled with a ramp rather than a colour, and edged so it stands off the
    /// backdrop.
    ///
    /// Win2D fills text with a colour; it has no brush for it. The ramp therefore goes down in
    /// three steps: the glyphs are drawn once into a command list as a mask, the ramp is filled
    /// into a second one over the mask's own rectangle, and the two are composited
    /// <c>SourceIn</c> — the ramp, cut to the ink. The edge underneath is the same glyphs drawn
    /// at a ring of small offsets in the darker end of the same ramp, which is what a stroke is
    /// when the only thing a canvas can do with text is fill it.
    /// </summary>
    private void Painted(
        CanvasDrawingSession session, FrameContext context, CanvasTextLayout layout, double size,
        double left, double baseline, Color colour, double opacity)
    {
        var ascent = layout.LineMetrics.Length > 0
            ? layout.LineMetrics[0].Baseline
            : layout.LayoutBounds.Height;

        // The layout's top edge: where the first line's box begins, not its baseline.
        var top = baseline - ascent;

        using var edge = Edge(session, layout, size, left, top, colour);

        using var art = new CanvasCommandList(session);

        using (var drawing = art.CreateDrawingSession())
        {
            // Edge first, so the glyph stands off the backdrop rather than blending into it.
            drawing.DrawImage(edge);

            // The glyphs filled with a metal ramp, drawn straight from a gradient brush. No
            // off-screen mask and no `SourceIn` composite — that composite aligned its two inputs
            // by their own bounds, which left the top of every glyph showing only the edge and
            // read as "covered". Drawing the text with a brush pins the ramp to the layout's own
            // box, so the whole glyph takes the gradient and nothing is left to the edge alone.
            using var brush = new CanvasLinearGradientBrush(session,
                [.. TitleSkins.Ramp(colour).Select(s => new CanvasGradientStop { Position = s.Position, Color = s.Colour })])
            {
                StartPoint = new Vector2(0, (float)top),
                EndPoint = new Vector2(0, (float)(top + layout.LayoutBounds.Height)),
            };

            drawing.DrawTextLayout(layout, (float)left, (float)top, brush);
        }

        // The halo is the ramp's own colour bleeding outwards, which is most of what makes a
        // metal read as metal rather than as coloured type. The same glow the page draws its
        // headline figure with, at a third of the strength.
        Ink.Glow(session, context.Px(10), 0.34 * opacity, drawing => drawing.DrawImage(art));

        using var faded = new OpacityEffect { Source = art, Opacity = (float)Math.Clamp(opacity, 0, 1) };

        session.DrawImage(faded);
    }

    /// <summary>
    /// The outline under the ramp: the glyphs at eight directions and two radii, in the darkest
    /// step of the same colour.
    /// </summary>
    private static CanvasCommandList Edge(
        CanvasDrawingSession session, CanvasTextLayout layout, double size, double left, double top, Color colour)
    {
        var list = new CanvasCommandList(session);
        var ink = TitleSkins.Edge(colour);
        var reach = Math.Max(0.55, size * EdgeReach);

        using (var drawing = list.CreateDrawingSession())
        {
            foreach (var radius in new[] { reach, reach * 0.55 })
            {
                foreach (var (x, y) in Ring)
                {
                    drawing.DrawTextLayout(layout, (float)(left + (x * radius)), (float)(top + (y * radius)), ink);
                }
            }
        }

        return list;
    }

    /// <summary>The width the title is measured and drawn against, in device pixels.</summary>
    private static double Available(FrameContext context) => Math.Max(1, context.Width - context.Px(SidePad));

    /// <summary>
    /// The treatment this draw uses: the page's own when the page passed one — the
    /// portfolio page keeps its per-page choice — otherwise the global setting.
    /// </summary>
    private TitleSkin EffectiveSkin() =>
        _skin != TitleSkin.Plain ? _skin : TitleSettings.Skin;

    /// <summary>
    /// The ink this draw uses, following the same ownership rule as the skin.
    ///
    /// A page that passed its own skin keeps the colour its page already resolved from
    /// its own preference. A page relying on the global setting uses the chosen colour
    /// when one is set, and otherwise the treatment's own default — which is white for
    /// Plain (so a page that never opted in is unchanged) and the skin's amber for the
    /// metal treatments.
    /// </summary>
    private Color ResolveInk(Color passed)
    {
        if (_skin != TitleSkin.Plain)
        {
            return passed;
        }

        if (TitleSettings.Colour is { } chosen)
        {
            return chosen;
        }

        var skin = TitleSettings.Skin;

        return skin == TitleSkin.Plain ? passed : TitleSkins.Default(skin);
    }

    /// <summary>
    /// The title laid out for measuring and for drawing, through the same code — a measurement
    /// taken through a different layout than the one drawn is a line count that disagrees with
    /// the picture.
    /// </summary>
    private CanvasTextLayout Layout(
        ICanvasResourceCreator target, string text, FrameContext context, double size, TitleSkin skin)
    {
        var layout = new CanvasTextLayout(target, text, Format(context, size, skin), (float)Available(context), 0);

        // Tracking is a property of the layout, not of the format: DirectWrite carries it per
        // character range. Half either side, so a tracked headline stays centred — spacing added
        // only after each glyph would shove the whole line to the left by the width of the gaps.
        if (skin is TitleSkin.Engraved)
        {
            var half = (float)(context.Px(Tracking) / 2);

            layout.SetCharacterSpacing(0, text.Length, half, half, 0f);
        }

        return layout;
    }

    /// <summary>
    /// The largest size at or above the floor at which the text wraps into no more than the cap,
    /// and the lines it comes to there.
    /// </summary>
    private Shape Resolve(ICanvasResourceCreator target, string text, FrameContext context, double available, TitleSkin skin)
    {
        var size = context.Px(_wanted);
        var floor = size * Floor;

        var lines = Count(target, text, context, size, available, skin);

        while (lines > _maxLines && size > floor)
        {
            size = Math.Max(floor, size * ShrinkStep);

            lines = Count(target, text, context, size, available, skin);
        }

        return new Shape(size, lines);
    }

    /// <summary>
    /// How many lines the text takes at this size, measured against the width it will be drawn
    /// into rather than against the whole frame: a title laid out through a wider box than it is
    /// drawn in wraps in one place and is broken in another.
    /// </summary>
    private int Count(
        ICanvasResourceCreator target, string text, FrameContext context, double size, double available, TitleSkin skin)
    {
        using var layout = Layout(target, text, context, size, skin);

        // Never zero: a layout always reports at least one line, and a title that somehow reports
        // none must still be reserved for rather than drawn over the subtitle. The floor is one
        // rather than the cap because this is "what was drawn", not "what was allowed".
        return Math.Max(1, layout.LineMetrics.Length);
    }

    /// <summary>
    /// The format the title is measured and drawn in: wrapping, centred, and with the line pitch
    /// pinned to <see cref="FrameContext.TitleLineHeight"/> instead of the font's own leading.
    /// </summary>
    private CanvasTextFormat Format(FrameContext context, double size, TitleSkin skin)
    {
        var engraved = skin is TitleSkin.Engraved;

        // The serif is set at its own weight: synthetic bold on Song fills in the thin
        // horizontals, which are the one thing the face was chosen for.
        var format = Ink.Format(size, _bold && !engraved, engraved ? Serif : null);

        format.WordWrapping = CanvasWordWrapping.Wrap;
        format.HorizontalAlignment = CanvasHorizontalAlignment.Center;
        format.LineSpacing = (float)context.Px(FrameContext.TitleLineHeight);
        format.LineSpacingMode = CanvasLineSpacingMode.Uniform;

        return format;
    }

    private sealed record Cache(string Text, double Available, TitleSkin Skin, Shape Shape);
}
