using System.Numerics;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The bull and the bear that ride the leading end of a holding's line: a round badge with a
/// face in it, red while the holding is climbing and green while it is falling.
///
/// **Drawn, not loaded.** These are the same kind of shape as the navigation icons — a handful
/// of circles and two curved strokes — so they are built here out of Win2D primitives rather
/// than shipped as pictures. That keeps them sharp at any export size, lets their colour come
/// from the same two constants the rest of the frame uses (<see cref="Palette.Emphasis"/> for a
/// rise and the cooling green a fall is drawn in), and means nothing has to be added to the
/// package or fetched on a background thread.
///
/// Everything is expressed as a fraction of the badge's radius, so the caller chooses how big
/// the badge is and the face keeps its proportions. The features that carry the read — the
/// bull's horns and the bear's ears — are deliberately oversized, because a frame is watched as
/// video at whatever size the player happens to be, and at seventy pixels a faithful bull would
/// be a smudge.
/// </summary>
public static class Mascots
{
    /// <summary>
    /// One badge, the face chosen by which way the holding has been going.
    /// </summary>
    /// <param name="rising">True for the bull, false for the bear.</param>
    /// <param name="up">The colour a rise is drawn in — the frame's own gain colour.</param>
    /// <param name="down">The colour a fall is drawn in — the frame's own loss colour.</param>
    /// <param name="opacity">The fade the whole badge is drawn at, for its entrance.</param>
    public static void Draw(
        CanvasDrawingSession session, float cx, float cy, float radius,
        bool rising, Color up, Color down, double opacity)
    {
        if (radius <= 0 || opacity <= 0)
        {
            return;
        }

        // Two tones of one colour: a pale ring the badge is cut from, and a deep face set into
        // it. The pair reads at any size, and neither is a flat black that would vanish into a
        // grid line.
        var ring = Tint(rising ? up : down, 0.52);
        var face = Shade(rising ? up : down, 0.34);
        var ink = Shade(rising ? up : down, 0.78);

        session.FillCircle(cx, cy, radius, Ink.Fade(ring, opacity));

        // The face sits inside the ring; every feature is placed as a fraction of this.
        var s = radius * 0.80f;

        session.FillCircle(cx, cy, s, Ink.Fade(face, opacity));

        if (rising)
        {
            Bull(session, cx, cy, s, ring, face, ink, opacity);
        }
        else
        {
            Bear(session, cx, cy, s, ring, face, ink, opacity);
        }
    }

    /// <summary>The bull's own marks: two swept horns, a low snout, two eyes, small ears.</summary>
    private static void Bull(
        CanvasDrawingSession session, float cx, float cy, float s,
        Color ring, Color face, Color ink, double opacity)
    {
        // Ears, poking out at the sides before the horns cross over them.
        session.FillEllipse(
            new Vector2(cx - (s * 0.80f), cy - (s * 0.06f)), s * 0.17f, s * 0.24f, Ink.Fade(ring, opacity));
        session.FillEllipse(
            new Vector2(cx + (s * 0.80f), cy - (s * 0.06f)), s * 0.17f, s * 0.24f, Ink.Fade(ring, opacity));

        // The horns: outward first, then up, the one thing that reads as a bull at any size.
        Horn(session, cx - (s * 0.28f), cy - (s * 0.40f), -1f, s, Ink.Fade(ring, opacity));
        Horn(session, cx + (s * 0.28f), cy - (s * 0.40f), 1f, s, Ink.Fade(ring, opacity));

        // Snout, low and wide, with the two nostrils as dark specks.
        session.FillEllipse(new Vector2(cx, cy + (s * 0.46f)), s * 0.44f, s * 0.30f, Ink.Fade(Tint(ring, 0.28), opacity));
        session.FillEllipse(new Vector2(cx - (s * 0.17f), cy + (s * 0.46f)), s * 0.06f, s * 0.09f, Ink.Fade(ink, opacity));
        session.FillEllipse(new Vector2(cx + (s * 0.17f), cy + (s * 0.46f)), s * 0.06f, s * 0.09f, Ink.Fade(ink, opacity));

        // Eyes.
        session.FillCircle(cx - (s * 0.34f), cy - (s * 0.04f), s * 0.105f, Ink.Fade(ink, opacity));
        session.FillCircle(cx + (s * 0.34f), cy - (s * 0.04f), s * 0.105f, Ink.Fade(ink, opacity));
    }

    /// <summary>The bear's own marks: two round ears, a raised snout, two eyes.</summary>
    private static void Bear(
        CanvasDrawingSession session, float cx, float cy, float s,
        Color ring, Color face, Color ink, double opacity)
    {
        // Ears on top, as two circles with a hollow centre — the difference the eye needs
        // between a bear and a bull, since neither has visible horns at seventy pixels.
        foreach (var side in new[] { -1f, 1f })
        {
            var ex = cx + (side * s * 0.54f);
            var ey = cy - (s * 0.58f);

            session.FillCircle(ex, ey, s * 0.30f, Ink.Fade(ring, opacity));
            session.FillCircle(ex, ey, s * 0.15f, Ink.Fade(face, opacity));
        }

        // Snout: a lighter oval with a dark nose and a short mouth, lower than the bull's.
        session.FillEllipse(new Vector2(cx, cy + (s * 0.34f)), s * 0.34f, s * 0.24f, Ink.Fade(Tint(ring, 0.30), opacity));
        session.FillEllipse(new Vector2(cx, cy + (s * 0.24f)), s * 0.12f, s * 0.08f, Ink.Fade(ink, opacity));

        using var mouth = new CanvasPathBuilder(session);
        mouth.BeginFigure(new Vector2(cx, cy + (s * 0.28f)));
        mouth.AddLine(new Vector2(cx, cy + (s * 0.42f)));
        mouth.AddLine(new Vector2(cx - (s * 0.12f), cy + (s * 0.50f)));
        mouth.EndFigure(CanvasFigureLoop.Open);

        using var mouthGeometry = CanvasGeometry.CreatePath(mouth);
        using var mouthStroke = Round(s * 0.07f);

        session.DrawGeometry(mouthGeometry, Ink.Fade(ink, opacity), s * 0.07f, mouthStroke);

        // Eyes.
        session.FillCircle(cx - (s * 0.28f), cy - (s * 0.02f), s * 0.095f, Ink.Fade(ink, opacity));
        session.FillCircle(cx + (s * 0.28f), cy - (s * 0.02f), s * 0.095f, Ink.Fade(ink, opacity));
    }

    /// <summary>
    /// A single horn: a thick stroke that leaves the head going outward and turns up. Traced as
    /// a curve rather than a triangle because a horn that reads as a spike reads as a devil.
    /// </summary>
    private static void Horn(
        CanvasDrawingSession session, float bx, float by, float side, float s, Color colour)
    {
        using var builder = new CanvasPathBuilder(session);

        builder.BeginFigure(new Vector2(bx, by));
        builder.AddQuadraticBezier(
            new Vector2(bx + (side * s * 0.40f), by - (s * 0.16f)),
            new Vector2(bx + (side * s * 0.32f), by - (s * 0.58f)));
        builder.EndFigure(CanvasFigureLoop.Open);

        using var geometry = CanvasGeometry.CreatePath(builder);
        using var stroke = Round(s * 0.09f);

        session.DrawGeometry(geometry, colour, s * 0.19f, stroke);
    }

    private static CanvasStrokeStyle Round(float width) =>
        new() { StartCap = CanvasCapStyle.Round, EndCap = CanvasCapStyle.Round, LineJoin = CanvasLineJoin.Round };

    /// <summary>Towards white; the pale ring a badge is cut from.</summary>
    private static Color Tint(Color colour, double amount) => Color.FromArgb(
        0xFF,
        (byte)Math.Round(colour.R + ((255 - colour.R) * amount)),
        (byte)Math.Round(colour.G + ((255 - colour.G) * amount)),
        (byte)Math.Round(colour.B + ((255 - colour.B) * amount)));

    /// <summary>Towards black; the face set into the ring, and the ink of its features.</summary>
    private static Color Shade(Color colour, double amount) => Color.FromArgb(
        0xFF,
        (byte)Math.Round(colour.R * (1 - amount)),
        (byte)Math.Round(colour.G * (1 - amount)),
        (byte)Math.Round(colour.B * (1 - amount)));
}
