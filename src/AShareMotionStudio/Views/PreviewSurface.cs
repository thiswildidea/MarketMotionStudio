using System.Numerics;
using AShareMotionStudio.Render;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.UI.Xaml;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.UI;

namespace AShareMotionStudio.Views;

/// <summary>
/// Shows one frame of what will be exported, at whatever size the window allows.
///
/// The frame is a fixed 9:16 and the space it is given is not, so the frame is
/// letterboxed: the largest rectangle of the right shape that fits, centred, with
/// the window's Mica showing around it. Stretching instead would be the one place
/// in the app where the preview and the file disagreed, and it would disagree
/// about proportion, which is the thing a composition is judged on.
///
/// The renderer is handed a drawing session that has already been scaled, so it
/// draws in the video's own pixels and is not aware a preview exists. The encoder
/// calls the same renderer with the same <see cref="FrameContext"/> and no
/// transform. There is deliberately no second code path.
///
/// The safe-area guides are drawn **here**, after the renderer has returned, and
/// therefore cannot reach a file: the encoder does not own a
/// <see cref="PreviewSurface"/>. In the tools this replaces the guides were DOM
/// elements outside the canvas and were also hidden during recording — two
/// mechanisms for one guarantee, either of which could be forgotten. This is one.
/// </summary>
public sealed class PreviewSurface : Grid
{
    private readonly CanvasControl _canvas = new();

    public PreviewSurface()
    {
        // Transparent, so the Mica behind the window shows in the letterbox
        // margins rather than a grey band that looks like part of the frame.
        // Microsoft.UI.Colors, not Windows.UI.Colors: the WinUI 3 palette is the one
        // in the app's own namespace, while the Color struct it yields is still
        // Windows.UI.Color, which is why only one of the two needs qualifying here.
        _canvas.ClearColor = Microsoft.UI.Colors.Transparent;
        _canvas.Draw += OnDraw;

        Children.Add(_canvas);

        // Win2D holds device resources that the XAML tree does not release for it.
        // A page that is navigated away from and collected takes its controls with
        // it, but the swap chain is not part of that, and the leak shows up as
        // memory that only grows while the app is used normally.
        Unloaded += (_, _) => _canvas.RemoveFromVisualTree();
    }

    /// <summary>The size and rate being previewed. Changing it re-letterboxes.</summary>
    public VideoFormat Format { get; set; } = VideoFormat.Default;

    /// <summary>The margins the sliders control, in baseline pixels.</summary>
    public ChartMargins Margins { get; set; } = new(108, 108, 480);

    /// <summary>Whether to overlay the host app's occlusion zones.</summary>
    public bool ShowGuides { get; set; }

    /// <summary>
    /// Which animation to draw. Null draws an empty frame rather than nothing at
    /// all: a blank rectangle of the right shape says "no data yet", where an
    /// empty control says "this feature does not work".
    /// </summary>
    public IFrameRenderer? Renderer { get; set; }

    /// <summary>The moment being shown, from 0 to 1.</summary>
    public double Progress { get; set; }

    /// <summary>
    /// Asks for a redraw. Every control that changes the picture calls this; the
    /// surface does not watch its own properties, because a property set three
    /// times while a slider is dragged should cost one frame and not three.
    /// </summary>
    public void Redraw() => _canvas.Invalidate();

    private void OnDraw(CanvasControl sender, CanvasDrawEventArgs args)
    {
        var available = sender.Size;

        if (available.Width <= 0 || available.Height <= 0)
        {
            return;
        }

        var fit = Math.Min(available.Width / Format.Width, available.Height / Format.Height);
        var drawn = new Vector2((float)(Format.Width * fit), (float)(Format.Height * fit));
        var offset = new Vector2(
            (float)((available.Width - drawn.X) / 2),
            (float)((available.Height - drawn.Y) / 2));

        var session = args.DrawingSession;

        // Scale then translate, in that order of application: the translation must
        // not itself be scaled, or the frame drifts off centre as the window grows.
        session.Transform = Matrix3x2.CreateScale((float)fit) * Matrix3x2.CreateTranslation(offset);

        var context = new FrameContext(Format, Margins, Progress);

        if (Renderer is { } renderer)
        {
            renderer.Draw(session, context);
        }
        else
        {
            Ink.FillVertical(
                session,
                new Windows.Foundation.Rect(0, 0, Format.Width, Format.Height),
                Palette.Background);
        }

        if (ShowGuides)
        {
            DrawGuides(session, context);
        }
    }

    /// <summary>
    /// Outlines the three regions the host app draws its own interface over, in the
    /// frame's own coordinates.
    ///
    /// Outlines and a wash rather than solid blocks. The point is to see whether
    /// something important is underneath one, which a solid overlay would hide —
    /// the guide would then be answering its own question.
    /// </summary>
    private void DrawGuides(CanvasDrawingSession session, FrameContext context)
    {
        var edge = Color.FromArgb(0xB0, 0xFF, 0xD1, 0x4A);
        var wash = Color.FromArgb(0x1A, 0xFF, 0xD1, 0x4A);
        var dashed = new CanvasStrokeStyle { DashStyle = CanvasDashStyle.Dash };
        var stroke = (float)context.Px(2);

        void Zone(double x, double y, double width, double height)
        {
            session.FillRectangle((float)x, (float)y, (float)width, (float)height, wash);
            session.DrawRectangle((float)x, (float)y, (float)width, (float)height, edge, stroke, dashed);
        }

        Zone(0, 0, context.Width, context.Height * SafeArea.Top);
        Zone(context.Width * (1 - SafeArea.Right), 0, context.Width * SafeArea.Right, context.Height);
        Zone(0, context.Height * (1 - SafeArea.Bottom), context.Width, context.Height * SafeArea.Bottom);
    }
}
