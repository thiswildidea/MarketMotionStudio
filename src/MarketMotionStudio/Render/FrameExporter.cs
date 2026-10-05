using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.UI.Xaml;
using Windows.Storage;

namespace MarketMotionStudio.Render;

/// <summary>
/// Writes a single frame to a PNG, at full export resolution.
///
/// Small, and worth more than its size. It is the cover image people need to post a video — but it
/// is also the **first thing in this app to render off-screen**, which is the mechanism the video
/// encoder will need: a <see cref="CanvasRenderTarget"/> at the real resolution, the production
/// renderer drawn into it with no transform, and the result read back. If a cover comes out right,
/// the encoder's drawing half is already proved and only its muxing half is new.
///
/// It also exercises the guarantee in `one-render-path.mdc` from the other side. The preview draws
/// the same renderer through a scaling transform; this draws it at 1:1. A cover that does not match
/// the preview means that rule has been broken somewhere.
/// </summary>
public static class FrameExporter
{
    /// <summary>
    /// Renders one frame and saves it as a PNG in <paramref name="folder"/>.
    /// </summary>
    /// <returns>The file written.</returns>
    public static async Task<StorageFile> SavePngAsync(
        IFrameRenderer renderer,
        VideoFormat format,
        ChartMargins margins,
        double progress,
        StorageFolder folder,
        string fileName,
        CancellationToken cancellation)
    {
        // The shared Win2D device rather than a new one: creating a device per export would mean a
        // driver round trip for a single image, and the preview already has one.
        var device = CanvasDevice.GetSharedDevice();

        // 96 DPI and the format's own pixel size, so the PNG is exactly the resolution the video
        // would be. Asking for display DPI here would silently produce a cover of a different size
        // on a scaled monitor than on an unscaled one.
        using var target = new CanvasRenderTarget(device, format.Width, format.Height, 96);

        // Read once, before drawing: the frame's backdrop is the one chosen when
        // the cover was asked for, not one that may have been changed since.
        // The watermark is read with it and for the same reason — a mark turned
        // on halfway through must not appear in half of one image.
        var backdrop = AnimationBackdrop.Current;
        var watermark = WatermarkSettings.Current;

        using (var session = target.CreateDrawingSession())
        {
            // No transform. This is the encoder's path, not the preview's.
            renderer.Draw(session, new FrameContext(format, margins, progress, backdrop, watermark));
        }

        cancellation.ThrowIfCancellationRequested();

        var file = await folder.CreateFileAsync(fileName, CreationCollisionOption.GenerateUniqueName);

        // GenerateUniqueName rather than ReplaceExisting: a cover is something someone may export
        // several of while choosing a frame, and silently overwriting the previous one would lose the
        // frame they had already decided they liked.
        using var stream = await file.OpenAsync(FileAccessMode.ReadWrite);
        await target.SaveAsync(stream, CanvasBitmapFileFormat.Png);

        return file;
    }

    /// <summary>
    /// A file name carrying what the image is of, so a folder of covers can be told apart.
    /// </summary>
    /// <remarks>
    /// Every part is sanitised even though none of it is user input today — the title is, and it
    /// reaches a file name. `Path.GetInvalidFileNameChars` rather than a hand-written list, and a
    /// length cap, because a title can be as long as someone cares to type.
    /// </remarks>
    public static string CoverName(string label, DateOnly from, DateOnly to, VideoFormat format)
    {
        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        if (safe.Length == 0)
        {
            safe = "cover";
        }

        return $"{safe}_{TurnoverRenderer.Iso(from)}_{TurnoverRenderer.Iso(to)}_{format.Width}x{format.Height}.png";
    }
}
