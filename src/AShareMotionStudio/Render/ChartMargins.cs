namespace AShareMotionStudio.Render;

/// <summary>
/// How much of the frame the chart leaves empty on its four sides, in baseline
/// pixels against 1080×1920.
///
/// **All four mean the same thing: how far the nearest content is from that
/// edge.** That uniformity was not true at first and is the point of the current
/// design. The bottom margin used to measure to the chart's *baseline*, with the
/// date labels, statistic cards and credit hanging below it and off the bottom of
/// the frame — so "250" meant something different on the bottom than on the left,
/// and the two indicator pages needed different values to look the same. Measuring
/// to the bottom-most content instead makes one number work for both, and makes
/// the stack above it move as a unit at fixed spacing.
///
/// <list type="bullet">
/// <item><description><b>Left</b> also decides where the Y-axis labels land. The
/// labels are drawn leftwards from the start of the gridline, so too small a
/// value does not crop the chart — it pushes the numbers off the edge of the
/// frame.</description></item>
/// <item><description><b>Bottom</b> is the distance from the *lowest thing drawn*
/// — the data-source credit — to the bottom of the frame. The credit, the
/// statistic cards and the chart baseline above it are spaced by fixed amounts, so
/// this moves the whole lower stack together without changing the gaps inside
/// it.</description></item>
/// <item><description><b>Right</b> is symmetry with the left in the ordinary
/// case, and headroom for the last bar's value label.</description></item>
/// <item><description><b>Top</b> is the distance from the top of the frame to the
/// title block. It has a floor the other three do not: <see cref="SafeArea.Top"/>,
/// the band a phone covers with its own status bar, which the render honours
/// whether the margin likes it or not. So the useful range starts at that floor
/// rather than at zero — the one direction a top margin cannot go is up.</description></item>
/// </list>
/// </summary>
public sealed record ChartMargins(double Left, double Right, double Bottom, double Top)
{
    /// <summary>
    /// What both indicators start from.
    ///
    /// One value rather than one per page. The two started out different — the
    /// whole-market chart left room under its baseline for four statistic cards
    /// and the per-stock one for a second panel — but that difference existed only
    /// because the bottom margin measured to the baseline. Now that all four
    /// margins measure content-to-edge, the same numbers suit both, and a
    /// per-page override would be a mechanism implying a difference that is no
    /// longer there.
    /// </summary>
    public static ChartMargins Default { get; } = new(150, 150, 250, TopSmallest);

    /// <summary>
    /// The side-margin range. The floor is not zero: a left margin of zero puts the axis
    /// labels outside the frame, which looks like a rendering fault rather than a setting.
    /// </summary>
    public const double SideSmallest = 40;

    public const double SideLargest = 260;

    /// <summary>
    /// The bottom margin's range, which is narrower at both ends and for a different reason.
    /// It has to keep a whole stack inside the frame — date labels, four statistic cards, the
    /// credit — so its useful floor is well above zero, and pushing it higher than this
    /// starts eating the plot rather than repositioning it.
    /// </summary>
    public const double BottomSmallest = 150;

    public const double BottomLargest = 420;

    /// <summary>
    /// The top margin's range. The floor *is* <see cref="SafeArea.Top"/> expressed in
    /// baseline pixels (0.12 of 1920): below it the title would slide under a phone's
    /// status bar, which is the one thing a margin must never do. The ceiling is where
    /// the plot starts being eaten rather than repositioned — the same reasoning as the
    /// bottom's, from the other end.
    /// </summary>
    public const double TopSmallest = 230;

    public const double TopLargest = 450;

    /// <summary>
    /// These measurements multiplied out for a real frame size. The caller draws
    /// in device pixels and never sees the baseline again.
    /// </summary>
    public ChartMargins Scaled(double scale) =>
        new(Left * scale, Right * scale, Bottom * scale, Top * scale);
}
