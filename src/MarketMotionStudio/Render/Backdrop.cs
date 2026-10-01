using System.Runtime.CompilerServices;
using Microsoft.Graphics.Canvas;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>What the frame's backdrop is: the built-in one, a colour, or a picture.</summary>
public enum BackdropKind
{
    /// <summary>Each page's own gradient, the one the frames were designed with.</summary>
    Default,

    /// <summary>A vertical gradient between two colours the user chose.</summary>
    Colour,

    /// <summary>A picture, faded back towards the page's own gradient.</summary>
    Picture,
}

/// <summary>
/// The bottom layer of every frame, however it has been set.
///
/// Carried in the <see cref="FrameContext"/> rather than read from the settings by
/// each renderer, for the same reason everything else is: a renderer is a pure
/// function of its context, and an export that captured its backdrop once cannot
/// have frame 2,000 drawn on a different one because somebody changed a setting
/// while it was running.
///
/// Painting is here, in one place, rather than in each of the seven renderers.
/// They each used to fill their own frame with their own gradient, which is why
/// the per-stock page's backdrop is a different shade from the whole-market one;
/// a backdrop that has been *chosen* has to reach all of them by one route, or
/// it reaches six and the seventh keeps its own.
/// </summary>
/// <param name="Top">The top of the gradient, for <see cref="BackdropKind.Colour"/>.</param>
/// <param name="Bottom">The bottom of the gradient, for <see cref="BackdropKind.Colour"/>.</param>
/// <param name="Picture">Path to the picture, for <see cref="BackdropKind.Picture"/>.</param>
/// <param name="Dim">How far a picture is faded back towards the base, 0 to 1.</param>
/// <param name="Strength">
/// How opaque the chosen pair of colours is, 0 to 1, for <see cref="BackdropKind.Colour"/>.
/// Below 1 the frame's own gradient shows through, which is how a colour too
/// light for the numbers to be read on is made usable without giving it up.
/// </param>
public sealed record Backdrop(
    BackdropKind Kind, Color Top, Color Bottom, string? Picture, double Dim, double Strength = 1)
{
    /// <summary>
    /// Fills the whole frame.
    /// </summary>
    /// <param name="fallback">
    /// The gradient this page uses when the backdrop is <see cref="BackdropKind.Default"/>.
    /// Passed in rather than read from <see cref="Palette.Background"/> here, because
    /// two pages were designed with a backdrop of their own and "default" has to
    /// mean *their* default, not the most common one.
    /// </param>
    public void Fill(
        CanvasDrawingSession session, FrameContext context, (float Position, Color Colour)[] fallback)
    {
        var box = new Rect(0, 0, context.Width, context.Height);

        if (Kind == BackdropKind.Colour)
        {
            if (Strength >= 1)
            {
                Ink.FillVertical(session, box, [(0f, Top), (1f, Bottom)]);
                return;
            }

            // The page's own gradient goes down first and the chosen pair is
            // laid over it, rather than the pair being darkened towards black:
            // what shows through at a lower opacity is the backdrop the frame
            // was designed with, so every setting between the two is a frame
            // that still reads, instead of a colour that has been made muddy
            // to make it darker.
            Ink.FillVertical(session, box, fallback);

            var alpha = Math.Clamp(Strength, 0, 1);

            Ink.FillVertical(
                session, box, [(0f, Ink.Fade(Top, alpha)), (1f, Ink.Fade(Bottom, alpha))]);

            return;
        }

        Ink.FillVertical(session, box, fallback);

        if (Kind != BackdropKind.Picture || Picture is not { Length: > 0 })
        {
            return;
        }

        if (Bitmap(session.Device, Picture) is not { } picture)
        {
            return;
        }

        // Cover rather than stretch: a picture of the wrong shape cropped to
        // fill beats one whose proportions have been changed to make it fit,
        // which is the one distortion a viewer notices without being told.
        //
        // **Clipped to the frame, and this is not decoration.** Covering a 9:16
        // frame with a 16:9 picture makes the drawn rectangle several times the
        // frame's width — the whole point of cover — and a drawing session does
        // not clip to anything by itself. In a file the render target stops it,
        // so the video was always right; in the preview it spilled across the
        // letterbox and over the rest of the window, which is a defect that
        // shows up exactly where the feature is being judged.
        using (session.CreateLayer(1f, box))
        {
            session.DrawImage(
                picture, Cover(box, picture), picture.Bounds, 1f,
                CanvasImageInterpolation.MultiSampleLinear);
        }

        if (Dim <= 0)
        {
            return;
        }

        // Faded towards the frame's own backdrop rather than towards black, so
        // at the strongest setting the frame is exactly the one that was
        // designed, and at every setting between it keeps that backdrop's cast.
        Ink.FillVertical(
            session, box,
            [.. fallback.Select(s => (s.Position, Ink.Fade(s.Colour, Math.Clamp(Dim, 0, 1))))]);
    }

    /// <summary>The largest rectangle of the picture's shape that covers <paramref name="box"/>, centred.</summary>
    private static Rect Cover(Rect box, CanvasBitmap picture)
    {
        var width = picture.Size.Width;
        var height = picture.Size.Height;

        if (width <= 0 || height <= 0)
        {
            return box;
        }

        var scale = Math.Max(box.Width / width, box.Height / height);

        return new Rect(
            box.X + ((box.Width - (width * scale)) / 2),
            box.Y + ((box.Height - (height * scale)) / 2),
            width * scale,
            height * scale);
    }

    /// <summary>
    /// The decoded picture for one device.
    ///
    /// Per device because a Win2D bitmap belongs to the device that made it and
    /// cannot be drawn by another — and the encoder deliberately has a device of
    /// its own, so a picture decoded for the preview would be unusable there.
    ///
    /// Keyed weakly on the device because that is the lifetime that matters: an
    /// export creates a device, uses it for a few thousand frames and drops it,
    /// and a cache that held bitmaps against paths would keep every picture ever
    /// used in an export for as long as the process ran.
    /// </summary>
    private static readonly ConditionalWeakTable<CanvasDevice, Entry> Decoded = new();

    private sealed class Entry
    {
        /// <summary>
        /// The path this entry was built for, whether or not it succeeded. Held
        /// even on failure, so a picture that cannot be decoded is not retried
        /// once per frame for two thousand frames.
        /// </summary>
        public string Path = string.Empty;

        public CanvasBitmap? Bitmap;
    }

    private static CanvasBitmap? Bitmap(CanvasDevice device, string path)
    {
        var decoded = Decoded.GetValue(device, static _ => new Entry());

        lock (decoded)
        {
            if (!string.Equals(decoded.Path, path, StringComparison.OrdinalIgnoreCase))
            {
                decoded.Bitmap = Load(device, path);
                decoded.Path = path;
            }

            return decoded.Bitmap;
        }
    }

    private static CanvasBitmap? Load(CanvasDevice device, string path)
    {
        try
        {
            // Synchronous, and the one blocking wait in the drawing path. It
            // happens once per picture per device: the preview's first frame
            // after a picture is chosen, and the encoder's first frame of an
            // export. Waiting for it is what keeps `Draw` a call that always
            // has a picture to draw rather than one that sometimes draws none.
            return CanvasBitmap.LoadAsync(device, path).AsTask().GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            Diagnostics.CrashLog.Note($"backdrop: {path} could not be decoded, {ex.GetType().Name}");
            return null;
        }
    }
}
