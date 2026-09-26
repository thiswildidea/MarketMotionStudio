namespace MarketMotionStudio.Render;

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
    /// The first row the title block may occupy.
    ///
    /// The floor is <see cref="SafeArea.Top"/> — above it the phone's status bar and the
    /// player's chrome overlap the frame, and no margin setting may cross that. The user's
    /// top margin can only push the title further **down** from there, which is what keeps
    /// the margin meaningful without being able to do damage: at the smallest value the
    /// layout is exactly what it was before the top margin existed.
    /// </summary>
    public double TitleTop => Height * SafeArea.Top + TopShift;

    /// <summary>
    /// How far the top margin pushes the top stack down from where the safe area alone
    /// would put it, in device pixels.
    ///
    /// Zero unless the margin is set past the safe-area floor. Every row anchored to the
    /// top of the frame — the header block's rows and the plot's first row — shifts by
    /// this same amount, so the spacing inside the stack never changes and the plot is
    /// what absorbs the difference.
    /// </summary>
    public double TopShift => Math.Max(0, Margins.Top - Height * SafeArea.Top);

    /// <summary>
    /// A row anchored to the top of the frame, stated as a fraction of frame height as the
    /// source HTML stated it, moved down by whatever the top margin added.
    ///
    /// Renderers use this instead of multiplying the fraction themselves so a top margin
    /// cannot move the header and leave the plot where it was — the drift between two
    /// ways of computing the same anchor is what <c>one-render-path.mdc</c> is about.
    /// </summary>
    public double TopRow(double fraction) => Height * fraction + TopShift;

    /// <summary>
    /// A header row as above, that also gives way when the title is hidden — the header-block
    /// convention shared by both indicator pages.
    ///
    /// Hiding the title frees its row and everything below moves *up into* it, by exactly
    /// <see cref="TitleRowHeight"/>, so the spacing between the rows that remain never changes.
    /// </summary>
    public double HeaderRow(double fraction, bool titleShown) =>
        TopRow(fraction) - (titleShown ? 0 : Px(TitleRowHeight));

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
