namespace AShareMotionStudio.Render;

/// <summary>
/// Everything a renderer needs to draw one frame, with the geometry already
/// worked out.
///
/// The point of this type is that it is computed **once per frame and shared by
/// the preview and the encoder**. Both draw through the same
/// <see cref="IFrameRenderer"/> with the same context; the preview differs only by
/// a transform applied before the renderer is called. So a renderer has no way to
/// behave differently in a preview than in a file, and "what you see is what is
/// exported" is a property of the structure rather than a claim to be re-tested
/// whenever a renderer changes.
///
/// It also keeps the baseline-pixel rule in one place. Renderers read
/// <see cref="Scale"/> and the resolved geometry below; none of them multiplies a
/// margin out for itself, which is what stopped being true in the tools this
/// replaces.
/// </summary>
/// <param name="Format">The size and rate being drawn for.</param>
/// <param name="BaselineMargins">Margins as the user set them, in baseline pixels.</param>
/// <param name="Progress">
/// How far through the animation this frame is, from 0 to 1. Time is expressed as
/// a fraction rather than as a frame index so a renderer cannot become dependent
/// on the frame rate: the same fraction must produce the same picture at 30 and at
/// 60 fps, or an export at one rate is not the video previewed at the other.
/// </param>
public sealed record FrameContext(VideoFormat Format, ChartMargins BaselineMargins, double Progress)
{
    public double Width => Format.Width;

    public double Height => Format.Height;

    public double Scale => Format.Scale;

    /// <summary>The user's margins in the pixels actually being drawn.</summary>
    public ChartMargins Margins => BaselineMargins.Scaled(Scale);

    /// <summary>Where the plotting area starts, and where the Y labels end.</summary>
    public double ChartLeft => Margins.Left;

    public double ChartRight => Width - Margins.Right;

    public double ChartWidth => Math.Max(1, ChartRight - ChartLeft);

    /// <summary>
    /// Where the lowest thing in the frame sits: the data-source credit. This is
    /// what the bottom margin measures to, which is what makes all three margins
    /// mean the same thing.
    ///
    /// Everything in the lower stack is positioned *upwards* from here at fixed
    /// spacing — credit, then the statistic cards or the second panel, then the
    /// chart baseline. So this is the anchor, and the baseline is derived from it
    /// rather than the other way round.
    /// </summary>
    public double CreditLine => Height - Margins.Bottom;

    /// <summary>
    /// The first row the title block may occupy. Not negotiable: above this the
    /// phone's status bar and the player's chrome overlap the frame.
    /// </summary>
    public double TitleTop => Height * SafeArea.Top;

    /// <summary>
    /// How tall one title row is, in baseline pixels.
    ///
    /// Named because hiding the title is a supported choice on the per-stock page,
    /// and what it does is shift everything below up by exactly this much while
    /// the bottom margin holds the lower edge still — so the chart area grows by
    /// this amount and unchecking the box restores the previous layout exactly.
    /// A shift that is not a named constant is one that the two halves of that
    /// behaviour can disagree about.
    /// </summary>
    public const double TitleRowHeight = 90;

    /// <summary>
    /// The line bars stand on, given how much room this indicator reserves between
    /// its baseline and the credit.
    ///
    /// A method rather than a property, and deliberately: the gap is not a property
    /// of the margins. The whole-market chart puts date labels and four statistic
    /// cards in that band; the per-stock chart puts a second panel there. Offering
    /// a bare <c>Baseline</c> would mean picking one of those as the default and
    /// having the other renderer quietly disagree with it — the drift that
    /// `one-render-path.mdc` exists to prevent.
    /// </summary>
    /// <param name="creditGapBaselinePixels">
    /// Distance from the chart baseline down to the credit, in baseline pixels.
    /// </param>
    public double BaselineAbove(double creditGapBaselinePixels) =>
        CreditLine - Px(creditGapBaselinePixels);

    /// <summary>
    /// The first row below the title that other content may use.
    ///
    /// Hiding the title frees the row it occupied, so everything under it shifts
    /// *up into that row* — it does not move above <see cref="TitleTop"/>, which is
    /// the platform's occlusion line and is not negotiable either way. Expressing
    /// it as "the title row is present or absent" rather than as an offset applied
    /// to the content is what makes unchecking the box restore the previous layout
    /// exactly instead of approximately.
    /// </summary>
    public double ContentTop(bool titleShown) =>
        TitleTop + (titleShown ? Px(TitleRowHeight) : 0);

    /// <summary>
    /// Where the plotting area begins: below the title row if there is one, and
    /// below whatever header rows the indicator draws under it.
    /// </summary>
    /// <param name="headerBaselinePixels">
    /// Rows the indicator puts between the title block and the plot — its subtitle,
    /// and a date line if it has one.
    /// </param>
    public double PlotTop(bool titleShown, double headerBaselinePixels) =>
        ContentTop(titleShown) + Px(headerBaselinePixels);

    /// <summary>
    /// The height available for plotting. Clamped, because a bottom margin dragged
    /// to its maximum on a short frame can otherwise cross the title block and give
    /// a negative height that draws as an inverted chart rather than as nothing.
    /// </summary>
    public double PlotHeight(bool titleShown, double headerBaselinePixels, double creditGapBaselinePixels) =>
        Math.Max(1, BaselineAbove(creditGapBaselinePixels) - PlotTop(titleShown, headerBaselinePixels));

    /// <summary>A baseline measurement in the pixels being drawn.</summary>
    public double Px(double baselinePixels) => baselinePixels * Scale;
}
