using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The colours the frames are drawn in, and the value-to-colour ramps.
///
/// Fixed, and not derived from the app's theme or from the Windows accent colour. A video
/// is a file that will be watched somewhere else; if its palette followed the machine that
/// made it, two people exporting the same data would get different videos and neither
/// preview would predict the result.
///
/// **These are the source tool's own values, not approximations of them.** An earlier pass
/// here carried plausible-looking colours inferred from a prose description, and got one
/// thing materially wrong: the volume ramp's stops are not evenly spaced. Cyan sits at 0.45
/// and orange at 0.75, so the blue-to-cyan half covers the quiet days and the warm end is
/// compressed into the top quarter — which is what makes an unusually heavy day stand out
/// instead of merely being redder than its neighbours. Evenly spaced stops flatten exactly
/// the distinction the colour is there to draw.
/// </summary>
public static class Palette
{
    /// <summary>
    /// The frame's backdrop, as a vertical gradient rather than a flat fill: slightly
    /// lifted at the top where the title sits, darkest at the bottom.
    /// </summary>
    public static readonly (float Position, Color Colour)[] Background =
    [
        (0f, Rgb(0x0C, 0x14, 0x28)),
        (0.55f, Rgb(0x09, 0x0E, 0x1D)),
        (1f, Rgb(0x06, 0x09, 0x11)),
    ];

    /// <summary>The title.</summary>
    public static readonly Color Title = Rgb(0xF0, 0xF5, 0xFF);

    /// <summary>Supporting text: the subtitle lines, card labels, the unit.</summary>
    public static readonly Color Muted = Rgb(0x7E, 0x94, 0xB8);

    /// <summary>Y-axis numbers.</summary>
    public static readonly Color AxisLabel = Rgb(0x65, 0x79, 0x9C);

    /// <summary>Date labels under the bars.</summary>
    public static readonly Color DateLabel = Rgb(0x63, 0x79, 0x9D);

    /// <summary>The count of trading days — the one number in the subtitle that is read.</summary>
    public static readonly Color Emphasis = Rgb(0xFF, 0x6B, 0x6B);

    /// <summary>The date advancing through the animation, and the high-water mark.</summary>
    public static readonly Color Moving = Rgb(0xFB, 0xBF, 0x24);

    /// <summary>The low-water mark, deliberately cool against the warm high.</summary>
    public static readonly Color MarkLow = Rgb(0x60, 0xA5, 0xFA);

    /// <summary>Gridlines.</summary>
    public static readonly Color Grid = Argb(0x21, 0x78, 0x96, 0xC8);

    /// <summary>The mean's dashed line, and the label on it.</summary>
    public static readonly Color AverageLine = Argb(0x8C, 0xE6, 0xF0, 0xFF);

    public static readonly Color AverageLabel = Rgb(0xDB, 0xE7, 0xFF);

    /// <summary>The statistic cards at the end.</summary>
    public static readonly Color CardFill = Argb(0xE6, 0x12, 0x1C, 0x32);

    public static readonly Color CardStroke = Argb(0x42, 0x78, 0x96, 0xD2);

    public static readonly Color CardValue = Rgb(0xEA, 0xF1, 0xFF);

    /// <summary>
    /// The data-source credit, and the calendar's weekday header row — the same tone, because both
    /// are labels the eye should skip over on its way to the data.
    /// </summary>
    public static readonly Color Credit = Rgb(0x5B, 0x6F, 0x92);

    /// <summary>A calendar block's month name. Brighter than the weekday heads under it.</summary>
    public static readonly Color MonthLabel = Rgb(0x93, 0xA9, 0xCC);

    /// <summary>The progress bar's unfilled track.</summary>
    public static readonly Color ProgressTrack = Argb(0x24, 0x78, 0x96, 0xD2);

    /// <summary>The progress bar's fill, left to right.</summary>
    public static readonly (float Position, Color Colour)[] ProgressFill =
    [
        (0f, Rgb(0x25, 0x63, 0xEB)),
        (0.6f, Rgb(0x06, 0xB6, 0xD4)),
        (1f, Rgb(0xF5, 0x9E, 0x0B)),
    ];

    /// <summary>
    /// Turnover and volume: blue through cyan and orange to red, with the warm end
    /// compressed into the top quarter. See the note on this class.
    /// </summary>
    private static readonly (double At, Color Colour)[] VolumeRamp =
    [
        (0.00, Rgb(0x25, 0x63, 0xEB)),
        (0.45, Rgb(0x06, 0xB6, 0xD4)),
        (0.75, Rgb(0xF5, 0x9E, 0x0B)),
        (1.00, Rgb(0xEF, 0x44, 0x44)),
    ];

    /// <summary>
    /// Turnover rate: indigo through purple to pink, for the per-stock page's lower panel.
    ///
    /// Lifted from `stock_dual_studio.html` — `torColor = ramp([[0,[99,102,241]],[0.5,[168,85,247]],
    /// [1,[236,72,153]]])` — with the midpoint at 0.5, unlike the volume ramp's compressed warm end.
    /// </summary>
    private static readonly (double At, Color Colour)[] RateRamp =
    [
        (0.0, Rgb(0x63, 0x66, 0xF1)),
        (0.5, Rgb(0xA8, 0x55, 0xF7)),
        (1.0, Rgb(0xEC, 0x48, 0x99)),
    ];

    /// <summary>
    /// A daily change's colour: red for a rise, green for a fall, deeper with the size of the move.
    ///
    /// Red-up and green-down is the Chinese market convention and the opposite of the Western one.
    /// It is not configurable, because the videos this makes are for an audience that reads it one
    /// way and a switch would only create the chance of publishing it the other.
    ///
    /// **The depth goes as the square root of the magnitude, not linearly.** Most days are small
    /// moves against a period's largest one, so a linear ramp leaves the great majority of cells at
    /// nearly the same near-black and the picture says only "there was one big day". The square root
    /// lifts the small moves into visible territory while keeping the extremes distinct — the point
    /// of the chart is which days were up and which down, and a cell nobody can read answers
    /// neither.
    /// </summary>
    /// <param name="change">The day's change in per cent; the sign chooses the hue.</param>
    /// <param name="absMax">
    /// The largest move either way in the period, which the depth is measured against. Zero or less
    /// is treated as one, so a period with no movement draws at its base tone rather than dividing
    /// by nothing.
    /// </param>
    public static Color Return(double change, double absMax)
    {
        var depth = Math.Sqrt(Math.Clamp(Math.Abs(change) / (absMax <= 0 ? 1 : absMax), 0, 1));

        var (from, to) = change >= 0
            ? (Rgb(0x56, 0x2A, 0x30), Rgb(0xEF, 0x44, 0x44))
            : (Rgb(0x1A, 0x42, 0x36), Rgb(0x22, 0xC5, 0x5E));

        return Lerp(from, to, depth);
    }

    /// <summary>
    /// A turnover's colour, given its position in the series from 0 to 1.</summary>
    public static Color Volume(double position) => Sample(VolumeRamp, position);

    /// <summary>A turnover rate's colour, given its position in the series.</summary>
    public static Color Rate(double position) => Sample(RateRamp, position);

    // ---- The per-stock page's own entries, all lifted from stock_dual_studio.html. ----
    // That tool has its own background, its own text tones and its own progress fill; they
    // differ from the whole-market ones by a few units in some places and by a whole hue in
    // others, and each app's look is the one its own audience tuned.

    /// <summary>The per-stock frame's backdrop: the same shape, cooler and a touch lighter.</summary>
    public static readonly (float Position, Color Colour)[] StockBackground =
    [
        (0f, Rgb(0x0D, 0x14, 0x30)),
        (0.5f, Rgb(0x09, 0x0E, 0x1D)),
        (1f, Rgb(0x07, 0x09, 0x14)),
    ];

    /// <summary>The per-stock header's dim runs: the code, the dates, the unit words.</summary>
    public static readonly Color StockMuted = Rgb(0x82, 0x96, 0xB8);

    /// <summary>A panel's title, and its unit, and its axis and date labels — one tone ladder.</summary>
    public static readonly Color StockPanelTitle = Rgb(0x93, 0xA9, 0xCC);

    public static readonly Color StockUnit = Rgb(0x5F, 0x73, 0x9A);

    public static readonly Color StockAxisLabel = Rgb(0x62, 0x77, 0x9B);

    public static readonly Color StockDateLabel = Rgb(0x5D, 0x71, 0x99);

    /// <summary>The line joining the turnover-rate bars' tops, and the rate panel's closing dashes.</summary>
    public static readonly Color StockRateLine = Argb(0xBF, 0xF4, 0xBE, 0xFF);

    public static readonly Color StockFinalRateLine = Argb(0x99, 0xEC, 0x48, 0x99);

    public static readonly Color StockFinalRateLabel = Rgb(0xFB, 0xCF, 0xE8);

    /// <summary>The per-stock progress bar's fill, left to right.</summary>
    public static readonly (float Position, Color Colour)[] StockProgressFill =
    [
        (0f, Rgb(0x63, 0x66, 0xF1)),
        (0.6f, Rgb(0xA8, 0x55, 0xF7)),
        (1f, Rgb(0xEC, 0x48, 0x99)),
    ];

    /// <summary>The sector race's progress bar: amber into red, its own accent pair.</summary>
    public static readonly (float Position, Color Colour)[] RaceProgressFill =
    [
        (0f, Rgb(0xF5, 0x9E, 0x0B)),
        (1f, Rgb(0xEF, 0x44, 0x44)),
    ];

    /// <summary>
    /// Reads a ramp at a position, interpolating between the two stops it falls between.
    ///
    /// The position is clamped rather than wrapped. A value slightly above 1 through
    /// floating-point error should be the top colour, not the bottom one — wrapping would
    /// put a single blue bar among the reds and look like data corruption.
    /// </summary>
    private static Color Sample((double At, Color Colour)[] ramp, double position)
    {
        var t = Math.Clamp(position, 0, 1);

        for (var i = 1; i < ramp.Length; i++)
        {
            if (t <= ramp[i].At)
            {
                var (from, lower) = ramp[i - 1];
                var (to, upper) = ramp[i];
                var span = to - from;

                return Lerp(lower, upper, span <= 0 ? 0 : (t - from) / span);
            }
        }

        return ramp[^1].Colour;
    }

    private static Color Lerp(Color from, Color to, double t) => Color.FromArgb(
        0xFF,
        (byte)Math.Round(from.R + ((to.R - from.R) * t)),
        (byte)Math.Round(from.G + ((to.G - from.G) * t)),
        (byte)Math.Round(from.B + ((to.B - from.B) * t)));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);

    private static Color Argb(byte a, byte r, byte g, byte b) => Color.FromArgb(a, r, g, b);
}
