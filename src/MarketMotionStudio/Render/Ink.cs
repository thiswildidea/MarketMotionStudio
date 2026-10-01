using System.Numerics;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Effects;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// Text drawing that positions by the alphabetic baseline, the way a canvas does.
///
/// This exists because Win2D and HTML canvas disagree about what a text position means.
/// `ctx.fillText(s, x, y)` puts the *baseline* at y, and with `textAlign = 'center'`
/// puts the centre of the text at x. Win2D's `DrawText` places the top-left of the
/// layout box instead. Porting positions across without accounting for that moves every
/// line down by roughly its ascent — about a fifth of the font size — which on a title
/// block of five stacked lines is enough to crowd them together and looks like the
/// spacing was never tuned.
///
/// Measuring a <see cref="CanvasTextLayout"/> gives the ascent exactly, so these
/// helpers take the coordinates the source used and put the text where it did.
/// </summary>
public static class Ink
{
    /// <summary>
    /// Windows ships this and it carries the CJK glyphs these frames are full of. Named
    /// once because a font fallback that differs between two call sites is a layout that
    /// differs between two lines of the same block.
    /// </summary>
    public const string Family = "Microsoft YaHei";

    public static CanvasTextFormat Format(double sizeInPixels, bool bold = false) => new()
    {
        FontFamily = Family,
        FontSize = (float)sizeInPixels,
        FontWeight = bold ? Microsoft.UI.Text.FontWeights.Bold : Microsoft.UI.Text.FontWeights.Normal,
        WordWrapping = CanvasWordWrapping.NoWrap,
        HorizontalAlignment = CanvasHorizontalAlignment.Left,
        VerticalAlignment = CanvasVerticalAlignment.Top,
    };

    /// <summary>Natural width of a string in a format, for centring and fitting.</summary>
    public static double Measure(ICanvasResourceCreator target, string text, CanvasTextFormat format)
    {
        using var layout = new CanvasTextLayout(target, text, format, 0, 0);
        return layout.LayoutBounds.Width;
    }

    /// <summary>
    /// How far the next run of a line starts after this one — the width of the text
    /// *including* the spaces it ends with.
    ///
    /// <see cref="Measure"/> cannot answer this, because a text layout's bounds
    /// exclude trailing whitespace: a run written as <c>"开 "</c> measures as
    /// <c>"开"</c>. Runs were separated by putting a space at the end of the one
    /// before, so every separator was measured as absent — and the line came out with
    /// no gaps at all, which on a run of CJK labels and figures reads as each label
    /// printed over the number before it rather than as a spacing that was never
    /// tuned. Nothing catches it: the wide pages that use this carry Latin text and a
    /// middle dot, and there a missing gap just looks tight.
    ///
    /// The width is taken against a sentinel, which gives the spaces something to sit
    /// in front of, and the sentinel's own width comes back off. Kerning between a
    /// space and a box-drawing character is nothing to correct for.
    /// </summary>
    private static double Advance(ICanvasResourceCreator target, string text, CanvasTextFormat format)
    {
        if (text.Length == 0)
        {
            return 0;
        }

        if (!char.IsWhiteSpace(text[^1]))
        {
            return Measure(target, text, format);
        }

        const string Sentinel = "\u2502";

        return Measure(target, text + Sentinel, format) - Measure(target, Sentinel, format);
    }

    /// <summary>Centred horizontally on <paramref name="cx"/>, baseline at <paramref name="baselineY"/>.</summary>
    public static void Centred(
        CanvasDrawingSession session, string text, double cx, double baselineY,
        CanvasTextFormat format, Color colour, double opacity = 1)
    {
        using var layout = new CanvasTextLayout(session, text, format, 0, 0);
        Draw(session, layout, cx - (layout.LayoutBounds.Width / 2), baselineY, colour, opacity);
    }

    /// <summary>Left edge at <paramref name="x"/>, baseline at <paramref name="baselineY"/>.</summary>
    public static void Left(
        CanvasDrawingSession session, string text, double x, double baselineY,
        CanvasTextFormat format, Color colour, double opacity = 1)
    {
        using var layout = new CanvasTextLayout(session, text, format, 0, 0);
        Draw(session, layout, x, baselineY, colour, opacity);
    }

    /// <summary>
    /// Right edge at <paramref name="rightX"/>, vertically centred on
    /// <paramref name="middleY"/> — the axis-label convention, which uses a middle
    /// baseline rather than an alphabetic one.
    /// </summary>
    public static void RightMiddle(
        CanvasDrawingSession session, string text, double rightX, double middleY,
        CanvasTextFormat format, Color colour, double opacity = 1)
    {
        using var layout = new CanvasTextLayout(session, text, format, 0, 0);
        var bounds = layout.LayoutBounds;

        session.DrawTextLayout(
            layout,
            (float)(rightX - bounds.Width),
            (float)(middleY - (bounds.Height / 2)),
            Fade(colour, opacity));
    }

    /// <summary>
    /// Left edge at <paramref name="x"/>, vertically centred on <paramref name="middleY"/> —
    /// a value label following the end of a bar, which sits on the bar's centre line.
    /// </summary>
    public static void LeftAt(
        CanvasDrawingSession session, string text, double x, double middleY,
        CanvasTextFormat format, Color colour, double opacity = 1)
    {
        using var layout = new CanvasTextLayout(session, text, format, 0, 0);

        session.DrawTextLayout(
            layout,
            (float)x,
            (float)(middleY - (layout.LayoutBounds.Height / 2)),
            Fade(colour, opacity));
    }

    /// <summary>
    /// One line built from runs of different colour, size and weight, centred as a whole.
    ///
    /// Measured in full before anything is drawn. Centring each run on its own would
    /// stack them; laying them out left to right from an assumed centre would shift the
    /// line whenever one run's width changed — and the run that changes here is a count
    /// of trading days, which changes with every fetch.
    ///
    /// Each run is advanced by its width with trailing spaces counted — see
    /// <see cref="Advance"/>. Runs are separated by writing the space into the run
    /// before, so measuring without it lays the line out with no gaps at all.
    /// </summary>
    public static void Runs(
        CanvasDrawingSession session, IReadOnlyList<(string Text, Color Colour, CanvasTextFormat Format)> runs,
        double cx, double baselineY, double opacity = 1)
    {
        var layouts = new CanvasTextLayout[runs.Count];
        var advances = new double[runs.Count];
        var total = 0.0;

        try
        {
            for (var i = 0; i < runs.Count; i++)
            {
                layouts[i] = new CanvasTextLayout(session, runs[i].Text, runs[i].Format, 0, 0);
                advances[i] = Advance(session, runs[i].Text, runs[i].Format);
                total += advances[i];
            }

            var x = cx - (total / 2);

            for (var i = 0; i < runs.Count; i++)
            {
                Draw(session, layouts[i], x, baselineY, runs[i].Colour, opacity);
                x += advances[i];
            }
        }
        finally
        {
            foreach (var layout in layouts)
            {
                layout?.Dispose();
            }
        }
    }

    /// <summary>
    /// The largest size at or below <paramref name="wanted"/> that fits
    /// <paramref name="available"/>, never below half.
    ///
    /// The floor is what stops a pasted paragraph shrinking to illegibility: at half size
    /// it is visibly too small, which reads as "shorten this", where four-point text reads
    /// as a broken renderer.
    /// </summary>
    public static double FitSize(
        ICanvasResourceCreator target, string text, double wanted, double available, bool bold)
    {
        using var format = Format(wanted, bold);
        var natural = Measure(target, text, format);

        return natural <= 0 || natural <= available
            ? wanted
            : wanted * Math.Max(0.5, available / natural);
    }

    /// <summary>
    /// One formatted line where a single substring is picked out in another colour.
    ///
    /// Takes the finished sentence and locates the highlighted run inside it, rather than
    /// asking translators for a prefix and a suffix. That matters for word order: several
    /// languages put the count before the noun it counts, and a prefix-plus-suffix pair
    /// forces a translator to either mangle the grammar or leave one of the two empty.
    /// A substring search does not care where in the sentence the number landed.
    ///
    /// If the highlight is not found the line is drawn in one colour, which is a legible
    /// outcome rather than a missing line.
    /// </summary>
    public static void Highlighted(
        CanvasDrawingSession session, string full, string highlight,
        Color baseColour, Color highlightColour,
        CanvasTextFormat plain, CanvasTextFormat strong,
        double cx, double baselineY, double opacity = 1)
    {
        var at = highlight.Length == 0 ? -1 : full.IndexOf(highlight, StringComparison.Ordinal);

        if (at < 0)
        {
            Centred(session, full, cx, baselineY, plain, baseColour, opacity);
            return;
        }

        var runs = new List<(string, Color, CanvasTextFormat)>(3);

        if (at > 0)
        {
            runs.Add((full[..at], baseColour, plain));
        }

        runs.Add((highlight, highlightColour, strong));

        var after = at + highlight.Length;

        if (after < full.Length)
        {
            runs.Add((full[after..], baseColour, plain));
        }

        Runs(session, runs, cx, baselineY, opacity);
    }

    private static void Draw(
        CanvasDrawingSession session, CanvasTextLayout layout, double x, double baselineY,
        Color colour, double opacity)
    {
        // LineMetrics carries the ascent, so the top of the box is the baseline minus it.
        // This is the whole point of the class: it converts a canvas baseline coordinate
        // into the box coordinate Win2D wants.
        var ascent = layout.LineMetrics.Length > 0 ? layout.LineMetrics[0].Baseline : layout.LayoutBounds.Height;

        session.DrawTextLayout(layout, (float)x, (float)(baselineY - ascent), Fade(colour, opacity));
    }

    /// <summary>
    /// Applies an animation's fade to a colour.
    ///
    /// Done on the colour rather than through a layer opacity because every call here
    /// draws one element that is fading on its own schedule. A layer would fade whatever
    /// else happened to be inside it.
    /// </summary>
    public static Color Fade(Color colour, double opacity) => opacity >= 1
        ? colour
        : Color.FromArgb((byte)Math.Clamp(colour.A * opacity, 0, 255), colour.R, colour.G, colour.B);

    /// <summary>
    /// Fills a rectangle with a gradient running top to bottom.
    ///
    /// Here rather than in <see cref="Palette"/> so the palette stays a list of colours with
    /// no drawing dependency, and here rather than in each renderer so the frame background
    /// is built once — three copies of the same stop list is three places for one of them to
    /// end up a shade out.
    /// </summary>
    public static void FillVertical(
        CanvasDrawingSession session, Rect box, (float Position, Color Colour)[] stops)
    {
        using var brush = Brush(session, stops, new Vector2((float)box.X, (float)box.Y),
            new Vector2((float)box.X, (float)(box.Y + box.Height)));

        session.FillRectangle(box, brush);
    }

    /// <summary>Fills a rectangle with a gradient running left to right.</summary>
    public static void FillHorizontal(
        CanvasDrawingSession session, Rect box, (float Position, Color Colour)[] stops, double spanWidth)
    {
        // The gradient is measured across spanWidth rather than across the box, so a partly
        // filled bar shows the colours it has reached rather than compressing the whole ramp
        // into whatever is drawn so far.
        using var brush = Brush(session, stops, new Vector2((float)box.X, (float)box.Y),
            new Vector2((float)(box.X + spanWidth), (float)box.Y));

        session.FillRectangle(box, brush);
    }

    private static CanvasLinearGradientBrush Brush(
        CanvasDrawingSession session, (float Position, Color Colour)[] stops, Vector2 from, Vector2 to) =>
        new(session, [.. stops.Select(s => new CanvasGradientStop { Position = s.Position, Color = s.Colour })])
        {
            StartPoint = from,
            EndPoint = to,
        };

    /// <summary>
    /// A soft halo behind whatever <paramref name="draw"/> draws — the equivalent of a
    /// canvas `shadowBlur`.
    /// </summary>
    /// <remarks>
    /// Win2D has no shadow property on the session, so this records the shape into a
    /// <see cref="CanvasCommandList"/> and puts a real Gaussian blur over it. The first
    /// attempt here avoided the effect graph by stacking concentric translucent rectangles,
    /// which is cheaper and was wrong in a way that only showed at size: behind a
    /// 128-pixel number it read as a distinct lighter box rather than as a glow. A halo has
    /// to follow the shape's outline, and for text that means blurring the glyphs.
    ///
    /// <paramref name="blurRadius"/> is a Gaussian sigma, which is about half a canvas
    /// `shadowBlur` — so a source value of 24 comes in here as 12.
    /// </remarks>
    public static void Glow(
        CanvasDrawingSession session, double blurRadius, double strength, Action<CanvasDrawingSession> draw)
    {
        if (strength <= 0 || blurRadius <= 0)
        {
            return;
        }

        using var recorded = new CanvasCommandList(session);

        using (var recording = recorded.CreateDrawingSession())
        {
            draw(recording);
        }

        using var blur = new GaussianBlurEffect
        {
            Source = recorded,
            BlurAmount = (float)blurRadius,

            // Soft, so the halo fades out at the edge of its own bounds instead of being
            // clipped to them — a hard cut is what made the rectangle version look like a box.
            BorderMode = EffectBorderMode.Soft,
        };

        using var faded = new OpacityEffect { Source = blur, Opacity = (float)Math.Clamp(strength, 0, 1) };

        // The command list recorded absolute coordinates, so this composites in place.
        session.DrawImage(faded);
    }
}
