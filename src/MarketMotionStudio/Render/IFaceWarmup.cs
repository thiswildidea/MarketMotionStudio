using Microsoft.Graphics.Canvas;

namespace MarketMotionStudio.Render;

/// <summary>
/// A renderer whose pictures want to exist before the first frame of a file:
/// the export device is a separate D3D device from the preview's, and a logo
/// still in flight when the encoder starts would otherwise draw the whole file
/// as the first-character badges the pictures stand in for.
/// </summary>
public interface IFaceWarmup
{
    /// <summary>Awaits every picture this renderer's frames will ask for onto
    /// <paramref name="device"/> — downloads settled, files decoded. Safe when
    /// there is nothing to warm.</summary>
    Task PrepareAsync(CanvasDevice device);
}
