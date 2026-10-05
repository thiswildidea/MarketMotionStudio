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
/// <param name="Backdrop">
/// What this frame is drawn on, already resolved.
///
/// Carried here rather than read by the renderer that fills the frame, so that a
/// backdrop chosen after an export has started cannot change the frames part-way
/// through the file: the encoder builds one of these for the whole run.
/// </param>
/// <param name="Watermark">
/// The name carried across the backdrop of this frame, or null when it is off.
///
/// Here for the reason the <see cref="Backdrop"/> is: it is drawn as part of the
/// backdrop, by <see cref="Backdrop.Fill"/>, and a mark turned on or off after
/// an export has started must not appear in half of the file.
/// </param>
public sealed record FrameContext(
    VideoFormat Format, ChartMargins BaselineMargins, double Progress, Backdrop Backdrop,
    Watermark? Watermark)
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
    /// The first row the title block may occupy: the top margin, and nothing else.
    ///
    /// It used to be clamped to <see cref="SafeArea.Top"/>, which made the setting
    /// one-directional — a margin below the band did nothing at all, so the lower half of
    /// the slider's range was inert and the number it showed was not the number in force.
    /// Measuring it straight from the margin instead lets the setting mean what it says:
    /// at <see cref="ChartMargins.TopDefault"/> the title sits exactly where the safe area
    /// puts it, and above that value it is inside the band a phone covers.
    /// </summary>
    public double TitleTop => Margins.Top;

    /// <summary>
    /// How far the top margin moves the top stack from where the safe area alone would put
    /// it, in device pixels — negative when the margin is drawn in above the band.
    ///
    /// Every row anchored to the top of the frame — the header block's rows and the plot's
    /// first row — shifts by this same amount, so the spacing inside the stack never
    /// changes and the plot is what absorbs the difference.
    /// </summary>
    public double TopShift => Margins.Top - Height * SafeArea.Top;

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
    /// A header row as above, that also gives way to the title block — the header-block
    /// convention shared by every indicator page.
    ///
    /// <paramref name="titleLines"/> is how many lines the title actually took on this frame, and
    /// the three cases are the whole of the behaviour:
    ///
    /// <list type="bullet">
    /// <item><description><b>Zero</b> — the title is hidden. Everything below moves *up into* its
    /// row, by exactly <see cref="TitleRowHeight"/>.</description></item>
    /// <item><description><b>One</b> — an ordinary title. Nothing moves, which is what keeps the
    /// layout that every page was tuned against unchanged for a title that fits on one
    /// line.</description></item>
    /// <item><description><b>Two or more</b> — a wrapped title. Everything below moves down by the
    /// lines it took beyond the first, one <see cref="TitleLineHeight"/> each. Stated as
    /// "the rows the title occupies" rather than as an offset the title adds, because the rows
    /// below have to agree with the block that was drawn and not the other way round.</description></item>
    /// </list>
    ///
    /// Either way the *first* line of the title stays where it always was — see
    /// <see cref="TitleBaseline"/> — so the block grows downwards and never into the band the
    /// phone covers.
    /// </summary>
    public double HeaderRow(double fraction, int titleLines) => TopRow(fraction) + TitleShift(titleLines);

    /// <summary>
    /// How far a row below the title block moves, given how many lines the title took. Zero
    /// when the title is shown on one line, negative when it is hidden — the one place those
    /// three cases are turned into a number.
    /// </summary>
    public double TitleShift(int titleLines) => titleLines <= 0
        ? -Px(TitleRowHeight)
        : Px((titleLines - 1) * TitleLineHeight);

    /// <summary>
    /// Where line <paramref name="line"/> of the title block sits, counted from zero — the
    /// alphabetic baseline, the way <see cref="Ink"/> wants it.
    ///
    /// Line zero is the row the title has always been drawn on, whatever the line count: a title
    /// that wraps keeps its first line exactly where a one-line title's only line is, and grows
    /// downwards into the room <see cref="HeaderRow"/> hands it. Growing upwards instead would
    /// move the headline into the strip the phone covers with its own interface, which is the one
    /// thing the top margin exists to prevent.
    /// </summary>
    public double TitleBaseline(int line) => TopRow(TitleRowFraction) + Px(line * TitleLineHeight);

    /// <summary>
    /// The row the title block starts on, as a fraction of frame height — the source's own
    /// figure, in one place so that the page whose renderer draws the title and the pages that
    /// borrow its plot rows cannot disagree about where the header ends.
    /// </summary>
    public const double TitleRowFraction = 0.155;

    /// <summary>
    /// The pitch between two lines of a wrapped title, in baseline pixels.
    ///
    /// Deliberately the same 0.035 of the frame the header's own rows are spaced by
    /// (0.155 → 0.19 → 0.225): a second title line then lands on the row the subtitle would
    /// have had, so wrapping one line costs exactly one header row and nothing about the
    /// spacing inside the block has to be re-tuned. The fraction is multiplied out here rather
    /// than written as 67.2 because the two numbers being the same is the point.
    /// </summary>
    public const double TitleLineHeight = HeaderRowPitch * VideoFormat.BaselineHeight;

    /// <summary>The frame-height fraction the header's rows are spaced by.</summary>
    public const double HeaderRowPitch = 0.035;

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
    ///
    /// A wrapped title takes more than one row, and this is the difference between
    /// <see cref="TitleRowHeight"/> and the two: the block is the row plus however many extra
    /// lines were drawn at <see cref="TitleLineHeight"/> each, so a caller stacking content
    /// under the title does not have to know which of the two it is looking at.
    /// </summary>
    public double ContentTop(int titleLines) =>
        TitleTop + (titleLines <= 0
            ? 0
            : Px(TitleRowHeight + ((titleLines - 1) * TitleLineHeight)));

    /// <summary>
    /// Where the plotting area begins: below the title row if there is one, and
    /// below whatever header rows the indicator draws under it.
    /// </summary>
    /// <param name="headerBaselinePixels">
    /// Rows the indicator puts between the title block and the plot — its subtitle,
    /// and a date line if it has one.
    /// </param>
    public double PlotTop(int titleLines, double headerBaselinePixels) =>
        ContentTop(titleLines) + Px(headerBaselinePixels);

    /// <summary>
    /// The height available for plotting. Clamped, because a bottom margin dragged
    /// to its maximum on a short frame can otherwise cross the title block and give
    /// a negative height that draws as an inverted chart rather than as nothing.
    /// </summary>
    public double PlotHeight(int titleLines, double headerBaselinePixels, double creditGapBaselinePixels) =>
        Math.Max(1, BaselineAbove(creditGapBaselinePixels) - PlotTop(titleLines, headerBaselinePixels));

    /// <summary>A baseline measurement in the pixels being drawn.</summary>
    public double Px(double baselinePixels) => baselinePixels * Scale;
}
