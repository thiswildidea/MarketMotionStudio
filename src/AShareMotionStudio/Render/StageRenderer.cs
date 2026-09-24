using System.Numerics;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;

namespace AShareMotionStudio.Render;

/// <summary>
/// The empty stage both animations are drawn onto: background, gridlines, the
/// baseline bars stand on, the title block and the data-source credit.
///
/// This is not a placeholder. Everything here is common to both indicators and
/// stays once they are implemented — an indicator renderer draws the stage first
/// and then its own series on top, so the two pages cannot drift apart on where
/// the baseline sits or how far the axis labels are from the edge.
///
/// Until those renderers exist it is also what the preview shows, which makes the
/// margin sliders and the resolution and safe-area controls testable on their own:
/// the thing they move is visible, and it is the same geometry the series will be
/// laid out against.
/// </summary>
public sealed class StageRenderer : IFrameRenderer
{
    /// <summary>How many horizontal gridlines to draw, including the baseline.</summary>
    private const int GridLines = 5;

    /// <summary>
    /// Room reserved between the chart baseline and the credit, in baseline pixels.
    ///
    /// The stage's own figure. Each indicator declares its own, because what lives
    /// in that band differs — date labels and four statistic cards on the
    /// whole-market chart, a second panel on the per-stock one — and the bottom
    /// margin measures to the credit rather than to the baseline precisely so that
    /// this can vary without the margin meaning something different per page.
    /// </summary>
    public const double CreditGap = 150;

    /// <summary>The headline, drawn in the title block under the top safe area.</summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Whether to draw the title at all.
    ///
    /// Off is a real choice, not a degraded one: a poster who puts the name in the
    /// caption, or who would rather not show which instrument this is, gets the
    /// title row back as chart height. Everything below shifts up into the freed
    /// row and the bottom margin holds the lower edge still.
    /// </summary>
    public bool ShowTitle { get; set; } = true;

    /// <summary>The line under it, for the range and the number of observations.</summary>
    public string Subtitle { get; set; } = string.Empty;

    /// <summary>
    /// Who the data came from, drawn at the very bottom of the content. Always
    /// present in an exported video, which is the point of it: the frame has to say
    /// where the numbers are from even when the caption that accompanied the post
    /// is gone.
    /// </summary>
    public string Credit { get; set; } = string.Empty;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        Ink.FillVertical(session, new Rect(0, 0, context.Width, context.Height), Palette.Background);

        DrawGrid(session, context);
        DrawTitleBlock(session, context);
        DrawCredit(session, context);
        DrawProgressBar(session, context);
    }

    /// <summary>
    /// Horizontal gridlines from the baseline upwards, with the baseline itself
    /// drawn solid and brighter — it is a different kind of line from the rest and
    /// the bars sit on it.
    /// </summary>
    /// <summary>
    /// Rows this stage puts between the title block and the plot: its subtitle.
    /// </summary>
    private const double HeaderRows = 60;

    private void DrawGrid(CanvasDrawingSession session, FrameContext context)
    {
        var baseline = context.BaselineAbove(CreditGap);
        var height = context.PlotHeight(ShowTitle, HeaderRows, CreditGap);

        var dashed = new CanvasStrokeStyle { DashStyle = CanvasDashStyle.Dash };
        var thin = (float)context.Px(1.5);

        for (var i = 1; i < GridLines; i++)
        {
            var y = (float)(baseline - (height * i / GridLines));

            session.DrawLine(
                new Vector2((float)context.ChartLeft, y),
                new Vector2((float)context.ChartRight, y),
                Palette.Grid,
                thin,
                dashed);
        }

        session.DrawLine(
            new Vector2((float)context.ChartLeft, (float)baseline),
            new Vector2((float)context.ChartRight, (float)baseline),
            Palette.Muted,
            (float)context.Px(2.5));
    }

    /// <summary>
    /// The title block, positioned from <see cref="FrameContext.TitleTop"/> rather
    /// than from the top of the frame. Above that line the phone's status bar and
    /// the player's own controls overlap the video.
    /// </summary>
    private void DrawTitleBlock(CanvasDrawingSession session, FrameContext context)
    {
        if (ShowTitle && Title.Length > 0)
        {
            // Shrunk to fit rather than clipped or wrapped. A custom title is free
            // text, and the two failure modes it would otherwise have are both worse
            // than smaller type: clipping loses words silently, and wrapping pushes
            // the whole layout down into the chart.
            using var format = Centred(context, FitSize(session, context, Title, 58), FontWeight.SemiBold);

            session.DrawText(
                Title,
                new Rect(context.ChartLeft, context.TitleTop + context.Px(18),
                         context.ChartWidth, context.Px(FrameContext.TitleRowHeight)),
                Palette.Title,
                format);
        }

        if (Subtitle.Length > 0)
        {
            using var format = Centred(context, 34, FontWeight.Normal);

            // Positioned from ContentTop, which is what moves up when the title is
            // hidden. Adding an offset to a fixed top instead is how the two halves
            // of that behaviour drift apart.
            session.DrawText(
                Subtitle,
                new Rect(context.ChartLeft, context.ContentTop(ShowTitle) + context.Px(6),
                         context.ChartWidth, context.Px(HeaderRows)),
                Palette.Muted,
                format);
        }
    }

    /// <summary>
    /// The largest font size at or below <paramref name="wanted"/> that lets the text
    /// fit the chart width, never going below half.
    ///
    /// The floor matters: without one, a pasted paragraph would shrink until it was
    /// unreadable, which looks like a rendering bug rather than like text that is too
    /// long. At half size it is legibly too small, which reads as "shorten this".
    /// </summary>
    private static double FitSize(CanvasDrawingSession session, FrameContext context, string text, double wanted)
    {
        using var probe = new CanvasTextFormat
        {
            FontSize = (float)context.Px(wanted),
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            WordWrapping = CanvasWordWrapping.NoWrap,
        };

        using var layout = new CanvasTextLayout(session, text, probe, 0, 0);

        var natural = layout.LayoutBounds.Width;

        if (natural <= 0 || natural <= context.ChartWidth)
        {
            return wanted;
        }

        return wanted * Math.Max(0.5, context.ChartWidth / natural);
    }

    /// <summary>
    /// Sits at <see cref="FrameContext.CreditLine"/>, which is the lowest content in
    /// the frame and therefore what the bottom margin measures to.
    ///
    /// This is the anchor of the lower stack, not a consequence of it. Drawing it at
    /// "baseline plus a gap" — which is what this did while the bottom margin still
    /// measured to the baseline — put the credit at a distance from the bottom edge
    /// that changed with the margin, so the one element guaranteeing the frame says
    /// where its numbers came from could be pushed off the bottom of the video.
    /// </summary>
    private void DrawCredit(CanvasDrawingSession session, FrameContext context)
    {
        if (Credit.Length == 0)
        {
            return;
        }

        using var format = Centred(context, 26, FontWeight.Normal);

        session.DrawText(
            Credit,
            new Rect(context.ChartLeft, context.CreditLine, context.ChartWidth, context.Px(48)),
            Palette.Muted,
            format);
    }

    /// <summary>
    /// A bar along the very bottom edge showing how far through the video this
    /// frame is. Outside every margin on purpose: it is chrome for the viewer, not
    /// part of the chart, and it should not move when the chart is re-laid out.
    /// </summary>
    private static void DrawProgressBar(CanvasDrawingSession session, FrameContext context)
    {
        var height = (float)context.Px(8);
        var y = (float)(context.Height - height);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.Grid);

        session.FillRectangle(
            0,
            y,
            (float)(context.Width * Math.Clamp(context.Progress, 0, 1)),
            height,
            Palette.Emphasis);
    }

    /// <summary>
    /// A centred text format at a baseline-pixel size.
    ///
    /// Every size in a renderer goes through <see cref="FrameContext.Px"/> like
    /// this. A font size assigned directly would be the one measurement in the app
    /// that did not scale with the resolution, and the symptom — text that is
    /// correct at 1080p and wrong at 1440p — reads as a layout bug rather than as a
    /// missing multiplication.
    /// </summary>
    private static CanvasTextFormat Centred(FrameContext context, double baselineSize, FontWeight weight) => new()
    {
        FontSize = (float)context.Px(baselineSize),
        FontWeight = weight switch
        {
            FontWeight.SemiBold => Microsoft.UI.Text.FontWeights.SemiBold,
            _ => Microsoft.UI.Text.FontWeights.Normal,
        },
        HorizontalAlignment = CanvasHorizontalAlignment.Center,
        VerticalAlignment = CanvasVerticalAlignment.Top,
        WordWrapping = CanvasWordWrapping.NoWrap,
    };

    private enum FontWeight
    {
        Normal,
        SemiBold,
    }
}
