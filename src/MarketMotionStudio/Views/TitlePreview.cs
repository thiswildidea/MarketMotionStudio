using System.Numerics;
using MarketMotionStudio.Render;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.UI.Xaml;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace MarketMotionStudio.Views;

/// <summary>
/// A strip of the frame's own backdrop with the headline drawn on it the way the frame draws
/// it — the same <see cref="TitleBlock"/>, the same ramp, edge and glow. Shown inside the title
/// dialogs, so what the reader confirms there is the headline as it will actually be inked, not
/// a flat stand-in.
///
/// The page's own badge used to carry this job with a <see cref="TextBlock"/>, which can only
/// fill type in one colour: a metal treatment read as flat pink where the frame draws a
/// gradient over a dark edge, and the two disagreed in exactly the way that reads as "the
/// preview is wrong". This control closes the gap by drawing through the real renderer.
/// </summary>
public sealed class TitlePreview : Grid
{
    private readonly CanvasControl _canvas = new();

    private TitleStyle _style = new();
    private string _text = string.Empty;

    public TitlePreview()
    {
        _canvas.ClearColor = Microsoft.UI.Colors.Transparent;
        _canvas.Draw += OnDraw;

        Children.Add(_canvas);

        // The same care as the frame's own surface: Win2D holds swap-chain resources the XAML
        // tree does not release for it, and a dialog closed takes its controls without them.
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

    /// <summary>The style to preview, as the dialog reads it — nulls where 「跟随全局」 is on.
    /// Named <c>Chosen</c> rather than <c>Style</c> — the latter is
    /// <see cref="FrameworkElement"/>'s own property, and shadowing it is a warning, not a
    /// feature.</summary>
    public TitleStyle Chosen
    {
        get => _style;
        set
        {
            _style = value ?? new TitleStyle();
            _canvas.Invalidate();
        }
    }

    /// <summary>What the headline says.</summary>
    public string Text
    {
        get => _text;
        set
        {
            _text = value ?? string.Empty;
            _canvas.Invalidate();
        }
    }

    /// <summary>Whether the preview draws the main title or the subtitle — the global it
    /// merges against differs.</summary>
    public bool Subtitle { get; set; }

    private void OnDraw(CanvasControl sender, CanvasDrawEventArgs args)
    {
        var width = sender.Size.Width;
        var height = sender.Size.Height;

        if (width <= 0 || height <= 0)
        {
            return;
        }

        var session = args.DrawingSession;

        // The frame's own backdrop, so the headline is seen against what it will actually sit
        // on: the ramp's dark edge and the glow only read against a dark ground, and on a white
        // card both are invisible — which is the whole of the difference the reader reported.
        Ink.FillVertical(session, new Windows.Foundation.Rect(0, 0, width, height), Palette.Background);

        // A context of the same proportions as a frame, so the block's baseline and wrap width
        // resolve the way they will on the page. The margins are the page's own defaults.
        var format = VideoFormat.Create(1080, 1920, 30, VideoFormat.Quality.High);
        var context = new FrameContext(
            format, ChartMargins.Default, 0, new Backdrop(BackdropKind.Default, default, default, null, 0), null);

        // The block is built fresh each draw so it carries the style as it stands right now:
        // the dialog mutates its record on every control change, and a block holding the
        // construction-time copy would draw the last change forever.
        var block = new TitleBlock(
            62, _style, Subtitle ? () => TitleSettings.SubtitleStyle : () => TitleSettings.MainStyle);

        var shown = _text.Length > 0;
        var shape = block.For(sender, _text, context, shown);

        if (shape.Lines <= 0)
        {
            return;
        }

        // The headline lives near the top of a 1080x1920 frame, but the strip is a fraction of
        // that tall. Scale the whole frame down to the strip's width and shift the title band
        // into view, so the block draws at its real size relative to the frame rather than being
        // re-measured against a box that is not the frame's proportions.
        var scale = width / 1080;
        var titleTop = context.TopRow(FrameContext.TitleRowFraction);
        var bandHeight = (shape.Lines * FrameContext.TitleLineHeight) + shape.Size;

        session.Transform = Matrix3x2.CreateScale((float)scale);
        session.Transform = Matrix3x2.Multiply(
            Matrix3x2.CreateTranslation(
                0, (float)((height - (bandHeight * scale)) / 2 - (titleTop * scale))),
            session.Transform);

        // The ink the block resolves — the reader's colour, else the treatment's own default.
        var resolved = TitleStyle.Merge(
            _style, Subtitle ? TitleSettings.SubtitleStyle : TitleSettings.MainStyle);

        var ink = resolved.ParsedColour()
            ?? TitleSkins.Default(resolved.Skin is { } skin ? (TitleSkin)skin : TitleSkin.Plain);

        block.Draw(session, context, _text, shape, ink, 1);
    }
}
