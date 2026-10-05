using MarketMotionStudio.Render;
using Microsoft.Graphics.Canvas.UI.Xaml;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Foundation;

namespace MarketMotionStudio.Views;

/// <summary>
/// A strip of the frame's own backdrop with the watermark laid across it, shown
/// on the Settings page.
///
/// Exists because the frame is on another page and the watermark is faint by
/// design: without this the answer to "did typing that name do anything" is not
/// on the page where the name was typed, and the previous appearance setting
/// that lacked a preview of its own was reported as not working while every
/// part of it was correct.
///
/// It is drawn by the same <see cref="Watermark"/> the frame is drawn by, at a
/// size of its own — so what it shows is the mark as it will be laid, not a
/// second opinion about it.
/// </summary>
public sealed class WatermarkPreview : Grid
{
    private readonly CanvasControl _canvas = new();

    /// <summary>
    /// The height of one repetition as a fraction of the strip.
    ///
    /// Bigger than the frame's own proportion, because a strip seventy-odd
    /// pixels tall drawn at the frame's scale would hold one repetition the
    /// height of a caption — legible, but not enough of it to see that it
    /// repeats, which is the half of the idea the strip is there to show.
    /// </summary>
    private const double Size = 0.30;

    private Watermark? _watermark;

    public WatermarkPreview()
    {
        _canvas.ClearColor = Microsoft.UI.Colors.Transparent;
        _canvas.Draw += OnDraw;

        Children.Add(_canvas);

        // The same care as the frame's own surface: Win2D holds swap-chain
        // resources the XAML tree does not release for it, and a page that is
        // navigated away from takes its controls without them.
        Loaded += (_, _) =>
        {
            if (_canvas.Parent is null)
            {
                Children.Add(_canvas);
            }

            _canvas.Invalidate();
        };

        Unloaded += (_, _) => _canvas.RemoveFromVisualTree();
    }

    /// <summary>The watermark to show. Null draws the backdrop without one.</summary>
    public Watermark? Watermark
    {
        get => _watermark;
        set
        {
            _watermark = value;
            _canvas.Invalidate();
        }
    }

    private void OnDraw(CanvasControl sender, CanvasDrawEventArgs args)
    {
        var width = sender.Size.Width;
        var height = sender.Size.Height;

        if (width <= 0 || height <= 0)
        {
            return;
        }

        var session = args.DrawingSession;

        // The frame's own backdrop, so the mark is seen against what it will
        // actually sit on: it is a light wash over a near-black gradient, and
        // on a white card it would not be visible at all.
        Ink.FillVertical(session, new Rect(0, 0, width, height), Palette.Background);

        if (_watermark is { } watermark)
        {
            watermark.Paint(session, width, height, height * Size);
        }
    }
}
