using Microsoft.Graphics.Canvas;

namespace AShareMotionStudio.Render;

/// <summary>
/// One indicator's animation, as a function from a moment to a picture.
///
/// Deliberately stateless with respect to time: <see cref="Draw"/> is handed the
/// fraction it is drawing and must not depend on having been called for the frames
/// before it. That is what lets the preview scrub, the encoder run frames out of
/// order or in parallel, and a re-render of frame 500 produce the same pixels the
/// second time.
///
/// It is also what separates this design from the browser-based tools it replaces.
/// There, the animation advanced with wall-clock time because the recorder
/// timestamped frames as they arrived, so a ninety-second video took ninety
/// seconds to export and feeding frames faster produced a video that played fast.
/// A renderer that is a pure function of <c>Progress</c> has no such coupling: the
/// encoder decides the clock.
/// </summary>
public interface IFrameRenderer
{
    /// <summary>
    /// Draws the whole frame, including its background.
    ///
    /// The session is not cleared first. A renderer owns every pixel of its frame
    /// — a video has no transparency to fall back on, and a renderer that painted
    /// only part of the frame would leave the previous frame's content showing
    /// through in the file while looking correct in a preview that happens to have
    /// a background behind it.
    /// </summary>
    void Draw(CanvasDrawingSession session, FrameContext context);
}
