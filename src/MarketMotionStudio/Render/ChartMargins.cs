namespace MarketMotionStudio.Render;

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
/// title block. It opens on <see cref="SafeArea.Top"/>, the band a phone covers with
/// its own status bar, and can be drawn in from there or pushed up through it. Going
/// up is allowed and is not the default: a frame exported for a player that shows no
/// chrome over the picture has that room to spend, and the preview draws the band so
/// the crossing is visible rather than a surprise in the file.</description></item>
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
    public static ChartMargins Default { get; } = new(150, 150, 250, TopDefault);

    /// <summary>
    /// What the top margin opens on: <see cref="SafeArea.Top"/> multiplied out for
    /// the 1080×1920 baseline. The floor and the default are no longer the same
    /// number — the default is where the title is safe on a phone, the floor is
    /// where the slider stops.
    /// </summary>
    public const double TopDefault = 230;

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
    /// The top margin's range. The floor matches the side margins' — a title set forty
    /// baseline pixels from the top edge is a decision someone may make, and the preview
    /// draws the safe-area band so that crossing into it is visible. The ceiling is where the
    /// plot starts being eaten rather than repositioned — the same reasoning as the
    /// bottom's, from the other end.
    /// </summary>
    public const double TopSmallest = 40;

    public const double TopLargest = 450;

    /// <summary>
    /// These measurements multiplied out for a real frame size. The caller draws
    /// in device pixels and never sees the baseline again.
    /// </summary>
    public ChartMargins Scaled(double scale) =>
        new(Left * scale, Right * scale, Bottom * scale, Top * scale);
}
