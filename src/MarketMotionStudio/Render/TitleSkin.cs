using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// How a headline is inked. Three treatments of the same text, at the same size, in the same
/// rows: the choice is a matter of weight and of finish, never of layout, because a headline
/// that changes position when it is restyled is a headline the rows below it have to follow.
/// </summary>
public enum TitleSkin
{
    /// <summary>
    /// The type as the pages have always drawn it: one solid colour, no finish. The colour the
    /// page offers is the whole of the choice here.
    /// </summary>
    Plain = 0,

    /// <summary>
    /// The same type inked in a ramp: light at the top of the block, dark at the bottom, with a
    /// thin darker edge so the letter stands off the backdrop instead of blending into it.
    /// </summary>
    Gilded = 1,

    /// <summary>
    /// <see cref="Gilded"/>'s ramp on a serif face, set with tracking and at its own weight. The
    /// face has thick and thin strokes, so the ramp has somewhere to go: the verticals catch the
    /// light and the horizontals fall away, which a sans face cannot do.
    ///
    /// No rule between the lines, though the design had one: the block's leading is 67.2 baseline
    /// pixels against 62 of type, so the second line's glyphs start two pixels below the first
    /// line's baseline — there is no gap to put a rule in. Drawn anyway, it went *under* the
    /// second line's text and was invisible in the frame; the ramp's own darkening is what
    /// separates the lines.
    /// </summary>
    Engraved = 2,
}

/// <summary>
/// The colours a <see cref="TitleSkin"/> draws with, derived from the one the reader picked.
///
/// One colour in, four out. A ramp is not three colours somebody has to choose: it is one
/// choice and two directions, because the alternative is a palette of stops that only agrees
/// with itself for the hue it was tuned on. Darkening towards black and lightening towards
/// white keeps the hue — a green chosen for a green day stays green at both ends.
/// </summary>
public static class TitleSkins
{
    /// <summary>The colour a skin uses until the reader picks one.</summary>
    public static Color Default(TitleSkin skin) => skin switch
    {
        TitleSkin.Gilded => Palette.Moving,
        TitleSkin.Engraved => Palette.Moving,
        _ => Palette.Title,
    };

    /// <summary>The top of the ramp: the chosen colour lifted towards white.</summary>
    public static Color Lighter(Color ink) => Toward(ink, White, 0.5);

    /// <summary>The bottom of the ramp: the chosen colour pushed towards black.</summary>
    public static Color Darker(Color ink) => Toward(ink, Black, 0.42);

    /// <summary>
    /// The edge drawn under the ramp.
    ///
    /// Well past <see cref="Darker"/> on purpose: an edge is only an edge if it reads as one
    /// against the ramp's own dark end, and a lighter one disappears into it.
    /// </summary>
    public static Color Edge(Color ink) => Toward(ink, Black, 0.72);

    /// <summary>The two ends the ramp is stretched between. Windows.UI has no <c>Colors</c>,
    /// so the two the whole app would otherwise name twice are named here once.</summary>
    private static readonly Color White = Color.FromArgb(255, 255, 255, 255);

    private static readonly Color Black = Color.FromArgb(255, 0, 0, 0);

    private static Color Toward(Color ink, Color towards, double amount) => Color.FromArgb(
        ink.A,
        Mix(ink.R, towards.R, amount),
        Mix(ink.G, towards.G, amount),
        Mix(ink.B, towards.B, amount));

    private static byte Mix(byte from, byte to, double amount) =>
        (byte)Math.Clamp(Math.Round(from + ((to - from) * amount)), 0, 255);
}
