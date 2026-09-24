using Microsoft.Graphics.Canvas;
using Windows.Media.Core;
using Windows.Media.MediaProperties;
using Windows.Media.Transcoding;
using Windows.Security.Cryptography;
using Windows.Storage;

namespace AShareMotionStudio.Render;

/// <summary>
/// Turns an <see cref="IFrameRenderer"/> into an H.264 MP4.
///
/// **The encoder owns the clock, and that is the whole point of the design it rests on.** Frames are
/// produced on demand: the muxer asks for the next sample, this draws it, hands it back stamped with
/// a timestamp derived from its *index*, and the loop runs as fast as the machine can encode. Nothing
/// waits for wall-clock time.
///
/// That is only possible because <see cref="IFrameRenderer.Draw"/> is a pure function of
/// <see cref="FrameContext.Progress"/>. The browser tool this replaces could not do it: it captured a
/// live canvas through `MediaRecorder`, which timestamps frames as they arrive, so a ninety-second
/// video took ninety seconds to write and feeding frames faster produced a video that played fast.
/// Every rule in `one-render-path.mdc` about renderers not reading a clock exists to make this class
/// possible.
/// </summary>
public static class VideoExporter
{
    /// <summary>
    /// Renders and encodes the whole animation.
    /// </summary>
    /// <param name="progress">Fraction complete, for a page to show. Reported by the transcoder.</param>
    /// <returns>The file written.</returns>
    public static async Task<StorageFile> EncodeAsync(
        IFrameRenderer renderer,
        VideoFormat format,
        ChartMargins margins,
        TimeSpan duration,
        StorageFolder folder,
        string fileName,
        IProgress<double>? progress,
        CancellationToken cancellation)
    {
        Diagnostics.CrashLog.Note($"encode: enter {format.Width}x{format.Height}@{format.FramesPerSecond} dur={duration}");

        var frames = format.FrameCount(duration);
        var frameDuration = TimeSpan.FromTicks(TimeSpan.TicksPerSecond / format.FramesPerSecond);

        // Uncompressed BGRA in, H.264 out. The input is what Win2D hands back from a render target, so
        // there is no pixel-format conversion on this side of the transcoder to get wrong.
        var uncompressed = VideoEncodingProperties.CreateUncompressed(
            MediaEncodingSubtypes.Bgra8, (uint)format.Width, (uint)format.Height);

        uncompressed.FrameRate.Numerator = (uint)format.FramesPerSecond;
        uncompressed.FrameRate.Denominator = 1;

        var descriptor = new VideoStreamDescriptor(uncompressed);

        var source = new MediaStreamSource(descriptor)
        {
            Duration = duration,

            // Nothing seeks a stream that is being generated once, front to back, and claiming
            // otherwise invites the transcoder to ask for a position this cannot produce.
            CanSeek = false,

            // No look-ahead buffering. Frames are cheap to produce on demand and buffering would only
            // hold finished ones in memory at 8 MB each.
            BufferTime = TimeSpan.Zero,
        };

        // **A device of its own, not the shared one.** `SampleRequested` is raised on the media
        // pipeline's thread, and drawing there through the device the UI is also drawing the preview
        // with is concurrent access to one D3D device. Win2D does not serialise that for you, and the
        // failure is not a managed exception — the process goes away with no crash log, no Windows
        // Error Reporting entry and no fault in the event log, which looks exactly like somebody
        // closing the window. That is what happened on the first attempt here.
        //
        // A dedicated device also stops a long encode from contending with preview redraws.
        Diagnostics.CrashLog.Note($"encode: source built, frames={frames}");

        using var device = new CanvasDevice();

        // One render target for the whole export rather than one per frame. At 1080×1920 each is an
        // 8 MB surface, and allocating one per frame would spend more time in the allocator than in
        // the renderer.
        using var target = new CanvasRenderTarget(device, format.Width, format.Height, 96);

        // The pipeline is documented to request samples one at a time, but this costs nothing and the
        // consequence of being wrong about it is the silent process death described above.
        var drawing = new Lock();

        var next = 0;
        Exception? failure = null;

        source.Starting += (_, e) => e.Request.SetActualStartPosition(TimeSpan.Zero);

        source.SampleRequested += (_, e) =>
        {
            // Synchronous on purpose: drawing one frame is fast and taking a deferral to do it on
            // another thread would only add a hand-off. The transcoder calls this on its own thread
            // and blocks until the sample comes back, which is exactly the back-pressure wanted.
            try
            {
                lock (drawing)
                {
                    if (next >= frames || cancellation.IsCancellationRequested)
                    {
                        // A null sample is how a MediaStreamSource says "that was the last one". Leaving
                        // it unset instead hangs the transcode rather than ending it.
                        e.Request.Sample = null;
                        return;
                    }

                    // The timestamp comes from the frame *index*, never from a clock. This is the line
                    // that makes the export faster than real time.
                    var timestamp = frameDuration * next;

                    // Progress runs 0 to 1 inclusive across the frames, so the last frame is the
                    // animation's final state rather than one frame short of it.
                    var fraction = frames <= 1 ? 1 : (double)next / (frames - 1);

                    using (var session = target.CreateDrawingSession())
                    {
                        // No transform, exactly as the cover export does it. Same renderer, same context
                        // type, no preview-specific path.
                        renderer.Draw(session, new FrameContext(format, margins, fraction));
                    }

                    var pixels = target.GetPixelBytes();

                    e.Request.Sample = MediaStreamSample.CreateFromBuffer(
                        CryptographicBuffer.CreateFromByteArray(pixels), timestamp);

                    e.Request.Sample.Duration = frameDuration;
                    next++;

                    if (next == 1 || next % 100 == 0)
                    {
                        Diagnostics.CrashLog.Note($"encode: served sample {next}/{frames}");
                    }
                }
            }
            catch (Exception ex)
            {
                // An exception thrown out of this handler is swallowed by the media pipeline and
                // surfaces only as a transcode that stops early with no reason given. Captured here and
                // rethrown below, so the page reports what actually went wrong.
                failure = ex;
                e.Request.Sample = null;
            }
        };

        Diagnostics.CrashLog.Note("encode: device and target built");

        var profile = MediaEncodingProfile.CreateMp4(VideoEncodingQuality.Auto);

        profile.Video.Width = (uint)format.Width;
        profile.Video.Height = (uint)format.Height;
        profile.Video.Bitrate = format.BitsPerSecond;
        profile.Video.FrameRate.Numerator = (uint)format.FramesPerSecond;
        profile.Video.FrameRate.Denominator = 1;

        // Video only. Left in place, an audio track would be a silent stream of the same length, which
        // costs bytes and makes some editors prompt about a track with nothing in it.
        profile.Audio = null;

        Diagnostics.CrashLog.Note("encode: profile built, creating file");

        var file = await folder.CreateFileAsync(fileName, CreationCollisionOption.GenerateUniqueName);

        Diagnostics.CrashLog.Note($"encode: file created {file.Name}");

        // Created before the transcode and deleted if it fails, so a failure does not leave a
        // zero-length MP4 that looks like a video until something tries to open it.
        try
        {
            using (var stream = await file.OpenAsync(FileAccessMode.ReadWrite))
            {
                var transcoder = new MediaTranscoder { HardwareAccelerationEnabled = true };

                var prepared = await transcoder.PrepareMediaStreamSourceTranscodeAsync(source, stream, profile);

                Diagnostics.CrashLog.Note($"encode: prepared can={prepared.CanTranscode} reason={prepared.FailureReason}");

                if (!prepared.CanTranscode)
                {
                    throw new InvalidOperationException($"The encoder refused this format: {prepared.FailureReason}.");
                }

                await prepared.TranscodeAsync().AsTask(cancellation, progress);

                Diagnostics.CrashLog.Note($"encode: transcode returned, samples served={next}");
            }

            if (failure is not null)
            {
                throw new InvalidOperationException("A frame could not be drawn.", failure);
            }

            return file;
        }
        catch
        {
            try
            {
                await file.DeleteAsync(StorageDeleteOption.PermanentDelete);
            }
            catch (Exception)
            {
                // Tidying up must not replace the real error with one about tidying up.
            }

            throw;
        }
    }

    /// <summary>
    /// A file name carrying what the video is of and what it is, so a folder of exports can be told
    /// apart without opening them.
    /// </summary>
    public static string VideoName(string label, DateOnly from, DateOnly to, VideoFormat format)
    {
        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        if (safe.Length == 0)
        {
            safe = "video";
        }

        return $"{safe}_{TurnoverRenderer.Iso(from)}_{TurnoverRenderer.Iso(to)}_{format.NameSuffix}.mp4";
    }
}
