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
    /// The same type inked in a metal ramp: a specular highlight near the top, the chosen colour
    /// through the body, and a dark fall-off at the bottom, with a thin darker edge so the letter
    /// stands off the backdrop instead of blending into it.
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

    /// <summary>
    /// A fixed flame — orange into gold, over a deep red-brown edge, with a warm halo — the
    /// game-字幕 look for a headline that is meant to hit. Unlike <see cref="Gilded"/> and
    /// <see cref="Engraved"/>, the ramp is not derived from the reader's colour: a flame is
    /// orange whatever else the page is inked in, so the reader's colour is set aside here
    /// rather than stretched into a hue a flame never has.
    /// </summary>
    Fire = 3,

    /// <summary>
    /// Gold over a cold cyan-blue reflection — a fixed two-tone metal, the 鎏金 look. The top
    /// catches warm gold light and the lower strokes fall into a blue-green sheen, so the two
    /// halves of every glyph read as a metal reflecting two lights rather than one ramp. Like
    /// <see cref="Fire"/> the colours are fixed, not derived from the reader's choice: the
    /// whole point is the gold-blue contrast, which a hue-stretched ramp would flatten.
    /// </summary>
    Aurum = 4,

    /// <summary>
    /// White ink with a fine gold edge — the 白墨 calligraphy look: a white body, a thin gold
    /// outline, and no halo. The edge is the *light* here rather than the dark under the other
    /// skins: the glyph is white and the gold rides its outline, so the treatment reads as ink
    /// drawn on the frame rather than metal standing off it. The colours are fixed, because the
    /// white-on-gold is the whole of the effect.
    /// </summary>
    Ink = 5,

    /// <summary>
    /// Silver-white ink with a cyan-green edge and a cold glow — the 青银 look. The body is a
    /// cold silver, the outline a mint-cyan, and the halo is the cyan bleeding outwards, so the
    /// whole reads as metal lit from a cold light. Unlike <see cref="Ink"/> the glow is *on*,
    /// and it is the cyan rather than the silver that glows. Fixed colours, like the other
    /// treatments that are a whole look rather than a hue of the reader's.
    /// </summary>
    Neon = 6,
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
        TitleSkin.Fire => FireInk,
        TitleSkin.Aurum => AurumInk,
        TitleSkin.Ink => InkInk,
        TitleSkin.Neon => NeonInk,
        _ => Palette.Title,
    };

    /// <summary>
    /// The edge drawn under the ramp.
    ///
    /// Well past <see cref="Darker"/> on purpose: an edge is only an edge if it reads as one
    /// against the ramp's own dark end, and a lighter one disappears into it.
    /// </summary>
    public static Color Edge(Color ink) => Toward(ink, Black, 0.72);

    /// <summary>The edge a skin draws with: the flame's deep red-brown, the aurum's deep
    /// brown-black, the ink's gold, the neon's cyan, and the derived dark otherwise.</summary>
    public static Color EdgeFor(TitleSkin skin, Color ink) => skin switch
    {
        TitleSkin.Fire => FireEdge,
        TitleSkin.Aurum => AurumEdge,
        TitleSkin.Ink => InkEdge,
        TitleSkin.Neon => NeonEdge,
        _ => Edge(ink),
    };

    /// <summary>
    /// The ramp a skinned headline is filled with: a metal read rather than a plain two-tone.
    /// A narrow specular highlight near the top — light catching the polished edge — leads into
    /// the chosen colour through the body and a dark fall-off at the bottom. Built from the one
    /// colour the reader picked, so any hue keeps its identity at both ends.
    /// </summary>
    public static (float Position, Color Colour)[] Ramp(Color ink) => [
        (0f, Toward(ink, Black, 0.45)),
        (0.10f, Toward(ink, White, 0.78)),
        (0.26f, Toward(ink, White, 0.16)),
        (0.58f, ink),
        (0.86f, Toward(ink, Black, 0.30)),
        (1f, Toward(ink, Black, 0.45)),
    ];

    /// <summary>The ramp a skin fills its glyphs with: the fixed flame, aurum, ink or neon, and
    /// the colour-derived metal for everything else.</summary>
    public static (float Position, Color Colour)[] RampFor(TitleSkin skin, Color ink) => skin switch
    {
        TitleSkin.Fire => FireRamp,
        TitleSkin.Aurum => AurumRamp,
        TitleSkin.Ink => InkRamp,
        TitleSkin.Neon => NeonRamp,
        _ => Ramp(ink),
    };

    /// <summary>The flame's own ink — the orange the reader's colour is set aside for.</summary>
    private static readonly Color FireInk = Color.FromArgb(255, 0xFF, 0x8C, 0x1A);

    /// <summary>The flame's edge: deep red-brown, so the orange glyphs stand off a dark frame.</summary>
    private static readonly Color FireEdge = Color.FromArgb(255, 0x5A, 0x1E, 0x0A);

    /// <summary>The aurum's own ink — the gold the reader's colour is set aside for.</summary>
    private static readonly Color AurumInk = Color.FromArgb(255, 0xF5, 0xC8, 0x5A);

    /// <summary>The aurum's edge: deep brown-black, so the gold glyphs stand off a dark frame.</summary>
    private static readonly Color AurumEdge = Color.FromArgb(255, 0x3A, 0x26, 0x0E);

    /// <summary>The ink's own ink — the white the reader's colour is set aside for.</summary>
    private static readonly Color InkInk = Color.FromArgb(255, 0xF5, 0xF2, 0xE9);

    /// <summary>The ink's edge: a fine gold, drawn *over* the white rather than under it.</summary>
    private static readonly Color InkEdge = Color.FromArgb(255, 0xE8, 0xB4, 0x44);

    /// <summary>The neon's own ink — the cold silver the reader's colour is set aside for.</summary>
    private static readonly Color NeonInk = Color.FromArgb(255, 0xE8, 0xF0, 0xF2);

    /// <summary>The neon's edge: a mint-cyan, so the silver glyph reads lit from a cold light.</summary>
    private static readonly Color NeonEdge = Color.FromArgb(255, 0x3E, 0xD8, 0xBF);

    /// <summary>The neon's halo colour: the cyan the glow bleeds outwards as.</summary>
    public static readonly Color NeonGlow = Color.FromArgb(255, 0x2A, 0xB8, 0xA0);

    /// <summary>The flame ramp: a narrow gold highlight into orange, falling to ember-red at the
    /// bottom. Fixed rather than derived, because a flame does not come in the reader's hue.</summary>
    public static readonly (float Position, Color Colour)[] FireRamp =
    [
        (0f, Color.FromArgb(255, 0xE6, 0x45, 0x1F)),
        (0.12f, Color.FromArgb(255, 0xFF, 0xD8, 0x4D)),
        (0.30f, Color.FromArgb(255, 0xFF, 0xB0, 0x2E)),
        (0.58f, Color.FromArgb(255, 0xFF, 0x8C, 0x1A)),
        (0.86f, Color.FromArgb(255, 0xE8, 0x4A, 0x1F)),
        (1f, Color.FromArgb(255, 0xC4, 0x32, 0x12)),
    ];

    /// <summary>The aurum ramp: a warm gold highlight at the top falling into the cold
    /// cyan-blue reflection at the bottom — the two lights a 鎏金 metal catches. Fixed.</summary>
    public static readonly (float Position, Color Colour)[] AurumRamp =
    [
        (0f, Color.FromArgb(255, 0xFF, 0xF2, 0xB3)),
        (0.14f, Color.FromArgb(255, 0xF7, 0xD2, 0x6B)),
        (0.34f, Color.FromArgb(255, 0xE8, 0xB4, 0x44)),
        (0.52f, Color.FromArgb(255, 0xC0, 0x8E, 0x38)),
        (0.70f, Color.FromArgb(255, 0x6E, 0xA5, 0x8E)),
        (0.86f, Color.FromArgb(255, 0x3E, 0x7E, 0x7A)),
        (1f, Color.FromArgb(255, 0x2E, 0x6E, 0x6E)),
    ];

    /// <summary>The ink ramp: near-white through the body, with the faintest warm-to-cool
    /// drift so the white reads as ink rather than a flat fill — the gold edge carries the
    /// contrast, so the body stays quiet.</summary>
    public static readonly (float Position, Color Colour)[] InkRamp =
    [
        (0f, Color.FromArgb(255, 0xEF, 0xEB, 0xE0)),
        (0.30f, Color.FromArgb(255, 0xFA, 0xF7, 0xF0)),
        (0.62f, Color.FromArgb(255, 0xF8, 0xF5, 0xEE)),
        (1f, Color.FromArgb(255, 0xEB, 0xE6, 0xDA)),
    ];

    /// <summary>The neon ramp: a cold silver with the faintest cyan underlight, so the metal
    /// reads lit from the same cold light the edge and glow come from.</summary>
    public static readonly (float Position, Color Colour)[] NeonRamp =
    [
        (0f, Color.FromArgb(255, 0xD8, 0xDE, 0xE2)),
        (0.26f, Color.FromArgb(255, 0xF2, 0xF5, 0xF6)),
        (0.58f, Color.FromArgb(255, 0xEB, 0xEF, 0xF0)),
        (0.84f, Color.FromArgb(255, 0xCF, 0xD9, 0xDB)),
        (1f, Color.FromArgb(255, 0xB8, 0xC9, 0xCC)),
    ];

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
