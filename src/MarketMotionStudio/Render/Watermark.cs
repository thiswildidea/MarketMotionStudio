using System.Numerics;
using System.Runtime.CompilerServices;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The name written across the backdrop of every frame, slanted and repeated.
///
/// It is drawn as part of the backdrop rather than on top of the chart: the
/// point of it is that the file carries where it came from, and a mark laid over
/// the numbers would be read as part of the data. Under the data it can be as
/// faint as it likes and still be in every frame, which is the only thing asked
/// of it.
///
/// **One setting for every page**, for the same reason the backdrop is: a video
/// is posted somewhere, and the reason to sign it is about the person posting,
/// not about which of the twenty-five pages made it.
///
/// Reached from <see cref="Backdrop.Fill"/>, which is the one place every
/// renderer fills its frame through — so this is written once and lands on all
/// of them, including the empty frame a page shows before anything is fetched.
/// </summary>
/// <param name="Text">What it says. Never blank; see <see cref="DefaultText"/>.</param>
public sealed record Watermark(string Text)
{
    /// <summary>
    /// What it says before anybody has changed it.
    ///
    /// The same four characters in every language. A watermark is a signature,
    /// and a signature that changed with the interface language would be a
    /// different signature on each machine — the one thing it cannot be. It is
    /// editable precisely because it is the user's own to change.
    /// </summary>
    public const string DefaultText = "周期留白";

    /// <summary>
    /// The longest name accepted, in characters.
    ///
    /// Not a limit on what can be said but on what stays a watermark: a whole
    /// sentence repeated across the frame stops reading as a mark on the
    /// backdrop and starts reading as something to be read, which then competes
    /// with the numbers it is drawn behind.
    /// </summary>
    public const int MaxLength = 24;

    /// <summary>
    /// The height of one repetition, in baseline pixels.
    ///
    /// Small relative to the frame because it is repeated: what has to be
    /// legible is one instance of it, not the pattern.
    /// </summary>
    private const double Size = 46;

    /// <summary>The gap after one repetition before the next, as a multiple of <see cref="Size"/>.</summary>
    private const double GapAcross = 2.4;

    /// <summary>The distance from one row to the next, as a multiple of <see cref="Size"/>.</summary>
    private const double GapDown = 3.4;

    /// <summary>
    /// How opaque one repetition is, out of 255.
    ///
    /// Low enough that nothing drawn over it — a bar, a line, a caption — keeps
    /// its own colour, and high enough to still be there when a still of the
    /// video is lifted out of it. Measured against the frame's own backdrop,
    /// which is near-black: this lifts a pixel by about a tenth of the way to
    /// the title's white, so it reads as part of the backdrop rather than as
    /// writing on it.
    /// </summary>
    private const byte Alpha = 26;

    /// <summary>The slant: 45°, the way a mark like this is usually laid.</summary>
    private const double Radians = -Math.PI / 4;

    /// <summary>
    /// Draws the watermark across one frame.
    ///
    /// Goes through the cached layer rather than painting the repetitions on
    /// every frame: tiling a 1080×1920 frame at this size is over a hundred
    /// pieces of text, and an export is thousands of frames. Drawn once per
    /// device instead, and the frame costs one image.
    /// </summary>
    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var fontSize = context.Px(Size);

        if (Layer(session, context.Width, context.Height, fontSize) is { } tile)
        {
            // The rectangle stated rather than the overload that takes a point:
            // a target carries a DPI of its own, and leaving the size to be
            // worked out from it would put the layer at the wrong scale on a
            // display that is not 96 dpi — which the preview is not.
            session.DrawImage(tile, new Rect(0, 0, context.Width, context.Height));
            return;
        }

        Paint(session, context.Width, context.Height, fontSize);
    }

    /// <summary>
    /// Paints the repetitions straight onto a session, at a size the caller
    /// chooses.
    ///
    /// Separate from <see cref="Draw"/> because the Settings page shows the
    /// watermark in a strip a fraction of the frame's size, where a layer the
    /// size of a frame would be a thousand times more than is needed — and
    /// where the size is the strip's, not the frame's.
    /// </summary>
    public void Paint(CanvasDrawingSession session, double width, double height, double fontSize)
    {
        if (width <= 0 || height <= 0 || fontSize <= 0)
        {
            return;
        }

        using var format = Ink.Format(fontSize);

        var colour = Color.FromArgb(Alpha, Palette.Title.R, Palette.Title.G, Palette.Title.B);
        var across = Ink.Measure(session, Text, format) + (fontSize * GapAcross);
        var down = fontSize * GapDown;

        // The square that covers the frame however far it is turned: the
        // diagonal, so that a corner of the pattern never leaves a bare
        // triangle at a corner of the frame.
        var reach = Math.Sqrt((width * width) + (height * height));

        var saved = session.Transform;

        try
        {
            // Turned about the frame's middle, and put in front of the
            // transform already in force — the preview's, which scales the
            // frame down to fit. Composed the other way round it would turn
            // about a point that has already been scaled, and the pattern
            // would walk off the frame as the window grew.
            session.Transform = Matrix3x2.CreateRotation(
                (float)Radians, new Vector2((float)(width / 2), (float)(height / 2))) * saved;

            var left = (width - reach) / 2;
            var top = (height - reach) / 2;

            for (var row = 0; (row * down) <= reach; row++)
            {
                // Every other row shifted half a step, which is what stops the
                // repetitions from lining up into the columns and rows of a
                // grid — a grid of them reads as a texture of its own and the
                // frame looks dirty rather than marked.
                var stagger = (row % 2) * (across / 2);

                for (var col = 0; (col * across) <= reach; col++)
                {
                    session.DrawText(
                        Text,
                        (float)(left + (col * across) + stagger),
                        (float)(top + (row * down)),
                        colour,
                        format);
                }
            }
        }
        finally
        {
            // Restored whatever happens, because the caller has a frame to draw
            // after this one and a transform left turned would put the whole
            // chart at 45°.
            session.Transform = saved;
        }
    }

    /// <summary>
    /// The whole pattern as one image, for one device.
    ///
    /// Per device for the same reason the backdrop's picture is: a Win2D bitmap
    /// belongs to the device that made it, and the encoder deliberately has a
    /// device of its own, so a layer built for the preview cannot be drawn into
    /// a file.
    ///
    /// Keyed weakly on the device because that is the lifetime that matters —
    /// an export makes a device, uses it for a few thousand frames and drops
    /// it, and a cache held against the text would keep every frame-sized layer
    /// this process ever built.
    /// </summary>
    private CanvasRenderTarget? Layer(
        CanvasDrawingSession session, double width, double height, double fontSize)
    {
        var entry = Painted.GetValue(session.Device, static _ => new Entry());

        lock (entry)
        {
            if (entry.Tile is { } tile
                && string.Equals(entry.Text, Text, StringComparison.Ordinal)
                && Math.Abs(entry.Width - width) < 0.5
                && Math.Abs(entry.Height - height) < 0.5
                && Math.Abs(entry.Size - fontSize) < 0.5)
            {
                return tile;
            }

            entry.Tile?.Dispose();
            entry.Tile = null;
            entry.Tile = Build(session.Device, width, height, fontSize);

            // Held even when the build failed, so a size that cannot be
            // allocated is not retried once per frame for the whole export.
            entry.Text = Text;
            entry.Width = width;
            entry.Height = height;
            entry.Size = fontSize;

            return entry.Tile;
        }
    }

    private CanvasRenderTarget? Build(CanvasDevice device, double width, double height, double fontSize)
    {
        try
        {
            // 96 dpi, like the render target an export draws into: the layer is
            // measured in the frame's own pixels, and a display dpi here would
            // make the pattern a different size in the preview than in the file.
            var target = new CanvasRenderTarget(
                device, (float)Math.Ceiling(width), (float)Math.Ceiling(height), 96);

            using (var session = target.CreateDrawingSession())
            {
                Paint(session, width, height, fontSize);
            }

            return target;
        }
        catch (Exception ex)
        {
            Diagnostics.CrashLog.Note($"watermark: {width}x{height} could not be drawn, {ex.GetType().Name}");
            return null;
        }
    }

    private static readonly ConditionalWeakTable<CanvasDevice, Entry> Painted = new();

    private sealed class Entry
    {
        public string Text = string.Empty;

        public double Width;

        public double Height;

        public double Size;

        public CanvasRenderTarget? Tile;
    }
}
